from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow importing top-level modules like engine.py when running from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import engine
except Exception as e:  # pragma: no cover
    raise SystemExit(f"engine import failed: {e}")

try:
    from hint_overrides import HINT_OVERRIDES
except Exception as e:  # pragma: no cover
    raise SystemExit(f"hint_overrides import failed: {e}")


def _with_seed(seed: int):
    class _Seed:
        def __enter__(self):
            self._state = random.getstate()
            random.seed(int(seed))

        def __exit__(self, exc_type, exc, tb):
            random.setstate(self._state)
            return False

    return _Seed()


def _get_override_candidates(*, only_approved: bool) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for template_id, entry in (HINT_OVERRIDES or {}).items():
        if not isinstance(template_id, str) or not template_id.strip():
            continue
        if not isinstance(entry, dict):
            continue
        if only_approved and not entry.get("approved"):
            continue
        out[str(template_id)] = entry
    return out


def check_template(
    *,
    template_id: str,
    entry: Dict[str, Any],
    per_template: int,
    seed: int,
) -> List[str]:
    errors: List[str] = []

    l1 = str(entry.get("level1") or "").strip()
    l2 = str(entry.get("level2") or "").strip()
    l3 = str(entry.get("level3") or "").strip()

    if not (l1 and l2 and l3):
        errors.append("override fields missing: level1/level2/level3 must be non-empty")
        return errors

    # Generate a few questions and ensure:
    # - engine.get_question_hints returns the override
    # - Hint1 does not contain the exact final answer string
    for i in range(int(per_template)):
        item_seed = int(seed) + i
        with _with_seed(item_seed):
            q = engine.next_question(template_id)

        if not isinstance(q, dict):
            errors.append(f"seed={item_seed}: engine.next_question returned non-dict")
            continue

        ans = str(q.get("answer") or "").strip()
        hints = engine.get_question_hints(q)
        if not isinstance(hints, dict):
            errors.append(f"seed={item_seed}: get_question_hints returned non-dict")
            continue

        h1 = str(hints.get("level1") or "").strip()
        h2 = str(hints.get("level2") or "").strip()
        h3 = str(hints.get("level3") or "").strip()

        # Ensure override is actually applied.
        if h1 != l1 or h2 != l2 or h3 != l3:
            errors.append(f"seed={item_seed}: override not applied")

        if not (h1 and h2 and h3):
            errors.append(f"seed={item_seed}: blank hint levels")

        if ans and ans in h1:
            errors.append(f"seed={item_seed}: hint1 leaks answer")

    return errors


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Regression check for hint overrides: samples questions and ensures overrides apply "
            "and Hint1 does not leak the final answer."
        )
    )
    p.add_argument("--per_template", type=int, default=5)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--only_approved", action="store_true", default=True)
    p.add_argument("--include_unapproved", action="store_true", default=False)
    p.add_argument("--template_id", default=None)

    args = p.parse_args(argv)

    only_approved = bool(args.only_approved) and not bool(args.include_unapproved)
    candidates = _get_override_candidates(only_approved=only_approved)

    if args.template_id:
        tid = str(args.template_id)
        if tid not in candidates:
            print(f"ERROR: template_id not found in overrides (or not approved): {tid}")
            return 2
        candidates = {tid: candidates[tid]}

    if not candidates:
        print("OK: no overrides to check")
        return 0

    any_errors = False
    for tid, entry in sorted(candidates.items(), key=lambda x: x[0]):
        errs = check_template(template_id=tid, entry=entry, per_template=args.per_template, seed=args.seed)
        if errs:
            any_errors = True
            print(f"FAIL template_id={tid}:")
            for e in errs[:50]:
                print(f"- {e}")
        else:
            print(f"OK template_id={tid}")

    return 1 if any_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
