#!/usr/bin/env python3
"""Debug tcool.cc download 403 issue."""
import requests

sess = requests.Session()
sess.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
})

# Visit main page to get session cookies
print("=== Step 1: Visit main page ===")
r1 = sess.get("https://tcool.cc/", timeout=15)
print(f"Status: {r1.status_code}")
print(f"Cookies: {dict(sess.cookies)}")

# Try download with cookies
print("\n=== Step 2: Try download ===")
test_url = "https://tcool.cc/d/q/50000081b51138800895.pdf"
r2 = sess.get(test_url, timeout=15, allow_redirects=True)
print(f"Status: {r2.status_code}")
ct = r2.headers.get("content-type", "")
print(f"Content-Type: {ct}")
print(f"Content-Length: {len(r2.content)}")
print(f"Redirects: {[h.status_code for h in r2.history]}")
if r2.status_code != 200 or "pdf" not in ct.lower():
    print(f"Body: {r2.text[:500]}")

# Try with Referer header
print("\n=== Step 3: Try with Referer ===")
sess.headers["Referer"] = "https://tcool.cc/"
r3 = sess.get(test_url, timeout=15, allow_redirects=True)
print(f"Status: {r3.status_code}")
ct3 = r3.headers.get("content-type", "")
print(f"Content-Type: {ct3}")
print(f"Content-Length: {len(r3.content)}")
if r3.status_code != 200 or "pdf" not in ct3.lower():
    print(f"Body: {r3.text[:500]}")

# Try www subdomain
print("\n=== Step 4: Try www.tcool.cc ===")
test_url2 = "https://www.tcool.cc/d/q/50000081b51138800895.pdf"
r4 = sess.get(test_url2, timeout=15, allow_redirects=True)
print(f"Status: {r4.status_code}")
ct4 = r4.headers.get("content-type", "")
print(f"Content-Type: {ct4}")
print(f"Content-Length: {len(r4.content)}")
if r4.status_code == 200 and len(r4.content) > 1000:
    print("SUCCESS! www.tcool.cc works")
else:
    print(f"Body: {r4.text[:500]}")

# Try different path patterns
print("\n=== Step 5: Try other URL patterns ===")
patterns = [
    "https://tcool.cc/d/q/50000081b51138800895.pdf",
    "https://www.tcool.cc/d/q/50000081b51138800895.pdf",
    "https://tcool.cc/download/q/50000081b51138800895.pdf",
    "https://tcool.cc/exam/download/50000081b51138800895.pdf",
]
for url in patterns:
    try:
        r = sess.get(url, timeout=10, allow_redirects=True)
        print(f"  {url} -> {r.status_code} ({r.headers.get('content-type','')[:30]}) {len(r.content)}b")
    except Exception as e:
        print(f"  {url} -> ERROR: {e}")
