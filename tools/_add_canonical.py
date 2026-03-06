#!/usr/bin/env python3
"""Add <link rel="canonical" href="./"> to all docs/ HTML files.

Uses relative self-reference canonical to avoid no_root_home_links check.
"""
import pathlib, re

DOCS = pathlib.Path("docs")
DIST = pathlib.Path("dist_ai_math_web_pages/docs")

def add_canonical(fpath: pathlib.Path) -> bool:
    text = fpath.read_text(encoding="utf-8")
    if 'rel="canonical"' in text:
        return False
    # Insert after last <meta> tag in <head>, before </head> or <style> or <link rel="manifest">
    # Strategy: insert before </head>
    new_text = text.replace(
        "</head>",
        '  <link rel="canonical" href="./">\n</head>',
        1
    )
    if new_text == text:
        return False
    fpath.write_text(new_text, encoding="utf-8")
    return True

count = 0
for html in sorted(DOCS.rglob("index.html")):
    if add_canonical(html):
        print(f"OK {html.relative_to(DOCS)}")
        count += 1
    else:
        print(f"SKIP {html.relative_to(DOCS)}")

# Sync to dist
for html in sorted(DIST.rglob("index.html")):
    src = DOCS / html.relative_to(DIST)
    if src.exists():
        import shutil
        shutil.copy2(src, html)

print(f"\nAdded canonical to {count} files")
