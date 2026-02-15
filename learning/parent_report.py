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


_REASON_LABELS_ZH = {
    "low_accuracy": "正確率偏低",
    "high_hint_dependency": "常需要提示才能做對",
    "repeated_mistake_code": "同類錯誤重複出現",
}


def _format_reasons_zh(reasons: List[str]) -> List[str]:
    out: List[str] = []
    for r in reasons:
        out.append(_REASON_LABELS_ZH.get(r, str(r)))
    return out


def _mastery_targets(*, skill_tag: str) -> Dict[str, Any]:
    """Numeric mastery targets used for 'until mastery' loops.

    Keep this simple and stable; the teaching guide contains the human phrasing.
    """

    # Defaults.
    return {
        "min_attempts": 10,
        "min_accuracy": 0.85,
        "max_hint_dependency": 0.30,
        "note": "以最近作答為主：正確率提高 + 提示依賴下降",
    }


def _skill_status(
    *,
    attempts: int,
    accuracy: float,
    hint_dependency: float,
    targets: Dict[str, Any],
) -> str:
    """Return one of: NEED_FOCUS | IMPROVING | MASTERED | NOT_ENOUGH_DATA"""

    if attempts < int(targets.get("min_attempts") or 0):
        return "NOT_ENOUGH_DATA"

    min_acc = float(targets.get("min_accuracy") or 0.0)
    max_hd = float(targets.get("max_hint_dependency") or 1.0)

    if accuracy >= min_acc and hint_dependency <= max_hd:
        return "MASTERED"

    # Improving: close to target but not yet.
    if accuracy >= max(0.0, min_acc - 0.10):
        return "IMPROVING"

    return "NEED_FOCUS"


def _kpi_summary(analytics: Dict[str, Any]) -> Dict[str, Any]:
    trend = analytics.get("trend") or []
    by_days = {int(x.get("days") or 0): x for x in trend if isinstance(x, dict)}
    t7 = by_days.get(7) or {"attempts": 0, "accuracy": 0.0}
    t14 = by_days.get(14) or {"attempts": 0, "accuracy": 0.0}
    a7 = float(t7.get("accuracy") or 0.0)
    a14 = float(t14.get("accuracy") or 0.0)
    delta = a7 - a14

    direction = "up" if delta > 0.03 else ("down" if delta < -0.03 else "flat")
    return {
        "attempts_7d": int(t7.get("attempts") or 0),
        "accuracy_7d": a7,
        "attempts_14d": int(t14.get("attempts") or 0),
        "accuracy_14d": a14,
        "accuracy_direction": direction,
        "accuracy_delta_7d_vs_14d": round(delta, 6),
    }


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
    reasons = evidence.get("evidence", {}).get("reasons")
    if not isinstance(reasons, list):
        reasons = evidence.get("reasons") if isinstance(evidence.get("reasons"), list) else []

    targets = _mastery_targets(skill_tag=skill_tag)
    status = _skill_status(attempts=attempts, accuracy=acc, hint_dependency=hd, targets=targets)

    # Pull suggested practice items for this skill (if present in remediation plan wrapper).
    suggested_practice = evidence.get("suggested_practice")
    if not isinstance(suggested_practice, list):
        suggested_practice = []

    status_zh = {
        "NEED_FOCUS": "需要加強",
        "IMPROVING": "改善中",
        "MASTERED": "已掌握",
        "NOT_ENOUGH_DATA": "資料不足（先多做幾題觀察）",
    }.get(status, status)

    reasons_zh = _format_reasons_zh([str(x) for x in reasons])
    targets_line = f"掌握門檻：最近作答 ≥{int(targets['min_attempts'])} 題，正確率 ≥{int(float(targets['min_accuracy']) * 100)}%，提示依賴 ≤{int(float(targets['max_hint_dependency']) * 100)}%"

    section_md = "\n".join(
        [
            f"### 弱點：{guide.title}",
            f"- 狀態：{status_zh}",
            f"- 本週嘗試 {attempts} 題，正確率 {round(acc * 100, 1)}%，提示依賴 {round(hd * 100, 1)}%",
            ("- 主要原因：" + "、".join(reasons_zh)) if reasons_zh else "- 主要原因：無（以數據為準）",
            f"- {targets_line}",
            "\n**建議題型（先做這些最有效）**",
            _md_list([f"{p.get('title')}（{p.get('rationale')}）" for p in suggested_practice]) if suggested_practice else "- （尚無對應題型，先做基礎練習）",
            "\n**觀念補充（家長可照這個問孩子）**",
            _md_list(guide.key_ideas),
            "\n**常見錯誤提醒**",
            _md_list(guide.common_mistakes),
            "\n**本週練習目標**",
            f"- {guide.practice_goal}",
            "\n**掌握檢核（做到才算真的會）**",
            f"- {guide.mastery_check}",
            "\n**練習迴圈（直到達標）**",
            _md_list(
                [
                    "先用自己的話講 2 句：這題在問什麼？基準量是什麼？",
                    "做 3 題同類題（先不看提示）。",
                    "錯題：當天訂正後『同類再做 2 題』確認不再犯。",
                    "達到掌握門檻後，再換另一個弱點。",
                ]
            ),
            "\n**針對弱點出題（練習題）**",
            *[f"- 題目 {idx + 1}：{qq.get('question')}" for idx, qq in enumerate(questions)],
        ]
    )

    payload = {
        "skill_tag": skill_tag,
        "guide": guide.__dict__,
        "evidence": evidence,
        "status": {
            "code": status,
            "label": status_zh,
            "targets": targets,
            "targets_line": targets_line,
        },
        "suggested_practice": suggested_practice,
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
    practice_seq = plan.get("suggested_practice_sequence") or []
    by_skill_practice: Dict[str, List[Dict[str, Any]]] = {}
    if isinstance(practice_seq, list):
        for p in practice_seq:
            if not isinstance(p, dict):
                continue
            sk = str(p.get("skill_tag") or "unknown")
            by_skill_practice.setdefault(sk, []).append(p)

    for t in weak:
        skill_tag = str(t.get("skill_tag") or "unknown")
        # Attach suggested practice items for this weakness.
        tw = dict(t)
        tw["suggested_practice"] = by_skill_practice.get(skill_tag, [])
        payload, md = _build_skill_section(
            student_id=str(student_id),
            skill_tag=skill_tag,
            evidence=tw,
            question_factory=qf,
            questions_per_skill=int(questions_per_skill),
            day=day,
        )
        practice_set.append(payload)
        sections.append(md)

    kpi = _kpi_summary(analytics)
    focus_skills = [str(x.get("skill_tag") or "") for x in (plan.get("weak_skills_top3") or []) if isinstance(x, dict)]
    focus_skills = [x for x in focus_skills if x]

    header = "\n".join(
        [
            "# 家長週報（學習弱點 + 練習建議）",
            f"- 學生：{student_id}",
            f"- 期間：最近 {int(window_days)} 天",
            "\n## 一眼看懂（本週狀況）",
            f"- 7 天作答：{kpi['attempts_7d']} 題；正確率：{round(kpi['accuracy_7d'] * 100, 1)}%",
            f"- 14 天正確率：{round(kpi['accuracy_14d'] * 100, 1)}%（趨勢：{kpi['accuracy_direction']}）",
            ("- 本週先做：" + " → ".join(focus_skills)) if focus_skills else "- 本週先做：目前資料不足，先做基礎題收集作答紀錄",
            "\n## 本週重點（先做最弱的 1–3 個觀念）",
            "- 原則：先把『觀念說清楚』再做題；錯題當天訂正並同類再做 2 題。",
            "- 目標：正確率提高、提示依賴下降，並能解釋每一步。",
        ]
    )

    report_md = "\n\n".join([header] + sections)

    return {
        "summary": {
            "kpi": kpi,
            "focus_skills": focus_skills,
        },
        "analytics": analytics,
        "plan": plan,
        "practice_set": practice_set,
        "report_markdown": report_md,
    }
