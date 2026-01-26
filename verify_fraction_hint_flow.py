# -*- coding: utf-8 -*-
from fastapi.testclient import TestClient
from server import app


client = TestClient(app)


def _bootstrap_get_api_key() -> str:
    # Uses admin bootstrap endpoint.
    r = client.post("/admin/bootstrap?name=HintTest")
    assert r.status_code == 200, r.text
    data = r.json()
    api_key = data.get("api_key")
    assert api_key
    return api_key


def test_fraction_hint_next_flow():
    api_key = _bootstrap_get_api_key()

    # create student
    r = client.post(
        "/v1/students?display_name=demo&grade=G5",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200, r.text

    # list students to get id
    r = client.get("/v1/students", headers={"X-API-Key": api_key})
    assert r.status_code == 200, r.text
    sid = r.json()["students"][0]["id"]

    # request a fraction word problem (topic_key 11)
    r = client.post(
        f"/v1/questions/next?student_id={sid}&topic_key=11",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200, r.text
    q = r.json()
    qid = q["question_id"]

    # request next-step hint with empty state
    r = client.post(
        "/v1/hints/next",
        headers={"X-API-Key": api_key},
        json={"question_id": qid, "student_state": "", "level": 1},
    )
    assert r.status_code == 200, r.text
    assert "hint" in r.json() and r.json()["hint"].strip()

    # request next-step hint with some partial work
    r = client.post(
        "/v1/hints/next",
        headers={"X-API-Key": api_key},
        json={"question_id": qid, "student_state": "我先算 1 - 1/3", "level": 2},
    )
    assert r.status_code == 200, r.text
    assert "hint" in r.json() and r.json()["hint"].strip()


if __name__ == "__main__":
    test_fraction_hint_next_flow()
    print("OK")
