#!/usr/bin/env python3
"""Discover tcool.cc structure and download 國小5年級數學 exam papers + answers."""
import requests, re, json, os, sys, time
from pathlib import Path

BASE = "https://tcool.cc"
OUT_DIR = Path(__file__).resolve().parent.parent / "artifacts" / "tcool_exams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://tcool.cc/",
})

# Step 1: Fetch the main page and discover structure
print("=== Step 1: Fetch main page ===")
r = session.get(BASE, timeout=15)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

# Extract all script sources
scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)', r.text)
print(f"Scripts: {scripts}")

# Look for any data attributes or embedded JSON
json_blocks = re.findall(r'(?:var|let|const)\s+\w+\s*=\s*(\{[^;]{20,500})', r.text)
print(f"JSON-like blocks: {len(json_blocks)}")
for jb in json_blocks[:5]:
    print(f"  {jb[:200]}")

# Look for fetch/axios/XMLHttpRequest API calls
api_calls = re.findall(r'(?:fetch|axios|XMLHttpRequest|\.get|\.post)\s*\(\s*["\']([^"\']+)', r.text)
print(f"API calls: {api_calls}")

# Look for form action
actions = re.findall(r'action=["\']([^"\']+)', r.text)
print(f"Form actions: {actions}")

# Save full HTML for inspection
with open(OUT_DIR / "main_page.html", "w", encoding="utf-8") as f:
    f.write(r.text)
print(f"Saved main page to {OUT_DIR / 'main_page.html'}")

# Step 2: Try common API patterns
print("\n=== Step 2: Try API patterns ===")
api_tries = [
    "/api/search?grade=5&subject=數學&has_answer=1",
    "/api/exams?grade=5&subject=數學",
    "/search?grade=5&subject=數學&has_answer=是",
    "/search.php?grade=5&subject=數學&has_answer=是",
    "/api/v1/exams?grade=5&subject=數學",
    "/exam/search?grade=5&subject=數學",
]
for path in api_tries:
    try:
        url = BASE + path
        r2 = session.get(url, timeout=10, allow_redirects=True)
        ctype = r2.headers.get("content-type", "")
        body_preview = r2.text[:300].replace("\n", " ")
        print(f"  {path} -> {r2.status_code} ({ctype[:40]}) [{len(r2.text)}b] {body_preview[:150]}")
        if "json" in ctype or r2.text.strip().startswith("{") or r2.text.strip().startswith("["):
            print(f"    JSON! {r2.text[:500]}")
            with open(OUT_DIR / f"api_response_{path.replace('/','_').replace('?','_')[:50]}.json", "w", encoding="utf-8") as f:
                f.write(r2.text)
    except Exception as e:
        print(f"  {path} -> ERROR: {e}")

# Step 3: Check if it's a PHP site or SPA
print("\n=== Step 3: Inspect page structure ===")
# Check for Vue/React/Angular
for fw in ["vue", "react", "angular", "next", "nuxt", "__NEXT", "__NUXT"]:
    if fw.lower() in r.text.lower():
        print(f"  Framework hint: {fw}")

# Look for PDF links or download patterns
pdf_links = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)', r.text)
print(f"PDF links in main page: {pdf_links[:10]}")

# Look for any data in the page that might be exam listings
exam_patterns = re.findall(r'(和順|大園|成功|廣興|內安|舊館)', r.text)
print(f"School names in page: {exam_patterns}")

print("\n=== Done ===")
