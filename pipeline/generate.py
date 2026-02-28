"""
pipeline/generate.py — Problem generation with Self-Refine loop.

Generates problem JSON conforming to schemas/problem.schema.json.
Uses a Self-Refine loop: if deterministic verification fails, the model
re-generates with structured feedback up to N iterations, then routes
to human review queue.

Agent Roles (multi-role architecture via system prompts):
  1) Retriever — fetch topic code + source material
  2) Generator — produce problem + steps JSON
  3) Verifier  — deterministic 4-gate check (pipeline.verify)
  4) Refiner   — fix issues based on structured feedback

Usage:
  python -m pipeline.generate --out data/problems.jsonl [--count 20] [--topics N-5-10,N-6-7]

NOTE: LLM integration is a scaffold — implement API calls when keys are configured.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── System Prompt ──────────────────────────────────────────

SYSTEM_PROMPT = """\
你是國小五六年級數學出題與解題代理。請嚴格遵守：
1) 必須輸出 JSON，符合 schema（我會提供）。
2) 題目 topic_codes 必須包含：學習表現 n-III/s-III/r-III/d-III 之一 \
   + 分年內容 N-5-*/N-6-* 或 S-6-*/D-5-*。
3) 解題步驟需可被程式化驗證：每一步只做一個可檢查的運算或等值轉換；包含單位。
4) 先輸出「自動檢核清單」，再輸出題目 JSON。
5) 若你不確定答案，必須在 JSON 內標記 confidence<0.7，讓系統送人工；不得猜。

第三學習階段 topic code 可用集合：
- 學習表現：n-III-1~12, s-III-1~4, r-III-1~3, d-III-1~2
- 分年內容：N-5-*, N-6-*, S-5-*, S-6-*, D-5-*, D-6-*
"""

# ── Six Scenario Prompts (covering Stage III core topics) ──

TOPIC_PROMPTS = {
    "N-5-10": {
        "prompt": (
            "生成 1 題 N-5-10（百分率/折/成）生活情境題。結果必須 <=100%。"
            "輸出需含 n-III-9。"
        ),
        "expected_answer_type": "percent",
        "verification": {
            "answer_max_if_percent": 100,
            "min_steps": 2,
        },
        "example_checks": {
            "answer_type": "integer",
            "unit": "元",
        },
    },
    "N-5-11": {
        "prompt": (
            "生成 1 題 N-5-11（對小數取概數、四捨五入、近似意義）題。"
            "不要使用「誤差」「近似值」字眼。"
        ),
        "expected_answer_type": "decimal",
        "verification": {
            "forbidden_words": ["誤差", "近似值"],
        },
        "example_checks": {
            "answer_type": "decimal",
        },
    },
    "N-6-7": {
        "prompt": (
            "生成 1 題 N-6-7（速度）題，必須包含單位換算（大單位到小單位或反向），"
            "並含「距離=速度×時間」。"
        ),
        "expected_answer_type": "decimal",
        "verification": {
            "must_include_formula": ["距離=速度×時間"],
            "min_steps": 2,
            "unit_consistency": True,
        },
        "example_checks": {
            "answer_type": "integer",
            "unit": "公里",
        },
    },
    "N-6-3": {
        "prompt": (
            "生成 1 題 N-6-3（分數除法：整數÷分數或分數÷分數）題，"
            "避免餘數題或標記為不評量。"
        ),
        "expected_answer_type": "fraction",
        "verification": {
            "forbidden_unless_grading_exempt": "餘數",
        },
        "example_checks": {
            "answer_type": "fraction",
        },
    },
    "S-6-2": {
        "prompt": (
            "生成 1 題 S-6-2（地圖比例尺）題，需包含常見錯誤"
            "「比例分母愈大，相對邊長也愈大」的反例或提醒。"
        ),
        "expected_answer_type": "decimal",
        "verification": {
            "min_steps": 2,
            "common_error_check": True,
        },
        "example_checks": {
            "answer_type": "decimal",
            "unit": "公里",
        },
    },
    "D-5-1": {
        "prompt": (
            "生成 1 題 D-5-1（製作折線圖）題：給一組時間序列資料，"
            "要求畫折線圖並回答一個「趨勢」問題。"
        ),
        "expected_answer_type": "mixed",
        "verification": {
            "min_data_points": 5,
            "min_steps": 2,
        },
        "example_checks": {
            "answer_type": "mixed",
        },
    },
}

ALL_TOPIC_CODES = list(TOPIC_PROMPTS.keys())

MAX_SELF_REFINE_ITERATIONS = 3

# ── Self-Refine Feedback Template ──────────────────────────

REFINE_FEEDBACK_TEMPLATE = """\
你生成的題目未通過自動驗證。以下是失敗原因：

{failure_reasons}

請根據以上失敗原因修正題目，然後重新輸出完整的 JSON。
注意：
- 不要改變題目核心邏輯，只修正驗證失敗的部分。
- 確保所有 topic_codes 仍存在。
- 答案必須正確、步驟必須完整。
- 若你無法確定答案，標記 confidence < 0.7。
"""

# ── Multi-Role Agent Architecture ──────────────────────────

class AgentRole:
    """Base class for agent roles in the generation pipeline."""

    RETRIEVER = "retriever"
    GENERATOR = "generator"
    VERIFIER = "verifier"
    REFINER = "refiner"

    ROLE_PROMPTS = {
        "retriever": (
            "你是檢索代理。根據指定的 topic_code，找出相關的課綱能力敘述與"
            "分年內容，回報可用於命題的關鍵資訊。"
        ),
        "generator": SYSTEM_PROMPT,
        "verifier": (
            "你是驗證代理。使用 pipeline/verify.py 的四道閘門檢查題目正確性。"
            "回報各 gate 的 pass/fail 與理由。"
        ),
        "refiner": (
            "你是修正代理。根據驗證失敗的結構化回饋，修正題目使其通過所有閘門。"
            "修正時不改變題目核心邏輯。"
        ),
    }

    @classmethod
    def get_system_prompt(cls, role: str) -> str:
        return cls.ROLE_PROMPTS.get(role, SYSTEM_PROMPT)


# ── Generation Functions ──────────────────────────────────

def generate_problem_stub(topic_code: str) -> dict | None:
    """
    Stub generator — returns None.
    Replace with actual LLM call + Self-Refine loop.

    Real implementation should:
    1. Send AgentRole.get_system_prompt('retriever') to retrieve topic context
    2. Send AgentRole.get_system_prompt('generator') + TOPIC_PROMPTS[topic_code] to LLM
    3. Parse JSON response
    4. Run pipeline.verify.verify_problem() on it (verifier role)
    5. If fails, send REFINE_FEEDBACK_TEMPLATE with reasons to LLM (refiner role)
    6. Repeat up to MAX_SELF_REFINE_ITERATIONS
    7. If still fails, set confidence < 0.7 and route to human queue
    """
    return None


def build_generation_request(topic_code: str) -> dict:
    """
    Build the full generation request payload for a given topic code.
    Returns a dict with system_prompt, user_prompt, verification_rules,
    and max_iterations that can be sent to an LLM API.
    """
    topic_config = TOPIC_PROMPTS.get(topic_code, {})
    return {
        "system_prompt": AgentRole.get_system_prompt(AgentRole.GENERATOR),
        "user_prompt": topic_config.get("prompt", f"生成 1 題 {topic_code} 題目。"),
        "topic_code": topic_code,
        "verification_rules": topic_config.get("verification", {}),
        "max_iterations": MAX_SELF_REFINE_ITERATIONS,
        "refine_template": REFINE_FEEDBACK_TEMPLATE,
    }


def build_refine_feedback(verify_result: dict) -> str:
    """
    Build structured feedback for Self-Refine from verify results.
    """
    reasons = verify_result.get("reasons", {})
    failures = []
    for gate, reason in reasons.items():
        if reason != "ok":
            failures.append(f"- {gate}: {reason}")
    if not failures:
        return ""
    failure_text = "\n".join(failures)
    return REFINE_FEEDBACK_TEMPLATE.format(failure_reasons=failure_text)


def create_human_review_entry(
    problem: dict | None,
    topic_code: str,
    iterations: int,
    last_verify_result: dict | None = None,
) -> dict:
    """
    Create a human review queue entry for problems that failed Self-Refine.
    """
    return {
        "topic_code": topic_code,
        "iterations_attempted": iterations,
        "max_iterations": MAX_SELF_REFINE_ITERATIONS,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "problem_draft": problem,
        "last_verify_result": last_verify_result,
    }


# ── CLI ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate curriculum-aligned problems")
    parser.add_argument("--out", required=True, help="Output JSONL path")
    parser.add_argument("--count", type=int, default=20, help="Number of problems to generate")
    parser.add_argument(
        "--topics", type=str, default="",
        help="Comma-separated topic codes to generate (default: all)"
    )
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    topics = args.topics.split(",") if args.topics else ALL_TOPIC_CODES

    print(f"[generate] stub — no LLM configured")
    print(f"[generate] Would generate {args.count} problems to {args.out}")
    print(f"[generate] Target topics: {', '.join(topics)}")
    print(f"[generate] Max Self-Refine iterations: {MAX_SELF_REFINE_ITERATIONS}")
    print()
    print("[generate] To enable: configure API key and implement generate_problem_stub()")
    print()
    print("[generate] Available topic prompts:")
    for code in topics:
        config = TOPIC_PROMPTS.get(code, {})
        prompt = config.get("prompt", f"(no prompt for {code})")
        print(f"  {code}: {prompt[:80]}...")
    print()
    print("[generate] Agent roles:")
    for role, prompt in AgentRole.ROLE_PROMPTS.items():
        print(f"  {role}: {prompt[:60]}...")
    print()
    print("[generate] Generation request example:")
    if topics:
        req = build_generation_request(topics[0])
        print(json.dumps(req, ensure_ascii=False, indent=2)[:500])

    sys.exit(0)


if __name__ == "__main__":
    main()
