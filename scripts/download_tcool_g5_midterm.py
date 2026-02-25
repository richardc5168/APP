#!/usr/bin/env python3
"""
Download 國小5年級數學 下學期 第一次期中考 題目+答案 from tcool.cc
Uses Playwright (visible browser) to bypass Cloudflare.
"""
import asyncio, json, os, re, time
from pathlib import Path

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
    print("tcool.cc 國小5年級數學 下學期 期中1 題目+答案 下載")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(accept_downloads=True)
        page = await ctx.new_page()

        # Step 1: Visit main page to pass Cloudflare
        print("\n[1] Visiting tcool.cc to pass Cloudflare check...")
        await page.goto("https://tcool.cc/", wait_until="domcontentloaded", timeout=60000)
        for attempt in range(30):
            title = await page.title()
            url = page.url
            print(f"  [{attempt}] Title: {title} | URL: {url}")
            if 'moment' not in title.lower() and 'challenge' not in title.lower() and 'just' not in title.lower():
                break
            await page.wait_for_timeout(3000)
        print(f"  ✓ Cloudflare passed. Title: {await page.title()}")

        # Step 2: Get exam listing via browser fetch (bypass CORS/Cloudflare)
        # API params: semester=2(下學期), period=1(期中考), has_answer=1
        print("\n[2] Fetching exam listings via browser fetch...")
        all_exams = []
        pg = 1
        while True:
            params = {
                "action": "exam_data",
                "p": pg,
                "pp": 20,
                "grade": "5",
                "subject": "數學",
                "semester": "2",
                "period": "1"
            }
            print(f"  Requesting page {pg} with params: {json.dumps(params, ensure_ascii=False)}")
            result = await page.evaluate("""async (params) => {
                try {
                    const r = await fetch('https://www.tcool.cc/api-exam.php', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(params)
                    });
                    return await r.json();
                } catch(e) {
                    return {error: e.message};
                }
            }""", params)

            if result.get("error"):
                print(f"  API error: {result['error']}")
                break

            exams = result.get("data", [])
            pagination = result.get("pagination", {})
            total_pages = pagination.get("totalPages", 1)
            total = pagination.get("total", 0)
            print(f"  Page {pg}/{total_pages} — {len(exams)} exams (total: {total})")

            if exams:
                # Print first exam to see field structure
                if pg == 1 and exams:
                    print(f"  Sample fields: {list(exams[0].keys())}")
                    print(f"  Sample: {json.dumps(exams[0], ensure_ascii=False)[:300]}")
                all_exams.extend(exams)

            if pg >= total_pages or not exams:
                break
            pg += 1
            await page.wait_for_timeout(500)

        # Filter: only those with both question AND answer files
        with_both = [e for e in all_exams
                     if e.get("question") and str(e["question"]).strip() not in ("", "null", "None")
                     and e.get("answer") and str(e["answer"]).strip() not in ("", "null", "None")]
        print(f"\n  Total fetched: {len(all_exams)}, With both Q+A: {len(with_both)}")

        # Save listing JSON
        listing_path = OUT / "exam_listing_g5_midterm1.json"
        with open(listing_path, "w", encoding="utf-8") as f:
            json.dump(with_both, f, ensure_ascii=False, indent=2)
        print(f"  Saved listing: {listing_path}")

        # Step 3: Download PDFs
        print(f"\n[3] Downloading {len(with_both)} exam pairs...")
        stats = {"q_ok": 0, "q_fail": 0, "a_ok": 0, "a_fail": 0}

        for i, exam in enumerate(with_both):
            school = exam.get("school", "unknown")
            city = exam.get("city", "")
            year_c = exam.get("year-c", exam.get("year", ""))
            period_c = exam.get("period-c", exam.get("period", ""))
            publisher = exam.get("publisher", "")
            q_file = str(exam.get("question", ""))
            a_file = str(exam.get("answer", ""))

            prefix = safe_fn(f"{year_c}_{school}_{city}_{period_c}_{publisher}")
            print(f"\n[{i+1}/{len(with_both)}] {school} ({city}) {year_c} {period_c} {publisher}")

            # --- Download Question PDF ---
            q_ext = os.path.splitext(q_file)[1] or ".pdf"
            q_dest = Q_DIR / f"{prefix}_題目{q_ext}"
            if q_dest.exists() and q_dest.stat().st_size > 1000:
                print(f"  SKIP Q (exists {q_dest.stat().st_size:,}b): {q_dest.name}")
                stats["q_ok"] += 1
            else:
                q_url = f"https://tcool.cc/d/q/{q_file}"
                try:
                    dl_page = await ctx.new_page()
                    resp = await dl_page.goto(q_url, wait_until="load", timeout=20000)
                    if resp and resp.status == 200:
                        body = await resp.body()
                        if body and len(body) > 1000:
                            with open(q_dest, "wb") as f:
                                f.write(body)
                            print(f"  ✓ Q: {q_dest.name} ({len(body):,}b)")
                            stats["q_ok"] += 1
                        else:
                            print(f"  ✗ Q: body too small ({len(body) if body else 0}b)")
                            stats["q_fail"] += 1
                    else:
                        print(f"  ✗ Q: HTTP {resp.status if resp else '?'}")
                        stats["q_fail"] += 1
                    await dl_page.close()
                except Exception as e:
                    print(f"  ✗ Q: {e}")
                    stats["q_fail"] += 1
                    try: await dl_page.close()
                    except: pass

            # --- Download Answer PDF ---
            a_ext = os.path.splitext(a_file)[1] or ".pdf"
            a_dest = A_DIR / f"{prefix}_答案{a_ext}"
            if a_dest.exists() and a_dest.stat().st_size > 500:
                print(f"  SKIP A (exists {a_dest.stat().st_size:,}b): {a_dest.name}")
                stats["a_ok"] += 1
            else:
                a_url = f"https://tcool.cc/d/a/{a_file}"
                try:
                    dl_page = await ctx.new_page()
                    resp = await dl_page.goto(a_url, wait_until="load", timeout=20000)
                    if resp and resp.status == 200:
                        body = await resp.body()
                        if body and len(body) > 500:
                            with open(a_dest, "wb") as f:
                                f.write(body)
                            print(f"  ✓ A: {a_dest.name} ({len(body):,}b)")
                            stats["a_ok"] += 1
                        else:
                            print(f"  ✗ A: body too small ({len(body) if body else 0}b)")
                            stats["a_fail"] += 1
                    else:
                        print(f"  ✗ A: HTTP {resp.status if resp else '?'}")
                        stats["a_fail"] += 1
                    await dl_page.close()
                except Exception as e:
                    print(f"  ✗ A: {e}")
                    stats["a_fail"] += 1
                    try: await dl_page.close()
                    except: pass

            await page.wait_for_timeout(800)

        await browser.close()

    print("\n" + "=" * 60)
    print("下載完成 Summary:")
    print(f"  題目卷: {stats['q_ok']} OK, {stats['q_fail']} failed")
    print(f"  答案卷: {stats['a_ok']} OK, {stats['a_fail']} failed")
    print(f"  Output: {OUT}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
