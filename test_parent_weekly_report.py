import sqlite3
from typing import Any, Dict, Optional

import pytest

from learning.db import ensure_learning_schema
from learning.parent_report import generate_parent_weekly_report


def _qfactory(topic_key: Optional[str]) -> Dict[str, Any]:
    # Deterministic stub question generator (do NOT depend on engine randomness).
    return {
        "topic": topic_key or "unknown",
        "difficulty": "stub",
        "question": f"Q({topic_key})",
        "answer": f"A({topic_key})",
        "explanation": "",
        "steps": ["s1", "s2"],
    }


def _insert_attempt(
    conn: sqlite3.Connection,
    *,
    student_id: str,
    question_id: str,
    ts: str,
    is_correct: int,
    skill_tag: str,
    hints: int = 0,
    mistake_code: Optional[str] = None,
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO la_students(student_id, created_at, meta_json) VALUES (?,?,?)",
        (student_id, ts, "{}"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO la_questions(question_id, created_at, meta_json) VALUES (?,?,?)",
        (question_id, ts, "{}"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO la_skill_tags(skill_tag, created_at, description) VALUES (?,?,?)",
        (skill_tag, ts, None),
    )

    cur = conn.execute(
        """
        INSERT INTO la_attempt_events(
          student_id, question_id, ts, is_correct, answer_raw,
          duration_ms, hints_viewed_count, hint_steps_viewed_json,
          mistake_code, unit, topic, question_type,
          session_id, device_json, extra_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            student_id,
            question_id,
            ts,
            int(is_correct),
            "x",
            15000,
            int(hints),
            "[]",
            mistake_code,
            None,
            "topic",
            "interactive",
            "sess",
            "{}",
            "{}",
        ),
    )
    attempt_id = int(cur.lastrowid)
    conn.execute(
        "INSERT OR IGNORE INTO la_attempt_skill_tags(attempt_id, skill_tag) VALUES (?,?)",
        (attempt_id, skill_tag),
    )


def test_generate_parent_weekly_report_deterministic(tmp_path: pytest.TempPathFactory):
    db_path = tmp_path.mktemp("db") / "t.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    ensure_learning_schema(conn)

    # Build evidence: make 分數/小數 clearly weak.
    # 8 wrong + hint usage; plus a few correct for another skill.
    for i in range(8):
        _insert_attempt(
            conn,
            student_id="1",
            question_id=f"qf{i}",
            ts=f"2026-02-15T10:0{i}:00",
            is_correct=0,
            skill_tag="分數/小數",
            hints=2,
            mistake_code="concept",
        )
    for i in range(3):
        _insert_attempt(
            conn,
            student_id="1",
            question_id=f"qa{i}",
            ts=f"2026-02-15T11:0{i}:00",
            is_correct=1,
            skill_tag="四則運算",
            hints=0,
            mistake_code=None,
        )
    conn.commit()

    report1 = generate_parent_weekly_report(
        conn,
        student_id="1",
        window_days=7,
        top_k=2,
        questions_per_skill=2,
        question_factory=_qfactory,
    )
    report2 = generate_parent_weekly_report(
        conn,
        student_id="1",
        window_days=7,
        top_k=2,
        questions_per_skill=2,
        question_factory=_qfactory,
    )

    assert report1["report_markdown"] == report2["report_markdown"]
    assert "家長週報" in report1["report_markdown"]

    assert "summary" in report1
    assert "kpi" in report1["summary"]
    assert isinstance(report1["summary"]["kpi"].get("attempts_7d"), int)

    # Ensure it generated practice questions and kept answers separate.
    assert len(report1["practice_set"]) >= 1
    first = report1["practice_set"][0]
    assert "practice" in first
    assert "status" in first
    assert first["status"]["code"] in ("NEED_FOCUS", "IMPROVING", "MASTERED", "NOT_ENOUGH_DATA")
    assert len(first["practice"]["questions"]) == 2
    assert len(first["practice"]["answer_key"]) == 2

    conn.close()
