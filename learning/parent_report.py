from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from . import analytics as analytics_mod
from .remediation import generate_remediation_plan
from .teaching import get_teaching_guide, suggested_engine_topic_key


try:
    import engine as _engine
except Exception:  # pragma: no cover
    _engine = None


QuestionFactory = Callable[[Optional[str]], Dict[str, Any]]


def _default_question_factory(topic_key: Optional[str]) -> Dict[str, Any]:
    if _engine is None or not hasattr(_engine, "next_question"):
        return {
            "topic": "unknown",
            "difficulty": "unknown",
            "question": "（題目產生器未載入）",
            "answer": "",
            "explanation": "",
            "steps": [],
        }
    return _engine.next_question(topic_key)


def _seed_for(student_id: str, skill_tag: str, *, day: str) -> int:
    s = f"{student_id}|{skill_tag}|{day}"
    return abs(hash(s)) % (2**31 - 1)


def _md_list(items: List[str]) -> str:
    return "\n".join([f"- {x}" for x in items])


def _safe_date_yyyymmdd(ts_iso: str) -> str:
    try:
        return datetime.fromisoformat(ts_iso.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")


def _build_skill_section(
    *,
    student_id: str,
    skill_tag: str,
    evidence: Dict[str, Any],
    question_factory: QuestionFactory,
    questions_per_skill: int,
    day: str,
) -> Tuple[Dict[str, Any], str]:
    guide = get_teaching_guide(skill_tag)

    topic_key = suggested_engine_topic_key(skill_tag)
    seed = _seed_for(student_id, skill_tag, day=day)

    questions: List[Dict[str, Any]] = []
    answer_key: List[str] = []

    # Make question selection deterministic per-day per-skill.
    rng = random.Random(seed)
    for i in range(int(questions_per_skill)):
        q_seed = rng.randint(1, 10_000_000)
        state = random.getstate()
        random.seed(q_seed)
        try:
            q = question_factory(topic_key)
        finally:
            random.setstate(state)

        # Parent report: include question text; keep answer in a separate key.
        questions.append(
            {
                "topic": q.get("topic"),
                "difficulty": q.get("difficulty"),
                "question": q.get("question"),
                "steps": q.get("steps") or [],
            }
        )
        answer_key.append(str(q.get("answer") or ""))

    acc = float(evidence.get("score_inputs", {}).get("accuracy") or 0.0)
    hd = float(evidence.get("score_inputs", {}).get("hint_dependency") or 0.0)
    attempts = int(evidence.get("score_inputs", {}).get("attempts") or 0)

    section_md = "\n".join(
        [
            f"### 弱點：{guide.title}",
            f"- 本週嘗試 {attempts} 題，正確率 {round(acc * 100, 1)}%，提示依賴 {round(hd * 100, 1)}%",
            "\n**觀念補充（家長可照這個問孩子）**",
            _md_list(guide.key_ideas),
            "\n**常見錯誤提醒**",
            _md_list(guide.common_mistakes),
            "\n**本週練習目標**",
            f"- {guide.practice_goal}",
            "\n**掌握檢核（做到才算真的會）**",
            f"- {guide.mastery_check}",
            "\n**針對弱點出題（練習題）**",
            *[f"- 題目 {idx + 1}：{qq.get('question')}" for idx, qq in enumerate(questions)],
        ]
    )

    payload = {
        "skill_tag": skill_tag,
        "guide": guide.__dict__,
        "evidence": evidence,
        "practice": {
            "topic_key": topic_key,
            "questions": questions,
            "answer_key": answer_key,
        },
    }

    return payload, section_md


def generate_parent_weekly_report(
    conn,
    *,
    student_id: str,
    window_days: int = 7,
    dataset_blueprint: Optional[Any] = None,
    top_k: int = 3,
    questions_per_skill: int = 3,
    question_factory: Optional[QuestionFactory] = None,
) -> Dict[str, Any]:
    """Generate a parent-friendly weekly report + targeted practice set.

    Returns a dict with keys: analytics, plan, report_markdown, practice_set.
    """

    analytics = analytics_mod.get_student_analytics(conn, student_id=str(student_id), window_days=int(window_days))
    plan = generate_remediation_plan(analytics, blueprint=dataset_blueprint, top_k=int(top_k))

    qf = question_factory or _default_question_factory

    day = _safe_date_yyyymmdd(str(analytics.get("generated_at") or ""))

    practice_set: List[Dict[str, Any]] = []
    sections: List[str] = []

    weak = plan.get("weak_skills_top3") or []
    for t in weak:
        skill_tag = str(t.get("skill_tag") or "unknown")
        payload, md = _build_skill_section(
            student_id=str(student_id),
            skill_tag=skill_tag,
            evidence=t,
            question_factory=qf,
            questions_per_skill=int(questions_per_skill),
            day=day,
        )
        practice_set.append(payload)
        sections.append(md)

    header = "\n".join(
        [
            "# 家長週報（學習弱點 + 練習建議）",
            f"- 學生：{student_id}",
            f"- 期間：最近 {int(window_days)} 天",
            "\n## 本週重點（先做最弱的 1–3 個觀念）",
            "- 原則：先把『觀念說清楚』再做題；錯題當天訂正並同類再做 2 題。",
            "- 目標：正確率提高、提示依賴下降，並能解釋每一步。",
        ]
    )

    report_md = "\n\n".join([header] + sections)

    return {
        "analytics": analytics,
        "plan": plan,
        "practice_set": practice_set,
        "report_markdown": report_md,
    }
