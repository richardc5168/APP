from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fraction_word_g5 import generate_fraction_word_problem_g5
from scripts.check_fraction_word_g5_bank_logic import _is_ambiguous_wording, load_bank_items


def _build_hints_from_steps(steps: list[str], answer: str) -> list[str]:
    s1 = steps[1] if len(steps) > 1 else (steps[0] if steps else "先圈出已知與未知。")
    s2 = steps[2] if len(steps) > 2 else (steps[1] if len(steps) > 1 else "先列式再計算。")
    full = "\n".join([f"Step {i+1}：{s}" for i, s in enumerate(steps)])
    return [
        f"觀念引導：{s1}",
        f"列式引導：{s2}",
        f"完整解題步驟：\n{full}\n答案：{answer}",
    ]


def _extract_var_name(js_text: str) -> str:
    m = re.search(r"window\.([A-Za-z0-9_]+)\s*=\s*\[", js_text)
    return m.group(1) if m else "FRACTION_WORD_G5_BANK"


def _repair_items(items: list[dict[str, Any]], seed: int = 20260218) -> tuple[list[dict[str, Any]], int]:
    random.seed(seed)
    fixed = 0
    out: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict):
            continue
        q = str(item.get("question") or "")
        if not _is_ambiguous_wording(q):
            out.append(item)
            continue

        replacement: dict[str, Any] | None = None
        for _ in range(80):
            cand = generate_fraction_word_problem_g5()
            q2 = str(cand.get("question") or "")
            if not _is_ambiguous_wording(q2):
                replacement = cand
                break
        if replacement is None:
            out.append(item)
            continue

        rid = str(item.get("id") or replacement.get("id") or "")
        answer = str(replacement.get("answer") or "")
        steps = list(replacement.get("steps") or [])
        if not steps:
            steps = ["先圈出已知與未知。", "列式並計算。", "檢查答案合理性。"]

        patched = {
            "id": rid,
            "kind": str(replacement.get("kind") or item.get("kind") or "generic_fraction_word"),
            "topic": str(replacement.get("topic") or item.get("topic") or "分數應用題(五年級)"),
            "difficulty": str(replacement.get("difficulty") or item.get("difficulty") or "medium"),
            "question": str(replacement.get("question") or ""),
            "answer": answer,
            "steps": steps,
            "explanation": str(replacement.get("explanation") or "\n".join([f"步驟 {i+1}：{s}" for i, s in enumerate(steps)])),
            "hints": list(replacement.get("hints") or _build_hints_from_steps(steps, answer)),
        }
        out.append(patched)
        fixed += 1

    return out, fixed


def _rewrite_bank(path: Path) -> int:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    var_name = _extract_var_name(raw)
    items = load_bank_items(path)
    repaired, fixed = _repair_items(items)
    payload = json.dumps(repaired, ensure_ascii=False, indent=2)
    out = f"/* Auto-generated offline question bank. */\nwindow.{var_name} = {payload};\n"
    path.write_text(out, encoding="utf-8")
    return fixed


def main() -> int:
    paths = [
        ROOT / "docs" / "fraction-word-g5" / "bank.js",
        ROOT / "dist_ai_math_web_pages" / "docs" / "fraction-word-g5" / "bank.js",
    ]

    total = 0
    for p in paths:
        fixed = _rewrite_bank(p)
        total += fixed
        print(f"OK: repaired {fixed} invalid items in {p.as_posix()}")
    print(f"OK: total repaired items = {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
