"""Generate a single-page learning map from all offline banks.

Outputs:
- docs/learning-map/index.html
- dist_ai_math_web_pages/docs/learning-map/index.html

The page aggregates per-module and per-kind:
- core concepts (from `core` and hint lines)
- common steps
- difficulty distribution
- a sample question

Run:
  python scripts/generate_learning_map.py
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIST = ROOT / "dist_ai_math_web_pages" / "docs"


BANK_ASSIGN_RE = re.compile(r"^\s*window\.([A-Za-z0-9_]+)\s*=\s*\[", re.MULTILINE)

MODULE_ALIAS_ZH: dict[str, str] = {
    "interactive-g5-empire": "五年級帝國闖關",
    "g5-grand-slam": "大單位換算大滿貫",
    "life-applications-g5": "小五生活應用題",
    "decimal-unit4": "五下第4單元｜小數",
    "offline-math": "離線數學練習",
}

KIND_ALIAS_ZH: dict[str, str] = {
    "d_mul_int": "小數×整數（買多份）",
    "int_mul_d": "整數×小數（比例/折扣）",
    "d_mul_d": "小數×小數（面積/單價）",
    "d_div_int": "小數÷整數（平均分）",
    "int_div_int_to_decimal": "整數÷整數（商是小數）",
    "x10_shift": "小數點位移（×10/÷10）",
}

FORMAT_KEY_ZH: dict[str, str] = {
    "symbolic_or_equation": "等式/符號",
    "unknown_format": "其他格式",
    "numeric_expr": "數值算式",
    "multi_space_numbers": "多值(空格)",
}


def _load_audit_report() -> dict[str, Any] | None:
    """Load answer-format audit JSON written under docs/learning-map/.

    This keeps the learning-map page and the audit tooling consistent.
    """

    p = DOCS / "learning-map" / "audit_answer_formats.json"
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _render_audit_block(report: dict[str, Any] | None) -> str:
    if not report:
        return (
            '<div class="box">'
            '<b>判題覆蓋率 / 答案格式</b><br/>'
            '<span class="k">尚未找到 audit_answer_formats.json（可執行 scripts/audit_bank_answer_formats.py 產生報表）</span>'
            '</div>'
        )

    totals = report.get("totals") or {}
    per_module = report.get("per_module") or {}

    def g(key: str) -> int:
        try:
            return int(totals.get(key, 0))
        except Exception:
            return 0

    def pill(label: str, q: str, cls: str = "pill") -> str:
        return f'<button class="{cls} clickable" type="button" data-set-q="{_html_escape(q)}">{_html_escape(label)}</button>'

    base_items = sum(
        g(k)
        for k in (
            "plain_number_or_fraction",
            "numeric_expr",
            "symbolic_or_equation",
            "unknown_format",
            "json_payload",
            "empty",
        )
    )

    # Focus modules: non-trivial formats / symbolic.
    focus: list[tuple[str, int, dict[str, Any]]] = []
    for mid, c in per_module.items():
        if not isinstance(c, dict):
            continue
        score = 0
        for key in ("symbolic_or_equation", "unknown_format", "numeric_expr", "json_payload", "empty"):
            try:
                score += int(c.get(key, 0))
            except Exception:
                pass
        if score:
            focus.append((str(mid), score, c))
    focus.sort(key=lambda x: (-x[1], x[0]))

    focus_lines = []
    for mid, _, c in focus[:8]:
        mid_zh = MODULE_ALIAS_ZH.get(mid, mid)
        parts = []
        for key in ("symbolic_or_equation", "unknown_format", "numeric_expr"):
            if int(c.get(key, 0) or 0):
                parts.append(f"{FORMAT_KEY_ZH.get(key, key)}:{int(c[key])}")
        if int(c.get("multi_space_numbers", 0) or 0):
            parts.append(f"{FORMAT_KEY_ZH['multi_space_numbers']}:{int(c['multi_space_numbers'])}")
        qterm = mid
        focus_lines.append(
            "".join(
                [
                    "<li>",
                    f'<button class="k linklike" type="button" data-set-q="{_html_escape(qterm)}">{_html_escape(mid_zh)}</button>',
                    " — ",
                    _html_escape(" / ".join(parts) or "需特殊支援"),
                    "</li>",
                ]
            )
        )

    focus_html = "".join(focus_lines) if focus_lines else "<li>（目前題庫皆為純數值/分數格式）</li>"

    return "\n".join(
        [
            '<div class="box">',
            '  <b>判題覆蓋率 / 答案格式（由題庫自動掃描）</b>',
            '  <div class="meta" style="margin-top:6px;">',
            f'    <span class="pill lvl">總題數 {base_items}</span>',
            f'    {pill(f"分數/數值 {g("plain_number_or_fraction")}", "fraction")}',
            f'    {pill(f"等式/符號 {g("symbolic_or_equation")}", "=")}',
            f'    {pill(f"其他格式 {g("unknown_format")}", ":")}',
            f'    {pill(f"多值(空格) {g("multi_space_numbers")}", "LCM")}',
            '  </div>',
            '  <div class="k" style="margin-top:6px;">',
            '    規則：小學算術優先用分數格式正規化（Fraction）；遇到代數/方程類才啟用安全版 SymPy（Guarded SymPy）。',
            '  </div>',
            '  <div style="margin-top:10px;">',
            '    <b>需要特殊判題/格式支援的模組（前 8）</b>',
            '    <ul style="margin-top:6px;">',
            f"      {focus_html}",
            '    </ul>',
            '    <div class="hint">點上面的按鈕／模組名稱可自動套用左側搜尋。</div>',
            '  </div>',
            '</div>',
        ]
    )


def _load_bank_items(bank_js_path: Path) -> tuple[str | None, list[dict[str, Any]]]:
    text = bank_js_path.read_text(encoding="utf-8")

    m = BANK_ASSIGN_RE.search(text)
    bank_var = m.group(1) if m else None

    # Avoid matching brackets in header comments like "[...]".
    if m:
        start = m.end() - 1  # points to the '['
    else:
        start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < 0 or end <= start:
        raise ValueError(f"Cannot locate JSON array assignment in {bank_js_path}")

    payload = text[start : end + 1]
    try:
        items = json.loads(payload)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse bank JSON array in {bank_js_path}: {e}") from e

    if not isinstance(items, list):
        raise ValueError(f"Bank payload is not a list in {bank_js_path}")

    out: list[dict[str, Any]] = []
    for it in items:
        if isinstance(it, dict):
            out.append(it)
    return bank_var, out


def _extract_concepts_from_hints(hints: list[str]) -> list[str]:
    concepts: list[str] = []
    for h in hints:
        if not h:
            continue
        for raw in str(h).splitlines():
            line = raw.strip()
            if not line:
                continue
            for prefix in ("觀念：", "規則：", "重點：", "提醒："):
                if line.startswith(prefix):
                    concepts.append(line.split("：", 1)[1].strip())
                    break
            else:
                m = re.search(r"觀念[:：]\s*(.+)$", line)
                if m:
                    concepts.append(m.group(1).strip())
                    continue
                if line.startswith("提示 1｜"):
                    txt = line.split("｜", 1)[1].strip() if "｜" in line else line
                    txt = re.sub(r"^先懂觀念[:：]\s*", "", txt)
                    if txt:
                        concepts.append(txt)
    return concepts


def _norm_space(s: str) -> str:
    return re.sub(r"\\s+", " ", (s or "").strip())


def _module_display(module_id: str, fallback_title: str) -> str:
    alias = MODULE_ALIAS_ZH.get(module_id)
    if alias:
        return alias
    title = _norm_space(fallback_title)
    return title or module_id


def _kind_display(kind: str) -> str:
    if kind in KIND_ALIAS_ZH:
        return KIND_ALIAS_ZH[kind]
    token_map = {
        "add": "加",
        "sub": "減",
        "mul": "乘",
        "div": "除",
        "int": "整數",
        "decimal": "小數",
        "fraction": "分數",
        "ratio": "比率",
        "percent": "百分率",
        "word": "應用",
        "time": "時間",
        "area": "面積",
        "volume": "體積",
        "speed": "速率",
        "distance": "距離",
        "money": "金額",
        "shift": "位移",
        "equation": "方程",
    }
    parts = [p for p in str(kind).split("_") if p]
    zh_parts = [token_map.get(p, p) for p in parts]
    text = "・".join(zh_parts)
    return text if text else kind


@dataclass
class KindAgg:
    count: int
    difficulties: Counter[str]
    concepts: Counter[str]
    steps: Counter[str]
    tags: Counter[str]
    sample_question: str
    sample_answer: str


@dataclass
class ModuleAgg:
    module_id: str
    module_title: str
    bank_var: str | None
    kinds: dict[str, KindAgg]


def _build_aggregates() -> list[ModuleAgg]:
    bank_paths = sorted(p for p in DOCS.rglob("bank.js") if p.is_file())

    modules: dict[str, dict[str, Any]] = {}

    for p in bank_paths:
        module_id = p.parent.relative_to(DOCS).as_posix().rstrip("/")
        try:
            bank_var, items = _load_bank_items(p)
        except Exception as e:
            print(f"WARN: skip non-JSON bank {p.as_posix()}: {e}")
            continue
        if not items:
            continue

        module_title = _norm_space(str(items[0].get("topic") or module_id))

        kinds: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "difficulties": Counter(),
            "concepts": Counter(),
            "steps": Counter(),
            "tags": Counter(),
            "sample_question": "",
            "sample_answer": "",
        })

        for it in items:
            kind = _norm_space(str(it.get("kind") or "(unknown)") )
            if not kind:
                kind = "(unknown)"

            agg = kinds[kind]
            agg["count"] += 1

            diff = _norm_space(str(it.get("difficulty") or ""))
            if diff:
                agg["difficulties"][diff] += 1

            for c in (it.get("core") or []):
                c2 = _norm_space(str(c))
                if c2:
                    agg["concepts"][c2] += 1

            hints = it.get("hints") or []
            if isinstance(hints, list):
                for c in _extract_concepts_from_hints([str(x) for x in hints]):
                    c2 = _norm_space(c)
                    if c2:
                        agg["concepts"][c2] += 1

            steps = it.get("steps") or []
            if isinstance(steps, list):
                for s in steps:
                    s2 = _norm_space(str(s))
                    if s2:
                        agg["steps"][s2] += 1

            tags = it.get("tags") or []
            if isinstance(tags, list):
                for t in tags:
                    t2 = _norm_space(str(t))
                    if t2:
                        agg["tags"][t2] += 1

            if not agg["sample_question"]:
                agg["sample_question"] = _norm_space(str(it.get("question") or ""))
                agg["sample_answer"] = _norm_space(str(it.get("answer") or ""))

        modules[module_id] = {
            "module_id": module_id,
            "module_title": module_title,
            "bank_var": bank_var,
            "kinds": kinds,
        }

    out: list[ModuleAgg] = []
    for module_id in sorted(modules.keys()):
        m = modules[module_id]
        kinds_out: dict[str, KindAgg] = {}
        for kind_name in sorted(m["kinds"].keys()):
            d = m["kinds"][kind_name]
            kinds_out[kind_name] = KindAgg(
                count=int(d["count"]),
                difficulties=d["difficulties"],
                concepts=d["concepts"],
                steps=d["steps"],
                tags=d["tags"],
                sample_question=str(d["sample_question"]),
                sample_answer=str(d["sample_answer"]),
            )

        out.append(
            ModuleAgg(
                module_id=m["module_id"],
                module_title=m["module_title"],
                bank_var=m["bank_var"],
                kinds=kinds_out,
            )
        )
    return out


def _pill(label: str, cls: str = "pill") -> str:
    return f'<span class="{cls}">{label}</span>'


def _html_escape(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _render_html(mods: list[ModuleAgg]) -> str:
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    audit_block = _render_audit_block(_load_audit_report())

    # Build TOC entries
    toc_items: list[str] = []
    for m in mods:
        total = sum(k.count for k in m.kinds.values())
        display_title = _module_display(m.module_id, m.module_title)
        toc_items.append(
            f'<li><a href="#m_{_html_escape(m.module_id)}">{_html_escape(display_title)} <span class="k">({total} 題 / {len(m.kinds)} 題型)</span></a></li>'
        )

    # Render sections
    sections: list[str] = []
    for m in mods:
        total = sum(k.count for k in m.kinds.values())
        display_title = _module_display(m.module_id, m.module_title)
        keywords_module = " ".join(
            [
                m.module_id,
                display_title,
                m.module_title,
                m.bank_var or "",
            ]
        )

        header_meta = (
            f'<div class="meta">'
            f'{_pill("模組", "pill lvl")}'
            f'{_pill(display_title)}'
            f'{_pill(f"{total} 題")}'
            f'{_pill(f"{len(m.kinds)} 題型")}'
            f'</div>'
        )

        details_blocks: list[str] = []
        for kind_name, agg in m.kinds.items():
            top_concepts = [c for c, _ in agg.concepts.most_common(6)]
            top_steps = [s for s, _ in agg.steps.most_common(6)]
            top_tags = [t for t, _ in agg.tags.most_common(8)]

            diff_parts = []
            diff_zh = {"easy": "簡單", "medium": "中等", "hard": "挑戰"}
            for label in ("easy", "medium", "hard"):
                if agg.difficulties.get(label):
                    diff_parts.append(f"{diff_zh.get(label, label)}:{agg.difficulties[label]}")
            diff_text = " / ".join(diff_parts) if diff_parts else "-"

            kw = " ".join(
                [
                    keywords_module,
                    kind_name,
                    " ".join(top_concepts),
                    " ".join(top_steps),
                    " ".join(top_tags),
                ]
            )

            details_blocks.append(
                "\n".join(
                    [
                        f'<details data-keywords="{_html_escape(kw)}">',
                        f'  <summary>{_html_escape(_kind_display(kind_name))} <span class="pills">'
                        f'{_pill(f"{agg.count} 題", "pill lvl mid")}'
                        f'{_pill(f"難度 {diff_text}", "pill")}</span></summary>',
                        '  <div class="grid2">',
                        '    <div>',
                        '      <div class="meta"><span class="pill lvl">核心觀念（常見）</span></div>',
                        '      <ul>'
                        + "\n".join(
                            f"        <li>{_html_escape(x)}</li>" for x in (top_concepts or ["（題庫未提供 core/觀念標註，請以提示文字為主）"])
                        )
                        + "\n      </ul>",
                        '      <div class="meta"><span class="pill lvl mid">常見步驟</span></div>',
                        '      <ul>'
                        + "\n".join(
                            f"        <li>{_html_escape(x)}</li>" for x in (top_steps or ["（無 steps）"])
                        )
                        + "\n      </ul>",
                        '    </div>',
                        '    <div>',
                        '      <div class="meta"><span class="pill lvl mid">常用標籤</span></div>',
                        '      <div class="chips">'
                        + "\n".join(f"        <span class=\"chip\">{_html_escape(t)}</span>" for t in (top_tags or ["（無 tags）"]))
                        + "\n      </div>",
                        '      <div class="meta" style="margin-top:10px;"><span class="pill lvl deep">題目樣例</span></div>',
                        f'      <div class="box">{_html_escape(agg.sample_question) if agg.sample_question else "（無）"}</div>',
                        f'      <div class="k">參考答案：{_html_escape(agg.sample_answer) if agg.sample_answer else "（無）"}</div>',
                        '    </div>',
                        '  </div>',
                        '</details>',
                    ]
                )
            )

        sections.append(
            "\n".join(
                [
                    f'<section id="m_{_html_escape(m.module_id)}" data-keywords="{_html_escape(keywords_module)}">',
                    f'  <h2>{_html_escape(display_title)}</h2>',
                    f'  {header_meta}',
                    "  " + "\n  ".join(details_blocks),
                    '</section>',
                ]
            )
        )

        toc_html = "\n      ".join(toc_items)
        sections_html = "\n\n    ".join(sections)

        template = """<!doctype html>
<html lang="zh-Hant">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>題型觀念地圖｜AI Math Web</title>
    <style>
        :root{
            --bg:#0b0f14; --panel:#101826; --panel2:#0f1623; --text:#e8eef7;
            --muted:#a8b3c5; --line:#243046; --accent:#7dd3fc; --accent2:#34d399;
            --warn:#fbbf24; --bad:#fb7185;
            --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        }
        *{box-sizing:border-box}
        body{margin:0; font-family:var(--sans); background:var(--bg); color:var(--text); line-height:1.6}
        a{color:var(--accent); text-decoration:none}
        a:hover{text-decoration:underline}
        header{padding:24px 18px 14px; border-bottom:1px solid var(--line); background:linear-gradient(180deg, rgba(125,211,252,0.08), rgba(0,0,0,0))}
        header h1{margin:0 0 6px; font-size:20px}
        header .sub{color:var(--muted); font-size:13px}
        .wrap{display:grid; grid-template-columns: 340px 1fr; gap:16px; padding:16px; max-width:1280px; margin:0 auto}
        @media (max-width: 980px){ .wrap{grid-template-columns:1fr} }
        .card{background:var(--panel); border:1px solid var(--line); border-radius:14px; box-shadow: 0 10px 30px rgba(0,0,0,0.25)}
        .toc{padding:14px 14px 10px; position:sticky; top:12px; height:fit-content}
        .toc h2{margin:0 0 10px; font-size:14px; letter-spacing:.3px; color:var(--muted)}
        .toc .search{display:flex; gap:8px; align-items:center; margin-bottom:10px}
        .toc input{
            width:100%; padding:10px 10px; border-radius:10px; border:1px solid var(--line);
            background:var(--panel2); color:var(--text); outline:none;
        }
        .toc .hint{font-size:12px; color:var(--muted); margin:6px 0 0}
        .toc ul{list-style:none; padding:0; margin:10px 0 0; max-height: calc(100vh - 170px); overflow:auto}
        .toc li{margin:6px 0}
        .toc a{display:block; padding:6px 8px; border-radius:10px}
        .toc a:hover{background:rgba(125,211,252,0.08)}
        main{padding:16px}
        section{margin:0 0 18px}
        section > h2{margin:0 0 8px; font-size:16px; border-left:4px solid var(--accent); padding-left:10px}
        .meta{font-size:12px; color:var(--muted); margin:6px 0 0}
        .pill{display:inline-block; font-size:11px; padding:2px 8px; border-radius:999px; border:1px solid var(--line); color:var(--muted); margin-right:6px; margin-bottom:6px}
        button.pill{background:transparent; cursor:pointer}
        .clickable:hover{background:rgba(125,211,252,0.08)}
        .linklike{border:none; padding:0; background:transparent; text-decoration:underline; color:var(--accent); cursor:pointer}
        .lvl{border-color:rgba(125,211,252,0.35); color:var(--accent)}
        .lvl.mid{border-color:rgba(52,211,153,0.35); color:var(--accent2)}
        .lvl.deep{border-color:rgba(251,113,133,0.35); color:var(--bad)}
        details{background:var(--panel2); border:1px solid var(--line); border-radius:12px; padding:10px 12px; margin:10px 0}
        details summary{cursor:pointer; font-weight:600}
        details summary .pills{margin-left:8px}
        .grid2{display:grid; grid-template-columns: 1fr 1fr; gap:12px}
        @media (max-width: 980px){ .grid2{grid-template-columns:1fr} }
        ul{margin:8px 0 0 18px}
        li{margin:6px 0}
        .k{font-family:var(--mono); font-size:12px; color:var(--muted)}
        .box{padding:10px 12px; border:1px dashed rgba(125,211,252,0.35); border-radius:12px; background:rgba(125,211,252,0.06); margin:10px 0}
        .chips{display:flex; flex-wrap:wrap; gap:6px; margin-top:8px}
        .chip{font-size:11px; padding:3px 8px; border-radius:999px; border:1px solid rgba(125,211,252,0.25); background:rgba(125,211,252,0.08); color:var(--accent)}
        .footer{padding:12px 16px; border-top:1px solid var(--line); color:var(--muted); font-size:12px}
    </style>
</head>

<body>
<header>
    <div style="max-width:1280px;margin:0 auto;">
        <h1>題型觀念地圖（提示 / 題型 / 核心觀念快速摘要）</h1>
        <div class="sub">
            來源：自動掃描 <span class="k">docs/**/bank.js</span>，彙整每個模組的 <b>題型</b>、<b>常見觀念</b>、<b>步驟要點</b> 與 <b>題數/難度分布</b>。<br/>
            使用方式：左側搜尋（建議中文關鍵字）→ 右側展開題型細節。<br/>
            生成時間：__GEN_TIME__
        </div>
        <div style="margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;">
            <a class="pill lvl" href="../">回首頁</a>
            <a class="pill lvl mid" href="#top">回到頂部</a>
        </div>
    </div>
</header>

<div class="wrap" id="top">
    <aside class="card toc">
        <h2>目錄 / 搜尋</h2>
        <div class="search">
            <input id="q" placeholder="輸入關鍵字，例如：通分、約分、折扣、小數點移位、平均分配…" />
        </div>
        <div class="hint">提示：可用「題型名稱」或「觀念句子」搜尋，例如：小數點移動、平均分配、百分率。</div>
        <ul id="toc">
            __TOC__
        </ul>
    </aside>

    <main class="card">
        <div class="box">
            <b>這頁適合怎麼用？</b>
            <ul>
                <li>考前 10 分鐘：用搜尋找出弱點（例如「通分」「補 0」「折扣」「速率」）。</li>
                <li>做題卡住：看同一題型的「常見步驟」與「核心觀念」。</li>
                <li>教學備課：用題型統計抓出出題面向是否齊全。</li>
            </ul>
        </div>

        __AUDIT__

        __SECTIONS__

        <div class="footer">
            本頁由 <span class="k">scripts/generate_learning_map.py</span> 自動產生；若你更新題庫（bank.js），請重新執行腳本以同步內容。
        </div>
    </main>
</div>

<script>
(function(){
    const q = document.getElementById('q');
    const sections = Array.from(document.querySelectorAll('main section'));
    const detailsList = Array.from(document.querySelectorAll('main details'));
    const tocLinks = Array.from(document.querySelectorAll('#toc a'));
    const setQButtons = Array.from(document.querySelectorAll('[data-set-q]'));

    function norm(s){ return (s||'').toLowerCase(); }

    function apply(){
        const term = norm(q.value.trim());

        // Filter details first
        detailsList.forEach(d=>{
            const keys = norm(d.getAttribute('data-keywords') || '');
            const text = norm(d.innerText || '');
            const hit = !term || keys.includes(term) || text.includes(term);
            d.style.display = hit ? '' : 'none';
        });

        // Hide section if it has no visible details and term is non-empty
        sections.forEach(sec=>{
            if (!term){ sec.style.display = ''; return; }
            const visibleDetails = Array.from(sec.querySelectorAll('details')).some(x=>x.style.display !== 'none');
            sec.style.display = visibleDetails ? '' : 'none';
        });

        // TOC sync
        tocLinks.forEach(a=>{
            const id = a.getAttribute('href').slice(1);
            const sec = document.getElementById(id);
            const visible = sec && sec.style.display !== 'none';
            a.parentElement.style.display = visible ? '' : 'none';
        });
    }

    q.addEventListener('input', apply);

    setQButtons.forEach(btn=>{
        btn.addEventListener('click', ()=>{
            const term = btn.getAttribute('data-set-q') || '';
            q.value = term;
            apply();
            q.focus();
        });
    });
    apply();
})();
</script>
</body>
</html>
"""

        return (
                template.replace("__GEN_TIME__", gen_time)
                .replace("__TOC__", toc_html)
                .replace("__SECTIONS__", sections_html)
            .replace("__AUDIT__", audit_block)
        )


def _write_output(html: str) -> None:
    rel = Path("learning-map") / "index.html"
    for base in (DOCS, DIST):
        out_path = base / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")


def main() -> int:
    mods = _build_aggregates()
    if not mods:
        raise SystemExit("No banks found under docs/**/bank.js")

    html = _render_html(mods)
    _write_output(html)
    print(f"OK: generated learning map for {len(mods)} modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
