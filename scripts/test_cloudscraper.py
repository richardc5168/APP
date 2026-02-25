#!/usr/bin/env python3
"""Test cloudscraper to bypass Cloudflare on tcool.cc downloads."""
import cloudscraper

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "desktop": True}
)

# Test download
test_url = "https://tcool.cc/d/q/50000081b51138800895.pdf"
print(f"Trying: {test_url}")
r = scraper.get(test_url, timeout=30)
print(f"Status: {r.status_code}")
ct = r.headers.get("content-type", "")
print(f"Content-Type: {ct}")
print(f"Content-Length: {len(r.content)}")

if r.status_code == 200 and ("pdf" in ct.lower() or len(r.content) > 10000):
    with open("artifacts/tcool_exams/test_download.pdf", "wb") as f:
        f.write(r.content)
    print("SUCCESS! Saved test_download.pdf")
else:
    print(f"Body preview: {r.text[:300]}")
