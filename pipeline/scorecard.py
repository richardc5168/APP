"""
pipeline/scorecard.py — Granular scoring system for curriculum-aligned problems.

Scorecard (0-100), weighted:
  - correctness      (40): answer complete match / within tolerance
  - step_consistency  (25): adjacent steps equivalence / derivation passes
  - step_completeness (15): step count vs minimum + required intermediates
  - answer_reasonable (10): value range, unit, context plausibility
  - anti_cheat_dedup  (10): similarity below threshold + no reproduction patterns

Gate results are hard gates (must all pass for auto-publish).
Score is a soft metric for ranking/prioritizing problems when all gates pass.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from pipeline.source_governance import (
    check_similarity_against_bank,
    check_textbook_reproduction,
)

# ── Topic-Specific Scoring Config ──────────────────────────

TOPIC_MIN_STEPS: dict[str, int] = {
    "N-6-7": 2,
    "S-6-2": 2,
    "N-5-10": 2,
    "N-5-11": 2,
    "N-6-3": 2,
    "D-5-1": 2,
}

TOPIC_REQUIRED_FORMULAS: dict[str, list[str]] = {
    "N-6-7": ["距離=速度×時間", "速度=距離÷時間", "時間=距離÷速度"],
}

# ── Helper: Parse Numeric ──────────────────────────────────

def _parse_numeric(value: Any) -> float | None:
    """Try to parse a value as a float (handles fractions like '3/2')."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(Fraction(value))
        except (ValueError, ZeroDivisionError):
            pass
        try:
            return float(value)
        except ValueError:
            pass
    return None


# ── Dimension Scorers ──────────────────────────────────────

def score_correctness(p: dict) -> float:
    """
    Score 0.0–1.0 for answer correctness.
    Full credit if answer.value is present and within tolerance.
    """
    sol = p.get("solution", {})
    ans = sol.get("answer", {})
    if ans.get("value") is None:
        return 0.0

    val = _parse_numeric(ans["value"])
    if val is None:
        # Non-numeric (e.g. "週四") — give partial credit if present
        return 0.8

    tolerance = ans.get("tolerance", 0)
    codes = p.get("topic_codes", [])

    # N-5-10 percent check
    if any(c.startswith("N-5-10") for c in codes):
        if p.get("answer_type") == "percent" and val > 100:
            return 0.0

    # Negative sanity
    if val < 0:
        return 0.0

    # Low confidence penalty
    conf = p.get("confidence", 1.0)
    if conf < 0.7:
        return 0.6  # Correct but uncertain

    return 1.0


def score_step_consistency(p: dict) -> float:
    """
    Score 0.0–1.0 for step-to-step consistency.

    Checks:
    - Adjacent steps share numeric continuity (output of step N appears in step N+1)
    - Unit mentions are consistent across steps
    - Required formulas appear
    """
    sol = p.get("solution", {})
    steps = sol.get("steps", [])
    if len(steps) == 0:
        return 0.0
    if len(steps) == 1:
        return 0.7  # Single step — can't verify consistency

    codes = p.get("topic_codes", [])
    score = 1.0

    # Check formula presence for topics that require it
    for code in codes:
        formulas = TOPIC_REQUIRED_FORMULAS.get(code, [])
        if formulas:
            all_text = " ".join(steps)
            if not any(f in all_text for f in formulas):
                score -= 0.3

    # Check numeric flow: numbers from step i should appear in step i+1
    # Skip flow checks when either step has no numbers (formula/concept steps)
    number_re = re.compile(r"\d+\.?\d*")
    flow_checks = 0
    flow_passes = 0
    for i in range(len(steps) - 1):
        nums_i = set(number_re.findall(steps[i]))
        nums_next = set(number_re.findall(steps[i + 1]))
        if nums_i and nums_next:  # Only check when both steps have numbers
            flow_checks += 1
            # At least one number from current step should appear in next
            if nums_i & nums_next:
                flow_passes += 1

    if flow_checks > 0:
        flow_ratio = flow_passes / flow_checks
        score *= (0.5 + 0.5 * flow_ratio)  # 50% base + 50% from flow

    return max(0.0, min(1.0, score))


def score_step_completeness(p: dict) -> float:
    """
    Score 0.0–1.0 for step completeness.

    Checks step count against topic-specific minimums and general heuristics.
    """
    sol = p.get("solution", {})
    steps = sol.get("steps", [])
    codes = p.get("topic_codes", [])

    if len(steps) == 0:
        return 0.0

    # Use explicit expected_steps_min if provided
    expected_min = p.get("expected_steps_min", 1)

    # Also check topic-specific minimums
    for code in codes:
        topic_min = TOPIC_MIN_STEPS.get(code, 1)
        expected_min = max(expected_min, topic_min)

    if len(steps) < expected_min:
        return len(steps) / expected_min  # Partial credit

    return 1.0


def score_answer_reasonableness(p: dict) -> float:
    """
    Score 0.0–1.0 for answer plausibility.

    Checks:
    - Value is non-negative for distance/price/percentage
    - Value is within expected range for topic
    - Unit is present when expected
    """
    sol = p.get("solution", {})
    ans = sol.get("answer", {})
    val = _parse_numeric(ans.get("value"))
    unit = ans.get("unit", "")
    codes = p.get("topic_codes", [])

    score = 1.0

    # Non-numeric answer (text like "週四")
    if val is None:
        # Text answer — unit shouldn't be required
        return 0.9

    # Negative value penalty
    if val < 0:
        score -= 0.5

    # Check unit presence for topics that should have units
    unit_expected_topics = {"N-6-7", "S-6-2", "N-5-10"}
    for code in codes:
        if code in unit_expected_topics and not unit:
            score -= 0.2

    # N-5-10 percent range check
    if any(c.startswith("N-5-10") for c in codes):
        if p.get("answer_type") == "percent" and val > 100:
            score -= 0.5

    # Extreme value sanity check
    if val > 1_000_000:
        score -= 0.1  # Unusual for elementary math

    return max(0.0, min(1.0, score))


def score_anti_cheat_dedup(
    p: dict,
    existing_questions: list[str] | None = None,
) -> float:
    """
    Score 0.0–1.0 for anti-cheat/dedup.

    Checks:
    - Textbook reproduction patterns
    - Similarity against existing bank
    - Pre-computed similarity_score field
    """
    question = p.get("question", "")
    score = 1.0

    # Textbook reproduction check
    is_safe, pattern = check_textbook_reproduction(question)
    if not is_safe:
        score -= 0.5

    # Check steps for textbook markers
    steps_text = " ".join(p.get("solution", {}).get("steps", []))
    is_safe_steps, _ = check_textbook_reproduction(steps_text)
    if not is_safe_steps:
        score -= 0.3

    # Use pre-computed similarity score if available
    sim = p.get("similarity_score")
    if sim is not None and sim > 0.85:
        score -= 0.4

    # Check against provided bank if available
    if existing_questions:
        is_unique, max_sim, _ = check_similarity_against_bank(
            question, existing_questions, threshold=0.85
        )
        if not is_unique:
            score -= 0.4

    return max(0.0, min(1.0, score))


# ── Composite Score ────────────────────────────────────────

def compute_scorecard(
    p: dict,
    gates: dict[str, bool],
    existing_questions: list[str] | None = None,
) -> dict:
    """
    Compute the full scorecard for a problem.

    Returns dict with dimension scores (0.0–1.0) and weighted total (0–100).
    Gates are hard requirements; score is for soft ranking.
    """
    dims = {
        "correctness": score_correctness(p),
        "step_consistency": score_step_consistency(p),
        "step_completeness": score_step_completeness(p),
        "answer_reasonableness": score_answer_reasonableness(p),
        "anti_cheat_dedup": score_anti_cheat_dedup(p, existing_questions),
    }

    weights = {
        "correctness": 40,
        "step_consistency": 25,
        "step_completeness": 15,
        "answer_reasonableness": 10,
        "anti_cheat_dedup": 10,
    }

    weighted_total = sum(
        dims[dim] * weights[dim] for dim in dims
    )
    total = round(weighted_total)

    return {
        "dimensions": {k: round(v, 3) for k, v in dims.items()},
        "weights": weights,
        "total": total,
        "gates_all_passed": all(gates.values()),
    }
