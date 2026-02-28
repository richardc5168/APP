"""
tests/unit/test_pipeline_scorecard.py — Unit tests for granular scorecard module.

Covers:
- Individual dimension scorers (correctness, step_consistency, step_completeness,
  answer_reasonableness, anti_cheat_dedup)
- Composite scorecard computation
- Edge cases (missing values, non-numeric answers, low confidence)
- Numeric flow checks between steps
- Topic-specific scoring (N-5-10 percent, N-6-7 formula, D-5-1 data points)
"""
import pytest

from pipeline.scorecard import (
    compute_scorecard,
    score_answer_reasonableness,
    score_anti_cheat_dedup,
    score_correctness,
    score_step_completeness,
    score_step_consistency,
)


def _make_problem(
    value=10,
    unit="元",
    steps=None,
    topic_codes=None,
    answer_type="integer",
    confidence=0.95,
    **extra,
):
    """Build a test problem dict."""
    _steps = steps if steps is not None else ["步驟一：計算", "步驟二：得到 10"]
    p = {
        "id": "SCORE-TEST",
        "grade": 5,
        "stage": "III",
        "topic_codes": topic_codes or ["n-III-6"],
        "question": "測試題目，小明有幾顆蘋果？",
        "answer_type": answer_type,
        "solution": {
            "steps": _steps,
            "answer": {"value": value, "unit": unit, "tolerance": 0},
        },
        "source": {
            "url": "https://example.com",
            "license_type": "CC BY 4.0",
            "captured_at": "2026-01-01T00:00:00Z",
        },
        "confidence": confidence,
    }
    p.update(extra)
    return p


class TestScoreCorrectness:
    def test_valid_numeric_answer(self):
        assert score_correctness(_make_problem(value=42)) == 1.0

    def test_missing_answer_value(self):
        p = _make_problem()
        p["solution"]["answer"] = {}
        assert score_correctness(p) == 0.0

    def test_negative_answer(self):
        assert score_correctness(_make_problem(value=-5)) == 0.0

    def test_non_numeric_answer(self):
        assert score_correctness(_make_problem(value="週四")) == 0.8

    def test_fraction_answer(self):
        assert score_correctness(_make_problem(value="3/2")) == 1.0

    def test_n510_percent_over_100(self):
        p = _make_problem(value=150, topic_codes=["N-5-10"], answer_type="percent")
        assert score_correctness(p) == 0.0

    def test_low_confidence_penalty(self):
        assert score_correctness(_make_problem(confidence=0.5)) == 0.6


class TestScoreStepConsistency:
    def test_numeric_flow_no_overlap(self):
        """Steps where output number differs from input (e.g. multiplication result)."""
        p = _make_problem(steps=["800 × 0.8", "= 640"])
        score = score_step_consistency(p)
        # Numbers don't overlap (800/0.8 vs 640) but that's a valid calculation
        assert 0.3 <= score <= 0.8

    def test_numeric_flow_with_overlap(self):
        """Steps sharing numbers should score higher."""
        p = _make_problem(steps=["800 × 0.8 = 640", "售價 = 640 元"])
        score = score_step_consistency(p)
        assert score >= 0.9

    def test_empty_steps(self):
        p = _make_problem(steps=[])
        assert score_step_consistency(p) == 0.0

    def test_single_step(self):
        p = _make_problem(steps=["只有一步"])
        assert score_step_consistency(p) == 0.7

    def test_formula_step_not_penalized(self):
        """Steps like '距離=速度×時間' without numbers shouldn't hurt flow."""
        p = _make_problem(
            steps=["30 分鐘 = 0.5 小時", "距離=速度×時間", "距離 = 12 × 0.5 = 6"],
            topic_codes=["N-6-7"],
        )
        score = score_step_consistency(p)
        assert score >= 0.7

    def test_n67_missing_formula(self):
        p = _make_problem(
            steps=["先換算", "12 × 0.5 = 6"],
            topic_codes=["N-6-7"],
        )
        score = score_step_consistency(p)
        assert score < 1.0  # Penalty for missing formula


class TestScoreStepCompleteness:
    def test_enough_steps(self):
        p = _make_problem(steps=["s1", "s2", "s3"])
        assert score_step_completeness(p) == 1.0

    def test_below_topic_minimum(self):
        p = _make_problem(steps=["only one"], topic_codes=["N-6-7"])
        assert score_step_completeness(p) < 1.0

    def test_respects_expected_steps_min(self):
        p = _make_problem(steps=["s1", "s2"], expected_steps_min=4)
        assert score_step_completeness(p) == 0.5

    def test_empty_steps(self):
        p = _make_problem(steps=[])
        assert score_step_completeness(p) == 0.0


class TestScoreAnswerReasonableness:
    def test_normal_positive_answer(self):
        assert score_answer_reasonableness(_make_problem(value=42)) == 1.0

    def test_negative_penalty(self):
        score = score_answer_reasonableness(_make_problem(value=-5))
        assert score < 1.0

    def test_missing_unit_for_n67(self):
        p = _make_problem(value=6, unit="", topic_codes=["N-6-7"])
        score = score_answer_reasonableness(p)
        assert score < 1.0  # Penalty for missing unit

    def test_has_unit_for_n67(self):
        p = _make_problem(value=6, unit="公里", topic_codes=["N-6-7"])
        assert score_answer_reasonableness(p) == 1.0

    def test_text_answer(self):
        p = _make_problem(value="週四")
        score = score_answer_reasonableness(p)
        assert score > 0.5  # Text answers are acceptable


class TestScoreAntiCheatDedup:
    def test_clean_question(self):
        score = score_anti_cheat_dedup(_make_problem())
        assert score == 1.0

    def test_textbook_reference_penalty(self):
        p = _make_problem()
        p["question"] = "翰林版數學第 3 課"
        score = score_anti_cheat_dedup(p)
        assert score < 1.0

    def test_high_similarity_penalty(self):
        p = _make_problem(similarity_score=0.90)
        score = score_anti_cheat_dedup(p)
        assert score < 1.0

    def test_bank_dedup(self):
        p = _make_problem()
        p["question"] = "小明有 5 顆蘋果"
        bank = ["小明有 5 顆蘋果，吃了 2 顆"]
        score = score_anti_cheat_dedup(p, existing_questions=bank)
        # Short similar texts — should still be OK since below threshold
        assert score >= 0.5


class TestCompositeScorecard:
    def test_all_gates_pass_structure(self):
        p = _make_problem()
        gates = {"schema": True, "correctness": True, "steps": True, "license": True}
        sc = compute_scorecard(p, gates)
        assert "dimensions" in sc
        assert "weights" in sc
        assert "total" in sc
        assert "gates_all_passed" in sc
        assert sc["gates_all_passed"] is True
        assert 0 <= sc["total"] <= 100

    def test_some_gates_fail(self):
        p = _make_problem()
        gates = {"schema": True, "correctness": False, "steps": True, "license": True}
        sc = compute_scorecard(p, gates)
        assert sc["gates_all_passed"] is False

    def test_good_problem_scores_high(self):
        p = _make_problem(
            value=640,
            unit="元",
            steps=["八折 = 80% = 0.8", "售價 = 800 × 0.8 = 640"],
            topic_codes=["n-III-9", "N-5-10"],
        )
        gates = {"schema": True, "correctness": True, "steps": True, "license": True}
        sc = compute_scorecard(p, gates)
        assert sc["total"] >= 80
