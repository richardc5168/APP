# -*- coding: utf-8 -*-
import re
from fastapi.testclient import TestClient

from server import app


client = TestClient(app)


def _bootstrap_get_api_key() -> str:
    r = client.post("/admin/bootstrap?name=HintOfflineTest")
    assert r.status_code == 200, r.text
    data = r.json()
    api_key = data.get("api_key")
    assert api_key
    return api_key


def _create_student(api_key: str) -> int:
    r = client.post(
        "/v1/students?display_name=demo&grade=G5",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200, r.text

    r = client.get("/v1/students", headers={"X-API-Key": api_key})
    assert r.status_code == 200, r.text
    return int(r.json()["students"][0]["id"])


def _next_question(api_key: str, student_id: int, topic_key: str) -> dict:
    r = client.post(
        f"/v1/questions/next?student_id={student_id}&topic_key={topic_key}",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _next_hint(api_key: str, *, question_id: int | None = None, question_data: dict | None = None, student_state: str = "", level: int = 1) -> dict:
    payload: dict = {"student_state": student_state, "level": level}
    if question_id is not None:
        payload["question_id"] = question_id
    if question_data is not None:
        payload["question_data"] = question_data

    r = client.post(
        "/v1/hints/next",
        headers={"X-API-Key": api_key},
        json=payload,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("hint") and str(data["hint"]).strip()
    assert int(data.get("level", level)) in (1, 2, 3)
    return data


def _assert_no_direct_answer_leak(hint: str):
    # Heuristic: do not contain explicit "答案" wording or equation that looks like final result.
    s = str(hint)
    assert "答案" not in s
    assert not re.search(r"=\s*\d+\s*(?:/\s*\d+)?\b", s)


def test_hints_next_offline_8plus_cases():
    api_key = _bootstrap_get_api_key()
    sid = _create_student(api_key)

    # 1) Fraction word problems (topic_key=11) + empty state
    q = _next_question(api_key, sid, "11")
    h = _next_hint(api_key, question_id=q["question_id"], student_state="", level=1)
    _assert_no_direct_answer_leak(h["hint"])

    # 2) Same question + partial setup state
    h = _next_hint(api_key, question_id=q["question_id"], student_state="我先圈出分數和總量，準備列式", level=2)
    _assert_no_direct_answer_leak(h["hint"])

    # 3) Custom question_data: average division
    h = _next_hint(
        api_key,
        question_data={"topic": "分數應用題(五年級)", "question": "把 3/4 公升果汁平均倒入 6 杯，每杯多少公升？"},
        student_state="我想用 3/4 ÷ 6",
        level=2,
    )
    _assert_no_direct_answer_leak(h["hint"])

    # 4) reverse fraction (original value)
    h = _next_hint(
        api_key,
        question_data={"topic": "分數應用題(五年級)", "question": "小明花掉零用錢的 1/3，還剩 40 元，原來有多少元？"},
        student_state="我先算 1 - 1/3",
        level=3,
    )
    _assert_no_direct_answer_leak(h["hint"])

    # 5) remain then fraction
    h = _next_hint(
        api_key,
        question_data={"topic": "分數應用題(五年級)", "question": "一本書有 120 頁，先看了 1/4，剩下的又看了 3/5，還剩多少頁？"},
        student_state="先算第一次剩下", 
        level=2,
    )
    _assert_no_direct_answer_leak(h["hint"])

    # 6) fraction of fraction (portion of portion)
    h = _next_hint(
        api_key,
        question_data={"topic": "分數應用題(五年級)", "question": "一塊地的 2/3 用來種菜，其中的 3/4 種高麗菜。高麗菜占全地幾分之幾？"},
        student_state="我覺得要乘法",
        level=1,
    )
    _assert_no_direct_answer_leak(h["hint"])

    # 7) remaining after fraction
    h = _next_hint(
        api_key,
        question_data={"topic": "分數應用題(五年級)", "question": "一條繩子長 24 公尺，用了 5/8，剩下多少公尺？"},
        student_state="我先算 1 - 5/8", 
        level=2,
    )
    _assert_no_direct_answer_leak(h["hint"])

    # 8) fraction of quantity
    h = _next_hint(
        api_key,
        question_data={"topic": "分數應用題(五年級)", "question": "全程 60 公里，小明走了其中的 3/5，他走了多少公里？"},
        student_state="我想用 60 × 3/5", 
        level=2,
    )
    _assert_no_direct_answer_leak(h["hint"])

    # 9) generic fallback (non-matching)
    h = _next_hint(
        api_key,
        question_data={"topic": "分數", "question": "有 5/6 的同學參加活動，問參加的比例。"},
        student_state="", 
        level=1,
    )
    _assert_no_direct_answer_leak(h["hint"])
