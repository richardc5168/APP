#!/usr/bin/env python3
"""
Download 國小5年級數學段考題目卷+答案卷 from tcool.cc
API: POST https://www.tcool.cc/api-exam.php
"""
import requests, json, os, sys, time, re
from pathlib import Path

API = "https://www.tcool.cc/api-exam.php"
DL_BASE = "https://tcool.cc/d"
OUT = Path(__file__).resolve().parent.parent / "artifacts" / "tcool_exams"
OUT.mkdir(parents=True, exist_ok=True)

sess = requests.Session()
sess.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://tcool.cc/",
    "Origin": "https://tcool.cc",
})

PER_PAGE = 20  # API max is 20

def fetch_exams(grade=5, subject="數學", page=1):
    """Fetch exam listing from API."""
    payload = {
        "action": "exam_data",
        "p": page,
        "pp": PER_PAGE,
        "grade": str(grade),
        "subject": subject,
    }
    r = sess.post(API, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def download_file(url, dest):
    """Download a file, skip if already exists."""
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  SKIP (exists): {dest.name}")
        return True
    try:
        r = sess.get(url, timeout=30, stream=True)
        if r.status_code != 200:
            print(f"  FAIL ({r.status_code}): {url}")
            return False
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        sz = dest.stat().st_size
        print(f"  OK: {dest.name} ({sz:,} bytes)")
        return True
    except Exception as e:
        print(f"  ERROR: {url} -> {e}")
        return False

def safe_filename(s):
    """Make a safe filename from a string."""
    return re.sub(r'[\\/:*?"<>|]', '_', str(s))

def main():
    print("=" * 60)
    print("tcool.cc 國小5年級數學 段考題目+答案 下載器")
    print("=" * 60)

    # Step 1: Get filter options
    print("\n[1] Fetching filter options...")
    try:
        r = sess.post(API, json={"action": "filter_options"}, timeout=15)
        opts = r.json()
        if "filterOptions" in opts:
            fo = opts["filterOptions"]
            print(f"  Grades: {fo.get('grade', [])}")
            print(f"  Subjects: {fo.get('subject', [])}")
            print(f"  Semesters: {fo.get('semester', [])}")
            print(f"  Periods: {fo.get('period', [])}")
    except Exception as e:
        print(f"  Warning: {e}")

    # Step 2: Fetch all 5年級 數學 exams (with answer sheets)
    all_exams = []
    page = 1
    print(f"\n[2] Fetching exam listings (grade=5, subject=數學)...")
    while True:
        data = fetch_exams(grade=5, subject="數學", page=page)
        if data.get("error"):
            print(f"  API error: {data['error']}")
            break
        exams = data.get("data", [])
        pagination = data.get("pagination", {})
        total_pages = pagination.get("totalPages", 1)
        total = pagination.get("total", 0)
        print(f"  Page {page}/{total_pages} — got {len(exams)} exams (total: {total})")
        all_exams.extend(exams)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.5)

    print(f"\n  Total exams found: {len(all_exams)}")

    # Filter: only exams with both question AND answer files
    with_answers = [e for e in all_exams if e.get("answer") and e["answer"] != "null" and e.get("question") and e["question"] != "null"]
    print(f"  With both question + answer: {len(with_answers)}")

    # Save listing JSON
    listing_path = OUT / "exam_listing.json"
    with open(listing_path, "w", encoding="utf-8") as f:
        json.dump(with_answers, f, ensure_ascii=False, indent=2)
    print(f"  Saved listing to {listing_path}")

    # Step 3: Download question + answer PDFs
    print(f"\n[3] Downloading PDFs...")
    q_dir = OUT / "questions"
    a_dir = OUT / "answers"
    q_dir.mkdir(exist_ok=True)
    a_dir.mkdir(exist_ok=True)

    stats = {"q_ok": 0, "q_fail": 0, "a_ok": 0, "a_fail": 0, "skip": 0}

    for i, exam in enumerate(with_answers):
        school = exam.get("school", "unknown")
        city = exam.get("city", "")
        grade = exam.get("grade", "5")
        subject = exam.get("subject", "數學")
        year_c = exam.get("year-c", "")
        period_c = exam.get("period-c", "")
        publisher = exam.get("publisher", "")
        q_file = exam.get("question", "")
        a_file = exam.get("answer", "")
        exam_id = exam.get("id", "")

        prefix = safe_filename(f"{year_c}_{school}_{city}_{period_c}_{publisher}")

        print(f"\n[{i+1}/{len(with_answers)}] {school} ({city}) {year_c} {period_c} {publisher}")

        # Download question PDF
        if q_file and q_file != "null":
            ext = ".pdf" if q_file.lower().endswith(".pdf") else os.path.splitext(q_file)[1] or ".pdf"
            q_dest = q_dir / f"{prefix}_題目{ext}"
            q_url = f"{DL_BASE}/q/{q_file}"
            if download_file(q_url, q_dest):
                stats["q_ok"] += 1
            else:
                stats["q_fail"] += 1
        else:
            print("  (no question file)")
            stats["skip"] += 1

        # Download answer PDF
        if a_file and a_file != "null":
            ext = ".pdf" if a_file.lower().endswith(".pdf") else os.path.splitext(a_file)[1] or ".pdf"
            a_dest = a_dir / f"{prefix}_答案{ext}"
            a_url = f"{DL_BASE}/a/{a_file}"
            if download_file(a_url, a_dest):
                stats["a_ok"] += 1
            else:
                stats["a_fail"] += 1
        else:
            print("  (no answer file)")

        time.sleep(0.3)  # polite rate limit

    # Summary
    print("\n" + "=" * 60)
    print("下載完成 Summary:")
    print(f"  題目卷: {stats['q_ok']} OK, {stats['q_fail']} failed")
    print(f"  答案卷: {stats['a_ok']} OK, {stats['a_fail']} failed")
    print(f"  Skipped: {stats['skip']}")
    print(f"  Files in: {OUT}")
    print("=" * 60)

if __name__ == "__main__":
    main()
