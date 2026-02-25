#!/usr/bin/env python3
"""
Download 國小5年級數學 段考題目+答案 from tcool.cc using Playwright (browser-based).
Cloudflare blocks direct requests; Playwright passes the JS challenge.
"""
import asyncio, json, os, re, time
from pathlib import Path

# -- config --
API = "https://www.tcool.cc/api-exam.php"
DL_BASE = "https://tcool.cc/d"
OUT = Path(__file__).resolve().parent.parent / "artifacts" / "tcool_exams"
Q_DIR = OUT / "questions"
A_DIR = OUT / "answers"
for d in [OUT, Q_DIR, A_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def safe_fn(s):
    return re.sub(r'[\\/:*?"<>|]', '_', str(s)).strip('_')[:120]

async def main():
    from playwright.async_api import async_playwright

    print("=" * 60)
    print("tcool.cc 國小5年級數學 段考題目+答案 瀏覽器下載")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(accept_downloads=True)
        page = await ctx.new_page()

        # Step 1: Visit main page to pass Cloudflare
        print("\n[1] Visiting tcool.cc to pass Cloudflare check...")
        await page.goto("https://tcool.cc/", wait_until="domcontentloaded", timeout=60000)
        # Wait for Cloudflare challenge to resolve
        for attempt in range(20):
            title = await page.title()
            print(f"  [{attempt}] Title: {title}")
            if 'moment' not in title.lower() and 'challenge' not in title.lower():
                break
            await page.wait_for_timeout(3000)
        print(f"  Final title: {await page.title()}")

        # Step 2: Get exam listing via API (using page.evaluate to call fetch)
        print("\n[2] Fetching exam listings via browser fetch...")
        all_exams = []
        pg = 1
        while True:
            result = await page.evaluate("""async (params) => {
                const r = await fetch('https://www.tcool.cc/api-exam.php', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(params)
                });
                return await r.json();
            }""", {"action": "exam_data", "p": pg, "pp": 20, "grade": "5", "subject": "數學"})

            if result.get("error"):
                print(f"  API error: {result['error']}")
                break

            exams = result.get("data", [])
            pagination = result.get("pagination", {})
            total_pages = pagination.get("totalPages", 1)
            total = pagination.get("total", 0)
            print(f"  Page {pg}/{total_pages} — {len(exams)} exams (total: {total})")
            all_exams.extend(exams)

            if pg >= total_pages:
                break
            pg += 1
            await page.wait_for_timeout(300)

        # Filter: both question AND answer
        with_both = [e for e in all_exams
                     if e.get("question") and str(e["question"]) != "null"
                     and e.get("answer") and str(e["answer"]) != "null"]
        print(f"\n  Total: {len(all_exams)}, With both Q+A: {len(with_both)}")

        # Save listing
        with open(OUT / "exam_listing.json", "w", encoding="utf-8") as f:
            json.dump(with_both, f, ensure_ascii=False, indent=2)

        # Step 3: Download PDFs via browser navigation
        print(f"\n[3] Downloading {len(with_both)} exam pairs...")
        stats = {"q_ok": 0, "q_fail": 0, "a_ok": 0, "a_fail": 0}

        for i, exam in enumerate(with_both):
            school = exam.get("school", "unknown")
            city = exam.get("city", "")
            year_c = exam.get("year-c", "")
            period_c = exam.get("period-c", "")
            publisher = exam.get("publisher", "")
            q_file = exam.get("question", "")
            a_file = exam.get("answer", "")

            prefix = safe_fn(f"{year_c}_{school}_{city}_{period_c}_{publisher}")
            print(f"\n[{i+1}/{len(with_both)}] {school} ({city}) {year_c} {period_c} {publisher}")

            # Download question
            q_ext = ".pdf" if q_file.lower().endswith(".pdf") else (os.path.splitext(q_file)[1] or ".pdf")
            q_dest = Q_DIR / f"{prefix}_題目{q_ext}"
            if q_dest.exists() and q_dest.stat().st_size > 1000:
                print(f"  SKIP Q (exists): {q_dest.name}")
                stats["q_ok"] += 1
            else:
                q_url = f"{DL_BASE}/q/{q_file}"
                try:
                    dl_page = await ctx.new_page()
                    async with dl_page.expect_download(timeout=15000) as dl_info:
                        await dl_page.goto(q_url, timeout=15000)
                    download = await dl_info.value
                    await download.save_as(str(q_dest))
                    sz = q_dest.stat().st_size if q_dest.exists() else 0
                    print(f"  Q OK: {q_dest.name} ({sz:,}b)")
                    stats["q_ok"] += 1
                    await dl_page.close()
                except Exception as e:
                    # Fallback: try reading page content as PDF
                    try:
                        resp = await dl_page.goto(q_url, wait_until="load", timeout=15000)
                        if resp and resp.status == 200:
                            body = await resp.body()
                            if body and len(body) > 1000:
                                with open(q_dest, "wb") as f:
                                    f.write(body)
                                print(f"  Q OK (body): {q_dest.name} ({len(body):,}b)")
                                stats["q_ok"] += 1
                            else:
                                print(f"  Q FAIL (small body): {len(body) if body else 0}b")
                                stats["q_fail"] += 1
                        else:
                            print(f"  Q FAIL: {resp.status if resp else 'no resp'}")
                            stats["q_fail"] += 1
                    except Exception as e2:
                        print(f"  Q FAIL: {e2}")
                        stats["q_fail"] += 1
                    try:
                        await dl_page.close()
                    except:
                        pass

            # Download answer
            a_ext = ".pdf" if a_file.lower().endswith(".pdf") else (os.path.splitext(a_file)[1] or ".pdf")
            a_dest = A_DIR / f"{prefix}_答案{a_ext}"
            if a_dest.exists() and a_dest.stat().st_size > 1000:
                print(f"  SKIP A (exists): {a_dest.name}")
                stats["a_ok"] += 1
            else:
                a_url = f"{DL_BASE}/a/{a_file}"
                try:
                    dl_page = await ctx.new_page()
                    resp = await dl_page.goto(a_url, wait_until="load", timeout=15000)
                    if resp and resp.status == 200:
                        body = await resp.body()
                        if body and len(body) > 500:
                            with open(a_dest, "wb") as f:
                                f.write(body)
                            print(f"  A OK: {a_dest.name} ({len(body):,}b)")
                            stats["a_ok"] += 1
                        else:
                            print(f"  A FAIL (small): {len(body) if body else 0}b")
                            stats["a_fail"] += 1
                    else:
                        print(f"  A FAIL: {resp.status if resp else 'no resp'}")
                        stats["a_fail"] += 1
                    await dl_page.close()
                except Exception as e:
                    print(f"  A FAIL: {e}")
                    stats["a_fail"] += 1
                    try:
                        await dl_page.close()
                    except:
                        pass

            await page.wait_for_timeout(500)

        await browser.close()

    print("\n" + "=" * 60)
    print("下載完成 Summary:")
    print(f"  題目卷: {stats['q_ok']} OK, {stats['q_fail']} failed")
    print(f"  答案卷: {stats['a_ok']} OK, {stats['a_fail']} failed")
    print(f"  Output: {OUT}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
