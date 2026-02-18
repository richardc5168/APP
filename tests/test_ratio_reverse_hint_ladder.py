from fractions import Fraction


def _build_q(question: str):
    return {
        "topic": "分數應用題(五年級)",
        "question": question,
    }


def test_ratio_reverse_ladder_core_case_2_3_and_7_8():
    import engine

    q = _build_q("走完全程需要多少小時？若走了全程的 2/3 時，用了 7/8 小時。")
    ladder = engine.build_ratio_reverse_hint_ladder(q)

    assert isinstance(ladder, list)
    assert len(ladder) == 7

    # Step 3 列式
    s3 = ladder[2]
    assert "T × 2/3 = 7/8" in str(s3.get("formula")) or "T×2/3=7/8" in str(s3.get("expected_answer"))

    # Step 5 倒數
    s5 = ladder[4]
    assert str(s5.get("expected_answer")) == "3/2"

    # Step 6 計算
    s6 = ladder[5]
    assert "21/16" in str(s6.get("formula"))

    # Step 7 驗算
    s7 = ladder[6]
    assert "= 7/8" in str(s7.get("formula"))


def test_ratio_reverse_math_random_case_3_5_and_9_10():
    import engine

    q = _build_q("完成了 3/5 路程，用了 9/10 小時，走完全程要多久？")
    parsed = engine._extract_ratio_reverse_case(q["question"])
    assert parsed is not None

    total = parsed["total_time"]
    assert total == Fraction(3, 2)

    # verify equality: T * a/b == c/d
    lhs = total * parsed["frac_part"]
    assert lhs == parsed["used_time"]


def test_ratio_reverse_math_random_case_minutes():
    import engine

    q = _build_q("做了全程的 4/7，用了 6/7 分鐘，求全程時間。")
    parsed = engine._extract_ratio_reverse_case(q["question"])
    assert parsed is not None

    # T = (6/7) ÷ (4/7) = 3/2
    assert parsed["total_time"] == Fraction(3, 2)
    assert parsed["unit"] == "分鐘"


def test_get_next_step_hint_includes_structured_ladder_for_ratio_reverse():
    import engine

    q = _build_q("走完全程需要多少小時？若走了全程的 2/3 時，用了 7/8 小時。")
    out = engine.get_next_step_hint(q, student_state="先設 T", level=2)

    assert isinstance(out, dict)
    assert isinstance(out.get("hint"), str) and out["hint"]
    assert isinstance(out.get("hint_ladder"), list)
    assert len(out["hint_ladder"]) == 7
    assert isinstance(out.get("current_step"), dict)


def test_get_question_hints_uses_ratio_reverse_branch():
    import engine

    q = _build_q("做了全程的 2/3，用了 7/8 小時，求全程時間。")
    hints = engine.get_question_hints(q)

    assert isinstance(hints, dict)
    assert "T" in str(hints.get("level1", ""))
    assert "T" in str(hints.get("level2", ""))
    assert "驗算" in str(hints.get("level3", "")) or "代回" in str(hints.get("level3", ""))
