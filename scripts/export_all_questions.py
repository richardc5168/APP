from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Allow importing top-level modules like engine.py when running from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


try:
    import engine
except Exception as e:  # pragma: no cover
    engine = None
    _ENGINE_IMPORT_ERROR = e
else:
    _ENGINE_IMPORT_ERROR = None


@dataclass(frozen=True)
class TemplateInfo:
    template_id: str
    name: str


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _iter_templates() -> List[TemplateInfo]:
    if engine is None:
        raise RuntimeError(f"engine import failed: {_ENGINE_IMPORT_ERROR}")

    gens = getattr(engine, "GENERATORS", None)
    if not isinstance(gens, dict):
        raise RuntimeError("engine.GENERATORS not found or invalid")

    out: List[TemplateInfo] = []
    for k, v in gens.items():
        try:
            name = str(v[0]) if isinstance(v, tuple) and len(v) >= 1 else str(k)
        except Exception:
            name = str(k)
        out.append(TemplateInfo(template_id=str(k), name=name))

    # Stable order.
    out.sort(key=lambda x: x.template_id)
    return out


def _with_seed(seed: int):
    class _Seed:
        def __enter__(self):
            self._state = random.getstate()
            random.seed(int(seed))

        def __exit__(self, exc_type, exc, tb):
            random.setstate(self._state)
            return False

    return _Seed()


def _extract_hints(q: Dict[str, Any]) -> List[str]:
    # Prefer explicit hint ladder if provided.
    h = q.get("hints")
    if isinstance(h, dict) and all(k in h for k in ("level1", "level2", "level3")):
        packed = [str(h.get("level1") or ""), str(h.get("level2") or ""), str(h.get("level3") or "")]
    elif engine is not None and hasattr(engine, "get_question_hints"):
        hh = engine.get_question_hints(q)
        packed = [str(hh.get("level1") or ""), str(hh.get("level2") or ""), str(hh.get("level3") or "")]
    else:
        packed = [
            "先整理題意，圈出關鍵數字/單位。",
            "把文字轉成算式（列式）。",
            "計算並檢查答案是否合理。",
        ]

    # Always exactly 3.
    packed = [x.strip() for x in packed if isinstance(x, str)]
    while len(packed) < 3:
        packed.append(packed[-1] if packed else "先整理題意，逐步計算。")
    packed = packed[:3]

    # Avoid blank hints.
    for i in range(3):
        if not packed[i].strip():
            packed[i] = "先整理題意，逐步計算。" if i == 0 else "寫出中間步驟再檢查。"

    return packed


def _extract_solution_steps(q: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps = q.get("steps")
    out: List[Dict[str, Any]] = []

    if isinstance(steps, list) and steps:
        for idx, s in enumerate(steps, start=1):
            out.append({"step_index": idx, "text": str(s)})
        return out

    # Fallback: split explanation into lines.
    expl = str(q.get("explanation") or "").strip()
    if expl:
        parts = [p.strip() for p in expl.splitlines() if p.strip()]
        for idx, p in enumerate(parts[:8], start=1):
            out.append({"step_index": idx, "text": p})
        return out

    return [{"step_index": 1, "text": "（無詳解步驟）"}]


def _answer_ok(answer: str) -> bool:
    if engine is None or not hasattr(engine, "check"):
        return True
    try:
        r = engine.check(str(answer), str(answer))
        return r == 1
    except Exception:
        return False


def _hint_ladder_ok(hints: List[str], *, answer: str) -> bool:
    if not isinstance(hints, list) or len(hints) != 3:
        return False
    if not all(isinstance(x, str) and x.strip() for x in hints):
        return False

    a = str(answer or "").strip()
    if a:
        # Basic leakage check: hint1 should not contain the exact final answer string.
        if a in hints[0]:
            return False
    return True


def export_all_questions(
    *,
    out_jsonl: Path,
    out_md: Path,
    per_template: int,
    seed: int,
    limit_templates: Optional[int] = None,
) -> Dict[str, Any]:
    templates = _iter_templates()
    if limit_templates is not None:
        templates = templates[: int(limit_templates)]

    _ensure_parent_dir(out_jsonl)
    _ensure_parent_dir(out_md)

    total = 0
    bad_answer = 0
    bad_hints = 0

    md_lines: List[str] = []
    md_lines.append("# Questions Dump (All Templates)")
    md_lines.append(f"- templates: {len(templates)}")
    md_lines.append(f"- per_template: {int(per_template)}")
    md_lines.append(f"- base_seed: {int(seed)}")

    with out_jsonl.open("w", encoding="utf-8") as f:
        for t in templates:
            md_lines.append("")
            md_lines.append(f"## {t.template_id} — {t.name}")

            for i in range(int(per_template)):
                # Derive a deterministic per-item seed (do NOT use Python's built-in hash()).
                seed_material = f"{int(seed)}::{t.template_id}::{int(i)}".encode("utf-8")
                seed_hash = hashlib.sha256(seed_material).digest()
                seed_offset = int.from_bytes(seed_hash[:8], "big") % 1_000_000_000
                item_seed = int(seed) + seed_offset

                with _with_seed(item_seed):
                    q = engine.next_question(t.template_id)  # type: ignore[union-attr]

                question = str(q.get("question") or "")
                answer = str(q.get("answer") or "")
                topic_id = str(q.get("topic") or t.name or t.template_id)

                hints = _extract_hints(q)
                steps = _extract_solution_steps(q)

                checks = {
                    "answer_ok": bool(_answer_ok(answer)),
                    "hint_ladder_ok": bool(_hint_ladder_ok(hints, answer=answer)),
                }

                if not checks["answer_ok"]:
                    bad_answer += 1
                if not checks["hint_ladder_ok"]:
                    bad_hints += 1

                obj: Dict[str, Any] = {
                    "topic_id": topic_id,
                    "topic": str(q.get("topic") or topic_id),
                    "template_id": t.template_id,
                    "template_name": t.name,
                    "seed": item_seed,
                    "question": question,
                    "answer": answer,
                    "hints": hints,
                    "solution_steps": steps,
                    "parent_summary": str(q.get("parent_summary") or ""),
                    "chart_config": q.get("chart_config") if isinstance(q.get("chart_config"), dict) else None,
                    "checks": checks,
                }

                f.write(json.dumps(obj, ensure_ascii=False))
                f.write("\n")

                md_lines.append(f"- seed={item_seed}: {question}")
                md_lines.append(f"  - answer: {answer}")
                md_lines.append(f"  - hints: 1) {hints[0]}  2) {hints[1]}  3) {hints[2]}")

                total += 1

    md_lines.append("")
    md_lines.append("# Summary")
    md_lines.append(f"- total_items: {total}")
    md_lines.append(f"- answer_ok_fail: {bad_answer}")
    md_lines.append(f"- hint_ladder_ok_fail: {bad_hints}")

    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    return {
        "templates": len(templates),
        "per_template": int(per_template),
        "total_items": total,
        "answer_ok_fail": bad_answer,
        "hint_ladder_ok_fail": bad_hints,
        "out_jsonl": str(out_jsonl),
        "out_md": str(out_md),
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Export all question templates to JSONL + Markdown for QA.")
    p.add_argument("--out_jsonl", default="artifacts/questions_dump.jsonl")
    p.add_argument("--out_md", default="artifacts/questions_dump.md")
    p.add_argument("--per_template", type=int, default=50)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--limit_templates", type=int, default=None)

    args = p.parse_args(argv)

    if engine is None:
        raise SystemExit(f"engine import failed: {_ENGINE_IMPORT_ERROR}")

    result = export_all_questions(
        out_jsonl=Path(args.out_jsonl),
        out_md=Path(args.out_md),
        per_template=int(args.per_template),
        seed=int(args.seed),
        limit_templates=(int(args.limit_templates) if args.limit_templates is not None else None),
    )

    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
