import json
from pathlib import Path


NOTES_PATH = Path("data/external_web_notes/external_web_fraction_app_notes.jsonl")
PACK_PATH = Path("data/external_web_fraction_app_v1_pack.json")


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        rows.append(json.loads(raw))
    return rows


def test_external_notes_contract():
    notes = _read_jsonl(NOTES_PATH)
    assert len(notes) >= 10

    for note in notes:
        assert str(note.get("source_url") or "")
        assert str(note.get("title") or "")
        assert str(note.get("retrieved_at") or "")
        assert str(note.get("grade") or "") in ("5", "6")
        tags = note.get("topic_tags") or []
        assert isinstance(tags, list) and len(tags) >= 1
        assert str(note.get("summary") or "")
        key_steps = note.get("key_steps") or []
        assert isinstance(key_steps, list) and len(key_steps) >= 3
        mistakes = note.get("common_mistakes") or []
        assert isinstance(mistakes, list) and len(mistakes) >= 5
        patterns = note.get("example_patterns") or []
        assert isinstance(patterns, list) and len(patterns) >= 4

        quotes = note.get("quotes") or []
        if quotes:
            q = quotes[0]
            assert len(str(q.get("text") or "")) <= 25
            assert str(q.get("citation") or "")


def test_external_pack_contract():
    data = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    items = data.get("items") or []
    assert data.get("type_key") == "external_web_fraction_app_v1"
    assert len(items) >= 30

    categories = set()
    for item in items:
        categories.add(str(item.get("category") or ""))
        assert str(item.get("question") or "")
        assert str(item.get("answer") or "")
        ladder = item.get("hint_ladder") or {}
        assert str(ladder.get("h1_strategy") or "")
        assert str(ladder.get("h2_equation") or "")
        assert str(ladder.get("h3_compute") or "")
        assert str(ladder.get("h4_check_reflect") or "")

        diagnostics = item.get("error_diagnostics") or []
        assert isinstance(diagnostics, list) and len(diagnostics) >= 5

    assert {"shopping_discount", "average_distribution", "unit_conversion", "distance_time"}.issubset(categories)
