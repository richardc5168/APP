#!/usr/bin/env python3
"""Quick probe: discover tcool API field names for filtering."""
import asyncio, json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "artifacts" / "tcool_exams"
OUT.mkdir(parents=True, exist_ok=True)

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto("https://tcool.cc/", wait_until="domcontentloaded", timeout=60000)
        for i in range(15):
            title = await page.title()
            if 'moment' not in title.lower() and 'challenge' not in title.lower():
                break
            await page.wait_for_timeout(2000)
        print(f"CF passed: {await page.title()}")

        # Try various param combos
        tests = [
            # baseline — no filters at all
            {"action": "exam_data", "p": 1, "pp": 5, "grade": "5", "subject": "數學"},
            # try semester as number
            {"action": "exam_data", "p": 1, "pp": 5, "grade": "5", "subject": "數學", "semester": "2"},
            # try period without semester
            {"action": "exam_data", "p": 1, "pp": 5, "grade": "5", "subject": "數學", "period": "1"},
            # try with "term"
            {"action": "exam_data", "p": 1, "pp": 5, "grade": "5", "subject": "數學", "term": "下"},
            # try has_answer as bool or string
            {"action": "exam_data", "p": 1, "pp": 5, "grade": "5", "subject": "數學", "has_answer": 1},
            {"action": "exam_data", "p": 1, "pp": 5, "grade": "5", "subject": "數學", "hasAnswer": "1"},
        ]

        for t in tests:
            result = await page.evaluate("""async (params) => {
                try {
                    const r = await fetch('https://www.tcool.cc/api-exam.php', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(params)
                    });
                    return await r.json();
                } catch(e) { return {error: e.message}; }
            }""", t)
            total = result.get("pagination", {}).get("total", "?")
            data = result.get("data", [])
            # show first item keys
            sample = ""
            if data:
                sample = json.dumps(data[0], ensure_ascii=False)[:200]
            print(f"\nParams: {json.dumps(t, ensure_ascii=False)}")
            print(f"  Total: {total}, Got: {len(data)}")
            if sample:
                print(f"  Sample: {sample}")

        # Also try to intercept actual site search
        print("\n\n=== Intercepting site's own search request ===")
        requests_captured = []
        async def capture(route, request):
            if "api-exam" in request.url:
                body = request.post_data
                requests_captured.append({"url": request.url, "body": body})
                print(f"  CAPTURED: {request.url}\n    body: {body}")
            await route.continue_()

        await page.route("**/*api-exam*", capture)

        # Now interact with the page like the user would
        # Try clicking search with the dropdowns set
        try:
            # Look for select elements
            selects = await page.query_selector_all("select")
            print(f"\n  Found {len(selects)} <select> elements")
            for sel in selects:
                name = await sel.get_attribute("name") or await sel.get_attribute("id") or "?"
                options = await sel.query_selector_all("option")
                opt_texts = []
                for o in options[:8]:
                    t = await o.inner_text()
                    v = await o.get_attribute("value")
                    opt_texts.append(f"{v}={t}")
                print(f"    <select name='{name}'> options: {opt_texts}")
        except Exception as e:
            print(f"  Error inspecting selects: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
