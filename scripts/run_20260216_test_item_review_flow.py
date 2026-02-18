from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> int:
    print("RUN:", " ".join(cmd))
    cp = subprocess.run(cmd)
    return int(cp.returncode)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run review validation/summary/apply flow for 20260216_test_item.")
    p.add_argument("--review_jsonl", default="artifacts/20260216_test_item_reviews.jsonl")
    p.add_argument("--dump_jsonl", default="artifacts/20260216_test_item.jsonl")
    p.add_argument("--summary_md", default="artifacts/20260216_test_item_review_summary.md")
    p.add_argument("--out_dir", default="artifacts/20260216_review_apply")
    p.add_argument("--python", default=sys.executable)
    args = p.parse_args(argv)

    review = Path(args.review_jsonl)
    dump = Path(args.dump_jsonl)

    if not dump.exists():
        print(f"ERROR: dump file not found: {dump}")
        return 2
    if not review.exists():
        print(f"ERROR: review file not found: {review}")
        print("Please generate it with your external model first.")
        return 2

    py = args.python

    rc = run([py, "scripts/validate_question_reviews.py", "--in_jsonl", str(review)])
    if rc != 0:
        return rc

    rc = run([
        py,
        "scripts/summarize_question_reviews.py",
        "--in_jsonl",
        str(review),
        "--out_md",
        str(args.summary_md),
    ])
    if rc != 0:
        return rc

    rc = run([
        py,
        "scripts/apply_question_reviews.py",
        "--in_reviews",
        str(review),
        "--in_dump",
        str(dump),
        "--out_dir",
        str(args.out_dir),
    ])
    if rc != 0:
        return rc

    print("OK: 20260216 review flow completed")
    print(f"- summary: {args.summary_md}")
    print(f"- apply out: {args.out_dir}")
    print("Next: review patch then run: git apply <out_dir>/hint_overrides_candidates.patch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
