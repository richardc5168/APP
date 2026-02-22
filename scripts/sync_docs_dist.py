from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIST = ROOT / "dist_ai_math_web_pages" / "docs"


def sync_tree(src: Path, dst: Path) -> tuple[int, int, int]:
    copied = 0
    deleted = 0
    unchanged = 0

    src_files = {p.relative_to(src).as_posix(): p for p in src.rglob("*") if p.is_file()}
    dst_files = {p.relative_to(dst).as_posix(): p for p in dst.rglob("*") if p.is_file()}

    for rel, src_path in src_files.items():
        dst_path = dst / rel
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        if not dst_path.exists() or src_path.read_bytes() != dst_path.read_bytes():
            shutil.copy2(src_path, dst_path)
            copied += 1
        else:
            unchanged += 1

    for rel, dst_path in dst_files.items():
        if rel not in src_files and dst_path.exists():
            dst_path.unlink()
            deleted += 1

    for folder in sorted([p for p in dst.rglob("*") if p.is_dir()], key=lambda x: len(x.parts), reverse=True):
        try:
            folder.rmdir()
        except OSError:
            pass

    return copied, deleted, unchanged


def main() -> int:
    if not DOCS.exists():
        raise SystemExit(f"missing source folder: {DOCS}")
    DIST.mkdir(parents=True, exist_ok=True)

    copied, deleted, unchanged = sync_tree(DOCS, DIST)
    print(f"sync_docs_dist: copied={copied} deleted={deleted} unchanged={unchanged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
