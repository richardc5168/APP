#!/usr/bin/env python3
"""
build_exam_sprint_bank.py
─────────────────────────
Aggregate ALL elementary-school offline question banks into a single
exam-sprint bank.js.  Only questions that have hints + steps + explanation
are included.  Optionally filter to medium/hard difficulty only.

Usage:
    python tools/build_exam_sprint_bank.py          # medium+hard only (default)
    python tools/build_exam_sprint_bank.py --all     # include easy too
"""

import json, re, os, sys, pathlib

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
OUT  = DOCS / "exam-sprint" / "bank.js"

# Map: directory_name → (bank.js filename, JS variable name)
MODULES = {
    "fraction-g5":                       ("bank.js", "FRACTION_G5_BANK"),
    "fraction-word-g5":                  ("bank.js", "FRACTION_WORD_G5_BANK"),
    "decimal-unit4":                     ("bank.js", "DECIMAL_UNIT4_BANK"),
    "volume-g5":                         ("bank.js", "VOLUME_G5_BANK"),
    "ratio-percent-g5":                  ("bank.js", "RATIO_PERCENT_G5_BANK"),
    "life-applications-g5":              ("bank.js", "LIFE_APPLICATIONS_G5_BANK"),
    "g5-grand-slam":                     ("bank.js", "G5_GRAND_SLAM_BANK"),
    "offline-math":                      ("bank.js", "OFFLINE_MATH_BANK"),
    "interactive-decimal-g5":            ("bank.js", "INTERACTIVE_DECIMAL_G5_BANK"),
    "interactive-g5-empire":             ("bank.js", "INTERACTIVE_G5_EMPIRE_BANK"),
    "interactive-g5-life-pack1-empire":  ("bank.js", "G5_LIFE_PACK1_BANK"),
    "interactive-g5-life-pack1plus-empire": ("bank.js", "G5_LIFE_PACK1PLUS_BANK"),
    "interactive-g5-life-pack2-empire":  ("bank.js", "G5_LIFE_PACK2_BANK"),
    "interactive-g5-life-pack2plus-empire": ("bank.js", "G5_LIFE_PACK2PLUS_BANK"),
    "interactive-g56-core-foundation":   ("g56_core_foundation.json", None),
}

def parse_bank_js(path: pathlib.Path, var_name: str | None):
    """Extract JSON array from bank.js (window.VAR = [...];) or .json"""
    text = path.read_text(encoding="utf-8")

    if path.suffix == ".json":
        return json.loads(text)

    # Find "window.XXXX = [" and then grab everything from [ to the matching ]
    # There may be multiple matches (e.g. comment "[...]" then actual data);
    # iterate all matches and return the first one that parses as valid JSON.
    for m in re.finditer(r"window\.\w+\s*=\s*\[", text):
        start = m.end() - 1  # position of opening [
        # Use bracket counting to find matching ]
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == '[':
                depth += 1
            elif text[i] == ']':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        array_str = text[start:end]
        if len(array_str) < 10:  # skip placeholder like "[...]"
            continue
        try:
            result = json.loads(array_str)
            if isinstance(result, list) and len(result) > 0:
                return result
        except json.JSONDecodeError:
            continue

    print(f"  WARN: no valid JSON array found in {path}")
    return []


def _strip_answer_from_hint(hint_text: str, answer_str: str) -> str:
    """Remove patterns like '答案：X' / '答案是 X' from hint text."""
    if not answer_str or len(answer_str) > 30:
        return hint_text
    ans_esc = re.escape(answer_str.strip())
    # Pattern: 答案：X / 答案是X / 答案為X (possibly at end of string)
    cleaned = re.sub(
        r"[，,。；\s]*答案[：:是為]\s*" + ans_esc + r"[。\.\s]*$",
        "。", hint_text, flags=re.MULTILINE
    )
    # Also strip isolated "= answer" at very end
    cleaned = re.sub(
        r"[，,。\s]*=\s*" + ans_esc + r"[。\.\s]*$",
        "。", cleaned, flags=re.MULTILINE
    )
    return cleaned.strip()


def _simplify_fraction_over_1(answer_str: str) -> str:
    """Convert answers like '3/1' → '3', '0/1' → '0'."""
    m = re.match(r"^(-?\d+)\s*/\s*1$", answer_str.strip())
    if m:
        return m.group(1)
    return answer_str


def normalize_question(q: dict, source_module: str) -> dict | None:
    """Normalize a question into exam-sprint schema.  Returns None if invalid."""

    # Must have question text + answer
    qtext = q.get("question") or q.get("stem") or q.get("prompt") or ""
    answer = q.get("answer")
    if not qtext or answer is None:
        return None
    answer = str(answer).strip()

    # ── Fix Q11: simplify N/1 fractions ──
    answer = _simplify_fraction_over_1(answer)

    # Must have hints (at least 1)
    hints = q.get("hints", [])
    if not isinstance(hints, list) or len(hints) == 0:
        return None

    # Pad hints to exactly 3 if only 1 or 2
    while len(hints) < 3:
        hints.append(hints[-1])
    hints = hints[:4]  # allow up to 4 hints

    # ── Fix Q10: strip answer leaks from hints ──
    hints = [_strip_answer_from_hint(str(h), answer) for h in hints]

    # Steps and explanation
    steps = q.get("steps") or q.get("teacherSteps") or []
    explanation = q.get("explanation") or ""

    # ── Fix Q4+Q5: generate steps/explanation from hints if missing ──
    if not steps:
        if hints:
            steps = [f"步驟 {i+1}：{str(hints[i])[:60]}" for i in range(min(3, len(hints)))]
        elif explanation:
            steps = [f"步驟 {i+1}" for i in range(3)]
    if not explanation and hints:
        explanation = " → ".join(str(h)[:80] for h in hints[:3])

    # Difficulty normalization
    diff = str(q.get("difficulty", "medium")).lower()
    if diff not in ("easy", "medium", "hard"):
        diff = "medium"

    # Build uniform ID
    orig_id = q.get("id", "")
    eid = f"exam_{source_module}__{orig_id}" if orig_id else f"exam_{source_module}__anon"

    out = {
        "id": eid,
        "topic": q.get("topic") or q.get("block") or source_module,
        "kind": q.get("kind") or q.get("subskill") or "general",
        "difficulty": diff,
        "question": qtext.strip(),
        "answer": answer,
        "answer_unit": q.get("answer_unit") or q.get("answer_mode") or "number",
        "hints": hints,
        "steps": steps if isinstance(steps, list) else [steps],
        "explanation": str(explanation).strip(),
        "meta": {
            "source_module": source_module,
            "source_id": orig_id,
        }
    }

    # Carry over any extra meta from original
    if isinstance(q.get("meta"), dict):
        for k, v in q["meta"].items():
            if k not in out["meta"]:
                out["meta"][k] = v

    return out


def main():
    include_easy = "--all" in sys.argv

    all_questions = []
    seen_ids = set()
    stats = {}

    for module_dir, (filename, var_name) in sorted(MODULES.items()):
        path = DOCS / module_dir / filename
        if not path.exists():
            print(f"  SKIP: {path} (not found)")
            continue

        questions = parse_bank_js(path, var_name)
        count_before = len(questions)
        added = 0

        for q in questions:
            nq = normalize_question(q, module_dir)
            if nq is None:
                continue

            # Difficulty filter
            if not include_easy and nq["difficulty"] == "easy":
                continue

            # Dedup by question text (some modules share questions)
            dedup_key = nq["question"].strip()[:120]
            if dedup_key in seen_ids:
                continue
            seen_ids.add(dedup_key)

            all_questions.append(nq)
            added += 1

        stats[module_dir] = {"total": count_before, "added": added}
        print(f"  {module_dir}: {count_before} total → {added} added")

    # Sort by difficulty (hard first), then by topic
    diff_order = {"hard": 0, "medium": 1, "easy": 2}
    all_questions.sort(key=lambda q: (diff_order.get(q["difficulty"], 1), q["topic"], q["kind"]))

    # Write bank.js
    js_array = json.dumps(all_questions, ensure_ascii=False, indent=2)
    js_content = f"/* Auto-generated exam-sprint bank — {len(all_questions)} questions from {len(stats)} modules. */\nwindow.EXAM_SPRINT_BANK = {js_array};\n"

    OUT.write_text(js_content, encoding="utf-8")
    print(f"\n✅ Wrote {OUT} — {len(all_questions)} questions")

    # Summary
    print("\n── Module Summary ──")
    for mod, s in sorted(stats.items()):
        print(f"  {mod:45s}  total={s['total']:4d}  added={s['added']:4d}")
    print(f"  {'TOTAL':45s}  {' ':10s}  added={len(all_questions)}")


if __name__ == "__main__":
    main()
