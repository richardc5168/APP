"""Add og: meta tags and missing meta descriptions to all module pages."""
import os, re

BASE = os.path.dirname(os.path.dirname(__file__))
SITE_URL = 'https://richardc5168.github.io/ai-math-web'

# Module: (description for meta + og, og_title override or None to use <title>)
MODULES = {
    'exam-sprint': ('考前衝刺練習：依考試範圍快速出題，AI 三階段提示引導解題，不給答案', None),
    'fraction-g5': ('國小五年級分數計算練習：通分、約分、加減乘除，AI 提示引導一步步理解', '分數計算練習｜AI 數學家教'),
    'g5-grand-slam': ('全課綱 188 題大滿貫，涵蓋小五上下學期所有數學單元', None),
    'interactive-g5-midterm1': ('全國題庫小五下數學整理，段考重點題型離線練習', '全國題庫小五下數學｜AI 數學家教'),
    'interactive-g5-national-bank': ('全國題庫小五下數學，精選段考題型離線練習', '全國題庫精選｜AI 數學家教'),
    'interactive-g56-core-foundation': ('國小五六年級核心必殺技練習，基礎概念重點加強', None),
    'ratio-percent-g5': ('國小五年級比率與百分率練習：百分率換算、折扣計算、AI 引導解題', '比率與百分率練習｜AI 數學家教'),
    'volume-g5': ('國小五年級體積練習：長方體、正方體體積公式，AI 提示引導計算', '體積練習｜AI 數學家教'),
    'fraction-word-g5': ('分數應用題練習：生活情境分數問題，AI 三階段提示引導解題', None),
    'decimal-unit4': ('國小五年級小數生活應用練習：小數乘除、單位換算，AI 引導解題', '小數生活應用｜AI 數學家教'),
    'interactive-decimal-g5': ('互動小五小數計算闖關練習：小數乘除法，遊戲化學習', '小數闖關練習｜AI 數學家教'),
    'interactive-g5-empire': ('數學帝國闖關：答對擴張領地，2900+ 題搭配 AI 提示，遊戲化數學練習', None),
    'interactive-g5-life-pack1-empire': ('生活應用題帝國第一包：10 單元生活情境數學，遊戲化闖關', '生活應用帝國（第一包）｜AI 數學家教'),
    'interactive-g5-life-pack1plus-empire': ('生活應用題帝國加強版：進階難度生活情境數學闖關', '生活應用帝國（加強版）｜AI 數學家教'),
    'interactive-g5-life-pack2-empire': ('生活應用題帝國第二包：10 單元進階生活情境數學闖關', '生活應用帝國（第二包）｜AI 數學家教'),
    'interactive-g5-life-pack2plus-empire': ('生活應用題帝國基礎入門：基礎級生活情境數學闖關', '生活應用帝國（基礎入門）｜AI 數學家教'),
    'life-applications-g5': ('國小五年級生活應用題：講義搭配自動出題，AI 引導解題', '生活應用題練習｜AI 數學家教'),
    'offline-math': ('離線數學題型練習：不需網路也能練習，PWA 離線可用', '離線數學練習｜AI 數學家教'),
    'offline-math-v2': ('小學基礎數學檢測：快速診斷弱點，AI 建議加強方向', '基礎數學檢測｜AI 數學家教'),
    'mixed-multiply': ('帶分數乘法練習：帶分數轉假分數再相乘，AI 逐步引導', '帶分數乘法｜AI 數學家教'),
    'commercial-pack1-fraction-sprint': ('分數衝刺包：200 題分數專項練習，快速提升分數計算能力', None),
    'learning-map': ('題型觀念地圖：視覺化展示各單元知識點關聯', '題型觀念地圖｜AI 數學家教'),
    'pricing': ('AI 數學家教方案與價格：免費版、標準版 NT$299/月、進階版 NT$499/月', None),
    'about': ('關於 AI 數學家教：專為國小五六年級設計的智能數學練習系統', None),
    'terms': ('AI 數學家教服務條款', None),
    'privacy': ('AI 數學家教隱私權政策：資料安全、不收集個資', None),
    'parent-report': ('家長遠端報告：隨時在手機查看孩子的學習進度與弱點分析', None),
}

count = 0
for mod, (desc, og_title_override) in MODULES.items():
    path = os.path.join(BASE, 'docs', mod, 'index.html')
    if not os.path.exists(path):
        print(f"SKIP {mod}")
        continue

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Extract existing <title> for og:title
    title_match = re.search(r'<title>([^<]+)</title>', content)
    page_title = title_match.group(1) if title_match else mod
    og_title = og_title_override if og_title_override else page_title

    og_url = f"{SITE_URL}/{mod}/"

    # Build meta tags to add
    new_tags = []

    # Add meta description if missing
    if '<meta name="description"' not in content:
        new_tags.append(f'  <meta name="description" content="{desc}">')

    # Add og: tags if missing
    if '<meta property="og:title"' not in content:
        new_tags.append(f'  <meta property="og:title" content="{og_title}">')
    if '<meta property="og:description"' not in content:
        new_tags.append(f'  <meta property="og:description" content="{desc}">')
    if '<meta property="og:type"' not in content:
        new_tags.append('  <meta property="og:type" content="website">')
    if '<meta property="og:url"' not in content:
        new_tags.append(f'  <meta property="og:url" content="{og_url}">')

    if not new_tags:
        print(f"SKIP {mod} (already complete)")
        continue

    # Insert after <title> tag
    insert_str = '\n'.join(new_tags) + '\n'
    content = content.replace('</title>\n', '</title>\n' + insert_str, 1)

    if content != original:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        count += 1
        print(f"OK {mod} (+{len(new_tags)} tags)")

print(f"\nUpdated {count} files")
