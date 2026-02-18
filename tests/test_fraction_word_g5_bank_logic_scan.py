from __future__ import annotations

from pathlib import Path

from scripts.check_fraction_word_g5_bank_logic import check_bank_items, load_bank_items


def test_check_bank_items_flags_illogical_entries():
    items = [
        {"id": "ok_1", "question": "一本書有 120 頁，先看了 1/4，剩下的又看了 3/5，還剩多少頁？"},
        {"id": "bad_1", "question": "一本書有 120 頁，先看了 1/4，剩下的又看了 1，還剩多少頁？"},
        {"id": "bad_2", "question": "一桶油用了 3/2，還剩多少公斤？"},
        {"id": "bad_3", "question": "一桶油用了 1/4，還剩 4/3 公斤，原來有多少公斤？"},
    ]

    violations = check_bank_items(items)
    ids = {v["id"] for v in violations}
    assert "ok_1" not in ids
    assert {"bad_1", "bad_2", "bad_3"}.issubset(ids)


def test_real_banks_pass_logic_scan():
    root = Path(__file__).resolve().parents[1]
    docs_bank = root / "docs" / "fraction-word-g5" / "bank.js"
    dist_bank = root / "dist_ai_math_web_pages" / "docs" / "fraction-word-g5" / "bank.js"

    assert docs_bank.exists(), f"Missing {docs_bank}"
    assert dist_bank.exists(), f"Missing {dist_bank}"

    docs_items = load_bank_items(docs_bank)
    dist_items = load_bank_items(dist_bank)

    assert not check_bank_items(docs_items)
    assert not check_bank_items(dist_items)
