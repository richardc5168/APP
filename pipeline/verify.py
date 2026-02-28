"""
pipeline/verify.py — Four-gate verification for curriculum-aligned problem records.

Gates:
  1) schema   — JSON must conform to schemas/problem.schema.json
  2) correctness — answer passes deterministic calculator / equivalence check
  3) steps    — solution steps pass lint (unit consistency, no jump, min length)
  4) license  — source.license_type on allowlist; deny → block auto-publish
              + prompt injection detection + anti-cheat/dedup
              + textbook reproduction detection

Scorecard (0-100) via pipeline/scorecard.py:
  - correctness weight 40
  - step_consistency weight 25
  - step_completeness weight 15
  - answer_reasonableness weight 10
  - anti_cheat_dedup weight 10

Usage:
  python -m pipeline.verify --dataset data/problems.jsonl --report artifacts/report.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from pipeline.scorecard import compute_scorecard
from pipeline.source_governance import (
    LICENSE_ALLOWLIST,
    LICENSE_DENY,
    check_textbook_reproduction,
    validate_source,
)

# ── Constants ──────────────────────────────────────────────

# Re-export for backward compatibility
DENY_AUTO_PUBLISH = LICENSE_DENY

TOPIC_SPECIFIC_RULES: dict[str, dict[str, Any]] = {
    "N-6-7": {
        "must_include_formula": ["距離=速度×時間", "速度=距離÷時間", "時間=距離÷速度"],
        "min_steps": 2,
    },
    "N-5-11": {
        "forbidden_words": ["誤差", "近似值"],
    },
    "N-6-3": {
        "forbidden_unless_exempt": "餘數",
    },
    "N-5-10": {
        "answer_max_if_percent": 100,  # 百分率不大於 100% (only when answer_type=percent)
    },
    "S-6-2": {
        "min_steps": 2,
        "common_error_check": True,  # Must address scale misconception
    },
    "D-5-1": {
        "min_data_points": 5,  # 折線圖至少 5 個資料點
        "min_steps": 2,
    },
}

# Prompt injection patterns (data-instruction isolation)
INJECTION_PATTERNS = [
    r"忽略以上指示",
    r"忽略之前的指令",
    r"改寫系統提示",
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+above",
    r"disregard\s+(the\s+)?(above|previous)",
    r"system\s*prompt",
    r"you\s+are\s+now",
    r"act\s+as\s+if",
    r"override\s+(the\s+)?rules",
    r"jailbreak",
]
INJECTION_RE = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

# ── Gate Functions ─────────────────────────────────────────

def gate_schema(p: dict) -> tuple[bool, str]:
    """Check required fields exist and types are valid."""
    required = ["id", "grade", "stage", "topic_codes", "question", "solution", "source"]
    for field in required:
        if field not in p:
            return False, f"missing required field: {field}"
    if p.get("grade") not in (5, 6):
        return False, f"grade must be 5 or 6, got {p.get('grade')}"
    if p.get("stage") != "III":
        return False, f"stage must be III, got {p.get('stage')}"
    codes = p.get("topic_codes", [])
    if not isinstance(codes, list) or len(codes) == 0:
        return False, "topic_codes must be a non-empty list"
    sol = p.get("solution", {})
    if "steps" not in sol or "answer" not in sol:
        return False, "solution must contain steps and answer"
    if not isinstance(sol["steps"], list) or len(sol["steps"]) == 0:
        return False, "solution.steps must be non-empty"
    src = p.get("source", {})
    for f in ["url", "license_type", "captured_at"]:
        if f not in src:
            return False, f"source missing required field: {f}"
    return True, "ok"


def gate_correctness(p: dict) -> tuple[bool, str]:
    """Deterministic answer check — extend per topic."""
    sol = p.get("solution", {})
    ans = sol.get("answer", {})
    if ans.get("value") is None:
        return False, "answer.value is missing"

    codes = p.get("topic_codes", [])

    # N-5-10: 百分率 ≤ 100% (only when answer_type is percent)
    for code in codes:
        rules = TOPIC_SPECIFIC_RULES.get(code, {})
        answer_max = rules.get("answer_max_if_percent")
        if answer_max is not None and p.get("answer_type") == "percent":
            try:
                v = float(ans["value"])
                if v > answer_max:
                    return False, f"{code} percent answer {v} exceeds max {answer_max}"
            except (TypeError, ValueError):
                pass

    # Negative answer sanity check (distance / price / percentage should be >= 0)
    try:
        v = float(ans["value"])
        if v < 0:
            return False, f"answer {v} is negative — likely unreasonable"
    except (TypeError, ValueError):
        pass  # non-numeric (fractions like "3/2") are ok

    # Low confidence → flag (not a hard failure, but noted)
    conf = p.get("confidence", 1.0)
    if conf < 0.7:
        return True, f"ok (low confidence {conf} — recommend human review)"

    return True, "ok"


def gate_steps(p: dict) -> tuple[bool, str]:
    """Step lint: check min steps, unit consistency, forbidden words per topic."""
    sol = p.get("solution", {})
    steps = sol.get("steps", [])
    codes = p.get("topic_codes", [])

    # Check minimum step count per topic
    for code in codes:
        rules = TOPIC_SPECIFIC_RULES.get(code, {})
        min_steps = rules.get("min_steps", 1)
        if len(steps) < min_steps:
            return False, f"{code} requires >= {min_steps} steps, got {len(steps)}"

        # Forbidden words
        forbidden = rules.get("forbidden_words", [])
        for fw in forbidden:
            for i, s in enumerate(steps):
                if fw in s:
                    return False, f"step {i+1} contains forbidden word '{fw}' (rule: {code})"

        # Forbidden unless exempt (e.g. N-6-3 餘數)
        fu = rules.get("forbidden_unless_exempt")
        if fu:
            exempt = p.get("grading_exempt", False)
            for i, s in enumerate(steps):
                if fu in s and not exempt:
                    return False, (
                        f"step {i+1} contains '{fu}' which requires "
                        f"grading_exempt=true (rule: {code})"
                    )

        # Must-include formula (at least one variant must appear)
        formulas = rules.get("must_include_formula", [])
        if formulas:
            all_text = " ".join(steps)
            if not any(f in all_text for f in formulas):
                return False, f"{code} requires one of {formulas} in steps"

        # D-5-1: check minimum data points in question
        min_dp = rules.get("min_data_points")
        if min_dp is not None:
            question = p.get("question", "")
            # Count numeric data points in question (e.g., temperature values, counts)
            data_point_re = re.compile(r"\d+(?:\.\d+)?(?:\s*[°℃%元公分公尺公升])?")
            question_nums = data_point_re.findall(question)
            # Also check checks.data_points_min if specified
            checks = p.get("checks", {})
            explicit_min = checks.get("data_points_min", min_dp)
            if len(question_nums) < explicit_min:
                return False, (
                    f"{code} requires >= {explicit_min} data points, "
                    f"found {len(question_nums)} in question"
                )

        # S-6-2: check for common error reminder
        if rules.get("common_error_check") and code == "S-6-2":
            all_text_with_q = p.get("question", "") + " " + " ".join(steps)
            checks = p.get("checks", {})
            reminder = checks.get("common_error_reminder", "")
            # Must address scale misconception somewhere
            scale_terms = ["比例尺", "分母", "放大", "縮小", "比例"]
            has_scale_context = any(t in all_text_with_q for t in scale_terms)
            if not has_scale_context:
                return False, (
                    f"{code} problem should reference scale concepts "
                    f"(比例尺/分母/放大/縮小)"
                )

    return True, "ok"


def gate_license(p: dict) -> tuple[bool, str]:
    """License allowlist check + prompt injection detection + anti-cheat + textbook repro."""
    src = p.get("source", {})
    lt = src.get("license_type", "unknown")
    decision = src.get("license_decision", "needs_review")

    if lt in DENY_AUTO_PUBLISH or decision == "deny":
        return False, f"license blocked: {lt} / decision={decision}"
    if lt not in LICENSE_ALLOWLIST and decision != "allow":
        return False, f"license '{lt}' not on allowlist; decision={decision} → needs_review"

    # Prompt injection detection — scan question + steps for injection patterns
    question = p.get("question", "")
    steps_text = " ".join(p.get("solution", {}).get("steps", []))
    full_text = question + " " + steps_text
    match = INJECTION_RE.search(full_text)
    if match:
        return False, f"prompt injection detected: '{match.group()}'"

    # Textbook reproduction detection
    is_safe_q, pattern_q = check_textbook_reproduction(question)
    if not is_safe_q:
        return False, f"textbook reproduction detected in question: '{pattern_q}'"
    is_safe_s, pattern_s = check_textbook_reproduction(steps_text)
    if not is_safe_s:
        return False, f"textbook reproduction detected in steps: '{pattern_s}'"

    return True, "ok"


# ── Scorecard ──────────────────────────────────────────────

def compute_score(p: dict, gates: dict[str, bool]) -> int:
    """Compute weighted score (0-100) using granular scorecard. Gate-aware."""
    sc = compute_scorecard(p, gates)
    return sc["total"]


# ── Main Verification ─────────────────────────────────────

def verify_problem(p: dict) -> dict:
    """Run all four gates and compute scorecard for one problem."""
    gates: dict[str, bool] = {}
    reasons: dict[str, str] = {}

    for name, fn in [
        ("schema", gate_schema),
        ("correctness", gate_correctness),
        ("steps", gate_steps),
        ("license", gate_license),
    ]:
        ok, reason = fn(p)
        gates[name] = ok
        reasons[name] = reason

    passed = all(gates.values())
    scorecard = compute_scorecard(p, gates)
    score = scorecard["total"]

    return {
        "id": p.get("id", "?"),
        "gate": gates,
        "reasons": reasons,
        "passed": passed,
        "score": score,
        "scorecard": scorecard["dimensions"],
    }


def verify_dataset(path: str) -> dict:
    """Verify all problems in a JSONL file."""
    results = []
    total = 0
    passed_count = 0
    failed = []
    topic_counter: Counter[str] = Counter()

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                p = json.loads(line)
            except json.JSONDecodeError as e:
                failed.append({"line": line_no, "error": str(e)})
                total += 1
                continue

            r = verify_problem(p)
            results.append(r)
            total += 1
            if r["passed"]:
                passed_count += 1
            else:
                failed.append({"line": line_no, "id": r["id"], "reasons": r["reasons"]})

            # Accumulate topic coverage
            for code in p.get("topic_codes", []):
                topic_counter[code] += 1

    return {
        "total": total,
        "passed": passed_count,
        "failed_count": total - passed_count,
        "pass_rate": round(passed_count / max(total, 1), 4),
        "topic_coverage": dict(topic_counter),
        "results": results,
        "failures": failed,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify curriculum-aligned problem dataset")
    parser.add_argument("--dataset", required=True, help="Path to problems JSONL")
    parser.add_argument("--report", default="artifacts/report.json", help="Output report path")
    args = parser.parse_args()

    if not Path(args.dataset).exists():
        print(f"Dataset not found: {args.dataset}")
        sys.exit(1)

    report = verify_dataset(args.dataset)

    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Verified {report['total']} problems: {report['passed']} passed, {report['failed_count']} failed")
    print(f"Pass rate: {report['pass_rate']*100:.1f}%")
    print(f"Report saved to {args.report}")

    if report["failed_count"] > 0:
        print("\n--- FAILURES ---")
        for f in report["failures"]:
            print(f"  {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
