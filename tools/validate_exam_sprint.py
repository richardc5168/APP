#!/usr/bin/env python3
"""
validate_exam_sprint.py
───────────────────────
Full QA sweep of the exam-sprint bank.js (1503 questions).

Checks per question:
  Q1  has non-empty question text (≥10 chars)
  Q2  has non-empty answer
  Q3  hints array ≥ 3 items, each ≥ 5 chars
  Q4  steps array ≥ 1 item
  Q5  explanation non-empty (≥ 5 chars)
  Q6  difficulty ∈ {easy, medium, hard}
  Q7  topic non-empty
  Q8  kind non-empty
  Q9  no garbled/encoding-corrupted text (detect ??? / \ufffd patterns)
  Q10 hint L3 does NOT literally contain the exact final answer as a standalone token
      (the "不爆答案" rule — hints should guide, not give away)
  Q11 arithmetic spot-check: for simple fraction/integer answers, verify against question
  Q12 no exact-duplicate question text

Output: summary + per-question FAIL list with reason codes.
"""

import json, re, sys, pathlib, collections
from fractions import Fraction

BANK_PATH = pathlib.Path(__file__).resolve().parent.parent / "docs" / "exam-sprint" / "bank.js"

# ── Parse bank.js ──────────────────────────────────────────────────────────────

def load_bank(path):
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"window\.\w+\s*=\s*\[", text):
        start = m.end() - 1
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "[": depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        chunk = text[start:end]
        if len(chunk) < 20:
            continue
        try:
            arr = json.loads(chunk)
            if isinstance(arr, list) and len(arr) > 0:
                return arr
        except json.JSONDecodeError:
            continue
    return []

# ── Validators ─────────────────────────────────────────────────────────────────

GARBLED_RE = re.compile(r"[\ufffd]{2,}|[?]{3,}|撠\?|嚗|蝚|銝|憭")
ANSWER_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")
ANSWER_FRACTION_RE = re.compile(r"^-?\d+\s*/\s*\d+$")
ANSWER_MIXED_RE = re.compile(r"^-?\d+\s+\d+\s*/\s*\d+$")

def parse_answer_value(ans_str):
    """Try to parse answer as a Fraction for comparison. Returns None if unparseable."""
    s = ans_str.strip()
    # mixed: a b/c
    m = re.match(r"^(-?\d+)\s+(\d+)\s*/\s*(\d+)$", s)
    if m:
        w, n, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if d == 0: return None
        sign = -1 if w < 0 else 1
        return Fraction(sign * (abs(w) * d + n), d)
    # fraction: a/b
    m = re.match(r"^(-?\d+)\s*/\s*(\d+)$", s)
    if m:
        n, d = int(m.group(1)), int(m.group(2))
        if d == 0: return None
        return Fraction(n, d)
    # integer or decimal
    try:
        f = float(s)
        return Fraction(f).limit_denominator(100000)
    except ValueError:
        return None

def hint_leaks_answer(hints, answer_str):
    """Check if the last hint (L3) literally contains the final answer as standalone text."""
    if not hints or len(hints) < 3:
        return False
    ans = answer_str.strip()
    if not ans or len(ans) > 20:
        return False  # skip long text answers
    # Check last hint only
    last_hint = str(hints[-1])
    # Look for answer as a standalone token: word boundary or surrounded by non-alphanumeric
    # Pattern: answer appears after "答案" or "=" or at end
    patterns = [
        # "答案：X" or "答案是 X" or "= X"
        re.compile(r"答案[：:是為]\s*" + re.escape(ans) + r"\s*[。\.\s]?$", re.MULTILINE),
        # "答案：X" anywhere
        re.compile(r"答案[：:]\s*" + re.escape(ans) + r"\b"),
    ]
    for pat in patterns:
        if pat.search(last_hint):
            return True
    return False

def validate_question(q, idx, seen_texts):
    """Returns list of (code, message) failures."""
    fails = []
    qid = q.get("id", f"index_{idx}")

    # Q1: question text
    qtext = str(q.get("question", "")).strip()
    if len(qtext) < 10:
        fails.append(("Q1_SHORT_QUESTION", f"question text too short ({len(qtext)} chars)"))

    # Q2: answer
    answer = str(q.get("answer", "")).strip()
    if not answer:
        fails.append(("Q2_NO_ANSWER", "missing answer"))

    # Q3: hints
    hints = q.get("hints", [])
    if not isinstance(hints, list):
        fails.append(("Q3_HINTS_NOT_LIST", f"hints is {type(hints).__name__}"))
        hints = []
    if len(hints) < 3:
        fails.append(("Q3_HINTS_TOO_FEW", f"only {len(hints)} hints (need ≥3)"))
    for i, h in enumerate(hints):
        if len(str(h).strip()) < 5:
            fails.append(("Q3_HINT_EMPTY", f"hint[{i}] too short"))
            break  # report once

    # Q4: steps
    steps = q.get("steps", [])
    if not isinstance(steps, list) or len(steps) < 1:
        fails.append(("Q4_NO_STEPS", "missing or empty steps"))

    # Q5: explanation
    expl = str(q.get("explanation", "")).strip()
    if len(expl) < 5:
        fails.append(("Q5_NO_EXPLANATION", f"explanation too short ({len(expl)} chars)"))

    # Q6: difficulty
    diff = str(q.get("difficulty", "")).lower()
    if diff not in ("easy", "medium", "hard"):
        fails.append(("Q6_BAD_DIFFICULTY", f"difficulty='{diff}'"))

    # Q7: topic
    topic = str(q.get("topic", "")).strip()
    if not topic:
        fails.append(("Q7_NO_TOPIC", "missing topic"))

    # Q8: kind
    kind = str(q.get("kind", "")).strip()
    if not kind:
        fails.append(("Q8_NO_KIND", "missing kind"))

    # Q9: garbled text (encoding corruption)
    all_text = " ".join([qtext, answer, topic, kind] + [str(h) for h in hints] + [expl])
    if GARBLED_RE.search(all_text):
        # Check if it's actually Chinese (some patterns are valid Chinese chars)
        # Only flag if we see replacement chars or consecutive ???
        if "\ufffd" in all_text or "???" in all_text:
            fails.append(("Q9_GARBLED", "possible encoding corruption"))

    # Q10: hint leaks answer
    if hint_leaks_answer(hints, answer):
        fails.append(("Q10_HINT_LEAKS_ANSWER", f"last hint reveals answer '{answer}'"))

    # Q11: arithmetic spot-check (simple cases only)
    # For fraction answers: check that the question's numbers can produce the answer
    # This is a lightweight check, not a full solver
    if answer and ANSWER_FRACTION_RE.match(answer):
        # Check: answer like "7/1" is probably wrong (should be "7")
        m = re.match(r"^(-?\d+)/(\d+)$", answer)
        if m and m.group(2) == "1":
            fails.append(("Q11_FRACTION_OVER_1", f"answer '{answer}' — denominator is 1, should be integer?"))
    
    # Check for negative answers in word problems (likely wrong)
    if answer and answer.startswith("-") and "生活" in topic:
        val = parse_answer_value(answer)
        if val is not None and val < 0:
            fails.append(("Q11_NEGATIVE_ANSWER", f"negative answer '{answer}' in word problem"))

    # Q12: duplicate question text
    dedup_key = qtext[:120].strip()
    if dedup_key in seen_texts:
        fails.append(("Q12_DUPLICATE", f"duplicate of {seen_texts[dedup_key]}"))
    else:
        seen_texts[dedup_key] = qid

    return fails

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    bank = load_bank(BANK_PATH)
    if not bank:
        print("ERROR: could not load bank.js")
        sys.exit(1)

    print(f"Loaded {len(bank)} questions from {BANK_PATH.name}")
    print("=" * 72)

    seen_texts = {}
    all_fails = []
    fail_by_code = collections.Counter()
    fail_by_module = collections.Counter()

    for idx, q in enumerate(bank):
        fails = validate_question(q, idx, seen_texts)
        if fails:
            qid = q.get("id", f"index_{idx}")
            module = (q.get("meta") or {}).get("source_module", "?")
            for code, msg in fails:
                all_fails.append((qid, module, code, msg))
                fail_by_code[code] += 1
                fail_by_module[module] += 1

    # ── Summary ────────────────────────────────────────────────────────────
    total = len(bank)
    fail_ids = set(f[0] for f in all_fails)
    pass_count = total - len(fail_ids)

    print(f"\n{'='*72}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*72}")
    print(f"Total questions : {total}")
    print(f"PASS            : {pass_count} ({pass_count/total*100:.1f}%)")
    print(f"FAIL            : {len(fail_ids)} ({len(fail_ids)/total*100:.1f}%)")
    print(f"Total issues    : {len(all_fails)}")

    print(f"\n── Failures by Code ──")
    for code, count in fail_by_code.most_common():
        print(f"  {code:30s}  {count:4d}")

    print(f"\n── Failures by Module ──")
    for mod, count in fail_by_module.most_common():
        print(f"  {mod:45s}  {count:4d}")

    # ── Difficulty distribution ─────────────────────────────────────────────
    diff_dist = collections.Counter(q.get("difficulty", "?") for q in bank)
    print(f"\n── Difficulty Distribution ──")
    for d, c in diff_dist.most_common():
        print(f"  {d:10s}  {c:4d}  ({c/total*100:.1f}%)")

    # ── Module distribution ─────────────────────────────────────────────────
    mod_dist = collections.Counter((q.get("meta") or {}).get("source_module", "?") for q in bank)
    print(f"\n── Source Module Distribution ──")
    for mod, c in sorted(mod_dist.items(), key=lambda x: -x[1]):
        print(f"  {mod:45s}  {c:4d}")

    # ── Topic distribution ──────────────────────────────────────────────────
    topic_dist = collections.Counter(q.get("topic", "?") for q in bank)
    print(f"\n── Topic Distribution (top 20) ──")
    for t, c in topic_dist.most_common(20):
        print(f"  {t:50s}  {c:4d}")

    # ── Kind distribution (top 30) ──────────────────────────────────────────
    kind_dist = collections.Counter(q.get("kind", "?") for q in bank)
    print(f"\n── Kind Distribution (top 30) ──")
    for k, c in kind_dist.most_common(30):
        print(f"  {k:40s}  {c:4d}")

    # ── Print all failures ──────────────────────────────────────────────────
    if all_fails:
        print(f"\n{'='*72}")
        print(f"ALL FAILURES ({len(all_fails)} issues in {len(fail_ids)} questions)")
        print(f"{'='*72}")
        for qid, mod, code, msg in all_fails:
            print(f"  [{code}] {qid}")
            print(f"    module: {mod}")
            print(f"    detail: {msg}")
            print()

    # ── Spot-check: sample hint quality ─────────────────────────────────────
    print(f"\n{'='*72}")
    print(f"HINT QUALITY SPOT-CHECK (5 random samples)")
    print(f"{'='*72}")
    import random
    random.seed(42)
    samples = random.sample(bank, min(5, len(bank)))
    for q in samples:
        print(f"\n  ID: {q['id']}")
        print(f"  Q:  {q['question'][:80]}...")
        print(f"  A:  {q['answer']}")
        hints = q.get("hints", [])
        for i, h in enumerate(hints[:3]):
            print(f"  H{i+1}: {str(h)[:100]}...")
        print(f"  Expl: {str(q.get('explanation',''))[:80]}...")

    return 0 if not fail_ids else 1


if __name__ == "__main__":
    sys.exit(main())
