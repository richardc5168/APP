import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return int(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Quality gate: verify_all + pytest. Intended for pre-commit / CI-like local checks.")
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip pytest (not recommended).",
    )
    args = parser.parse_args()

    py = sys.executable

    rc = run([py, "scripts/verify_all.py"])
    if rc != 0:
        print("\nFAIL: verify_all")
        return rc

    if not args.skip_pytest:
        rc = run([py, "-m", "pytest", "-q"])
        if rc != 0:
            print("\nFAIL: pytest")
            return rc

    print("\nOK: precommit_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
