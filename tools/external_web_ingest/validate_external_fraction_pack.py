from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TYPE_KEY = "external_web_fraction_app_v1"


def _die(message: str) -> None:
    raise SystemExit(message)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        _die(f"Missing pack: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_fraction(value: str) -> bool:
    return bool(re.fullmatch(r"-?\d+\s*/\s*-?\d+", value.strip()))


def _hint_leaks_answer(hints: dict[str, Any], answer: str) -> bool:
    ans = "".join(str(answer or "").split()).lower()
    if not ans:
        return False
    for level in ("level1", "level2", "level3"):
        text = "".join(str(hints.get(level) or "").split()).lower()
        if ans in text:
            return True
    return False


def _ladder_valid(ladder: dict[str, Any], answer: str) -> bool:
    ans = "".join(str(answer or "").split()).lower()
    required = ("h1_strategy", "h2_equation", "h3_compute", "h4_check_reflect")
    for key in required:
        text = str(ladder.get(key) or "").strip()
        if not text:
            return False
        if key in ("h1_strategy", "h4_check_reflect") and ans and ans in "".join(text.split()).lower():
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", default="data/external_web_fraction_app_v1_pack.json")
    args = parser.parse_args(argv)

    pack = _load_json(Path(args.pack))
    if pack.get("type_key") != TYPE_KEY:
        _die("pack.type_key mismatch")

    items = pack.get("items")
    if not isinstance(items, list) or not items:
        _die("pack.items must be non-empty list")

    seen_ids: set[str] = set()
    seen_questions: set[str] = set()
    category_seen: set[str] = set()

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            _die(f"item#{index} must be object")

        item_id = str(item.get("id") or "").strip()
        if not item_id:
            _die(f"item#{index} missing id")
        if item_id in seen_ids:
            _die(f"duplicate id: {item_id}")
        seen_ids.add(item_id)

        if str(item.get("type_key") or "") != TYPE_KEY:
            _die(f"item#{index} type_key mismatch")

        category = str(item.get("category") or "").strip()
        if category not in ("shopping_discount", "average_distribution", "unit_conversion", "distance_time"):
            _die(f"item#{index} invalid category={category}")
        category_seen.add(category)

        question = str(item.get("question") or "").strip()
        if not question:
            _die(f"item#{index} missing question")
        if question in seen_questions:
            _die(f"duplicate question: {question}")
        seen_questions.add(question)

        answer = str(item.get("answer") or "").strip()
        if not answer:
            _die(f"item#{index} missing answer")

        hints = item.get("hints")
        if not isinstance(hints, dict):
            _die(f"item#{index} hints must be object")
        for level in ("level1", "level2", "level3"):
            if not str(hints.get(level) or "").strip():
                _die(f"item#{index} missing {level}")
        if _hint_leaks_answer(hints, answer):
            _die(f"item#{index} hints leak final answer")

        ladder = item.get("hint_ladder")
        if not isinstance(ladder, dict):
            _die(f"item#{index} hint_ladder must be object")
        if not _ladder_valid(ladder, answer):
            _die(f"item#{index} invalid hint_ladder")

        steps = item.get("steps")
        if not isinstance(steps, list) or not steps:
            _die(f"item#{index} steps must be non-empty list")

        diagnostics = item.get("error_diagnostics")
        if not isinstance(diagnostics, list) or len(diagnostics) < 5:
            _die(f"item#{index} error_diagnostics must include at least 5 entries")

        validator = item.get("validator")
        if not isinstance(validator, dict):
            _die(f"item#{index} validator must be object")
        vtype = str(validator.get("type") or "").strip()
        if vtype not in ("number", "fraction", "text"):
            _die(f"item#{index} unsupported validator.type={vtype}")

        if vtype == "number":
            try:
                float(answer)
            except Exception:
                _die(f"item#{index} answer is not parseable number")
        if vtype == "fraction" and not _is_fraction(answer):
            _die(f"item#{index} answer is not parseable fraction")

        evidence = item.get("evidence")
        if not isinstance(evidence, dict):
            _die(f"item#{index} evidence must be object")
        if not str(evidence.get("source_url") or "").strip():
            _die(f"item#{index} evidence.source_url required")
        quoted_fact = str(evidence.get("quoted_fact") or "")
        if len(quoted_fact) > 25:
            _die(f"item#{index} evidence.quoted_fact too long")

    required_categories = {"shopping_discount", "average_distribution", "unit_conversion", "distance_time"}
    if not required_categories.issubset(category_seen):
        _die("pack missing required categories")

    print(f"OK: items={len(items)} unique_questions={len(seen_questions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
