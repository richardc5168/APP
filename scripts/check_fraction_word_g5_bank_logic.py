from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fraction_word_g5 import _is_ambiguous_wording


def load_bank_items(bank_js_path: Path) -> list[dict[str, Any]]:
    text = bank_js_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"window\.FRACTION_WORD_G5_BANK\s*=\s*(\[.*\])\s*;", text, flags=re.DOTALL)
    if not m:
        raise ValueError(f"Cannot parse FRACTION_WORD_G5_BANK from: {bank_js_path}")
    arr = json.loads(m.group(1))
    if not isinstance(arr, list):
        raise ValueError(f"Bank payload is not an array: {bank_js_path}")
    out: list[dict[str, Any]] = []
    for item in arr:
        if isinstance(item, dict):
            out.append(item)
    return out


def check_bank_items(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for idx, item in enumerate(items):
        qid = str(item.get("id") or f"idx_{idx}")
        qtext = str(item.get("question") or "")
        if _is_ambiguous_wording(qtext):
            violations.append(
                {
                    "id": qid,
                    "question": qtext,
                    "reason": "ambiguous_or_illogical_fraction_wording",
                }
            )
    return violations


def run_check(bank_js_path: Path) -> tuple[bool, str]:
    items = load_bank_items(bank_js_path)
    violations = check_bank_items(items)
    if not violations:
        return True, f"OK: {bank_js_path.as_posix()} logic scan passed ({len(items)} items)"

    preview = " | ".join(
        f"{v['id']}: {v['reason']} -> {v['question']}" for v in violations[:5]
    )
    more = "" if len(violations) <= 5 else f" | ... and {len(violations)-5} more"
    return (
        False,
        f"NOT OK: {bank_js_path.as_posix()} logic scan failed ({len(violations)} violations) | {preview}{more}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fraction-word-g5 bank question logic constraints.")
    parser.add_argument(
        "--file",
        default="docs/fraction-word-g5/bank.js",
        help="Path to bank.js file (default: docs/fraction-word-g5/bank.js)",
    )
    args = parser.parse_args()

    ok, msg = run_check(Path(args.file))
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
