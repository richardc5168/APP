from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIST_DOCS = ROOT / "dist_ai_math_web_pages" / "docs"

OUT_JS = DOCS / "exam-sprint" / "bank.js"
OUT_JS_DIST = DIST_DOCS / "exam-sprint" / "bank.js"

WINDOW_VAR = "EXAM_SPRINT_BANK"


SOURCE_BANKS: List[Tuple[str, Path]] = [
    ("g5-grand-slam", DOCS / "g5-grand-slam" / "bank.js"),
    ("ratio-percent-g5", DOCS / "ratio-percent-g5" / "bank.js"),
    ("volume-g5", DOCS / "volume-g5" / "bank.js"),
    ("fraction-word-g5", DOCS / "fraction-word-g5" / "bank.js"),
    ("fraction-g5", DOCS / "fraction-g5" / "bank.js"),
    ("decimal-unit4", DOCS / "decimal-unit4" / "bank.js"),
    ("life-applications-g5", DOCS / "life-applications-g5" / "bank.js"),
    ("interactive-decimal-g5", DOCS / "interactive-decimal-g5" / "bank.js"),
    ("interactive-g5-empire", DOCS / "interactive-g5-empire" / "bank.js"),
    ("interactive-g5-life-pack1-empire", DOCS / "interactive-g5-life-pack1-empire" / "bank.js"),
    ("interactive-g5-life-pack1plus-empire", DOCS / "interactive-g5-life-pack1plus-empire" / "bank.js"),
    ("interactive-g5-life-pack2-empire", DOCS / "interactive-g5-life-pack2-empire" / "bank.js"),
    ("interactive-g5-life-pack2plus-empire", DOCS / "interactive-g5-life-pack2plus-empire" / "bank.js"),
]


ADV_KEYWORDS = (
    "至少",
    "最多",
    "剛好",
    "剩下",
    "其餘",
    "平均",
    "比較",
    "差",
    "比率",
    "百分率",
    "折",
    "打折",
    "原來",
    "如果",
    "需要",
    "共",
    "每",
    "分成",
    "三步",
)


def _extract_json_array_from_bank_js(text: str) -> List[Dict[str, Any]]:
    s = str(text)

    # Many banks include comments like: // window.X = [...]
    # So we must locate the real assignment and then extract the matching array.
    m = re.search(
        r"^[ \t]*(?!//)window\.[A-Za-z0-9_]+\s*=\s*\[",
        s,
        flags=re.MULTILINE,
    )
    if not m:
        raise ValueError("bank.js missing 'window.<VAR> = [' assignment")

    start = m.end() - 1  # points to '['
    depth = 0
    in_str: str | None = None
    esc = False

    for pos in range(start, len(s)):
        ch = s[pos]

        if in_str is not None:
            if esc:
                esc = False
                continue
            if ch == "\\":
                esc = True
                continue
            if ch == in_str:
                in_str = None
            continue

        if ch in ('"', "'", "`"):
            in_str = ch
            continue
        if ch == "[":
            depth += 1
            continue
        if ch == "]":
            depth -= 1
            if depth == 0:
                raw = s[start : pos + 1]
                return json.loads(raw)

    raise ValueError("bank.js missing matching closing ']' for array")


def _load_bank(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    return _extract_json_array_from_bank_js(path.read_text(encoding="utf-8"))


def _difficulty_rank(diff: str) -> int:
    d = str(diff or "").lower().strip()
    if d == "hard":
        return 3
    if d == "advanced":
        return 3
    if d == "medium":
        return 2
    if d == "normal":
        return 2
    if d == "easy":
        return 1
    return 0


def _is_advanced_item(q: Dict[str, Any], source_id: str) -> bool:
    diff = str(q.get("difficulty") or "").lower().strip()
    if diff in ("hard", "advanced"):
        return True

    # Some modules are application-heavy even at "medium".
    if diff == "medium" and source_id in (
        "fraction-word-g5",
        "life-applications-g5",
        "ratio-percent-g5",
        "volume-g5",
        "interactive-g56-core-foundation",
    ):
        qt = str(q.get("question") or "")
        if len(qt) >= 24:
            return True
        if any(k in qt for k in ADV_KEYWORDS):
            return True

    return False


def _normalize_item(q: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    # Keep schema compatible with existing offline pages.
    out: Dict[str, Any] = {}
    out["id"] = f"exam_{source_id}__{q.get('id') or q.get('qid') or ''}".strip('_')

    # Prefer existing topic/kind; fall back to source label.
    out["topic"] = q.get("topic") or source_id
    out["kind"] = q.get("kind") or "mixed"
    diff = q.get("difficulty") or "medium"
    if str(diff).lower().strip() == "normal":
        diff = "medium"
    out["difficulty"] = diff

    out["question"] = q.get("question") or ""
    out["answer"] = q.get("answer")

    # Preserve answer type fields if present.
    # Normalize answer type field across banks.
    if "answer_unit" in q and q.get("answer_unit"):
        out["answer_unit"] = q.get("answer_unit")
    elif "answer_mode" in q and q.get("answer_mode"):
        out["answer_unit"] = q.get("answer_mode")

    out["hints"] = q.get("hints") or []
    out["steps"] = q.get("steps") or []
    out["explanation"] = q.get("explanation") or ""

    meta = dict(q.get("meta") or {})
    meta["source_module"] = source_id
    meta["source_id"] = q.get("id") or q.get("qid")
    out["meta"] = meta

    return out


def _is_valid_item(q: Dict[str, Any]) -> bool:
    if not q.get("question"):
        return False
    if q.get("answer") is None:
        return False
    hints = q.get("hints")
    if not isinstance(hints, list) or len(hints) < 3:
        return False
    if not str(q.get("explanation") or "").strip():
        return False
    return True


def build_exam_sprint_bank(max_items: int = 240, seed: int = 20260209) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for source_id, path in SOURCE_BANKS:
        for q in _load_bank(path):
            if not isinstance(q, dict):
                continue
            if not _is_advanced_item(q, source_id):
                continue
            item = _normalize_item(q, source_id)
            if not _is_valid_item(item):
                continue
            rows.append(item)

    # De-dup by (topic, question)
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for it in rows:
        key = (str(it.get("topic") or ""), str(it.get("question") or ""))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)

    # Sort by difficulty desc then stable fields.
    uniq.sort(
        key=lambda x: (
            -_difficulty_rank(str(x.get("difficulty"))),
            str(x.get("topic") or ""),
            str(x.get("kind") or ""),
            str(x.get("id") or ""),
        )
    )

    # Light shuffle within each difficulty bucket so it's not too repetitive but still deterministic.
    rng = random.Random(int(seed))
    buckets: Dict[int, List[Dict[str, Any]]] = {3: [], 2: [], 1: [], 0: []}
    for it in uniq:
        buckets[_difficulty_rank(str(it.get("difficulty")))].append(it)
    for k in buckets:
        rng.shuffle(buckets[k])

    ordered = buckets[3] + buckets[2] + buckets[1] + buckets[0]
    return ordered[: int(max_items)]


def write_bank_js(items: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(items, ensure_ascii=False, indent=2)
    out_path.write_text(
        f"/* Auto-generated offline question bank. */\nwindow.{WINDOW_VAR} = {payload};\n",
        encoding="utf-8",
    )


def main() -> int:
    items = build_exam_sprint_bank()
    write_bank_js(items, OUT_JS)
    write_bank_js(items, OUT_JS_DIST)

    hard = sum(1 for x in items if str(x.get("difficulty")).lower() in ("hard", "advanced"))
    medium = sum(1 for x in items if str(x.get("difficulty")).lower() == "medium")
    print(f"Wrote {len(items)} items: hard={hard} medium={medium}")
    print(f"- {OUT_JS}")
    print(f"- {OUT_JS_DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
