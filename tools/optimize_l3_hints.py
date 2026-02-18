#!/usr/bin/env python3
"""
tools/optimize_l3_hints.py
Phase 1: Replace boilerplate L3 hints with per-question computation guidance.
Strategy: "引導到倒數第二步" — show computation steps, mask final answer with ？

Usage:
  python tools/optimize_l3_hints.py --dry-run   # preview changes
  python tools/optimize_l3_hints.py              # apply changes
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"

# ---------- module registry ----------
MODULES: dict[str, tuple[str, str | None]] = {
    "fraction-g5":                         ("bank.js", "FRACTION_G5_BANK"),
    "fraction-word-g5":                    ("bank.js", "FRACTION_WORD_G5_BANK"),
    "decimal-unit4":                       ("bank.js", "DECIMAL_UNIT4_BANK"),
    "volume-g5":                           ("bank.js", "VOLUME_G5_BANK"),
    "ratio-percent-g5":                    ("bank.js", "RATIO_PERCENT_G5_BANK"),
    "life-applications-g5":                ("bank.js", "LIFE_APPLICATIONS_G5_BANK"),
    "g5-grand-slam":                       ("bank.js", "G5_GRAND_SLAM_BANK"),
    "offline-math":                        ("bank.js", "OFFLINE_MATH_BANK"),
    "interactive-decimal-g5":              ("bank.js", "INTERACTIVE_DECIMAL_G5_BANK"),
    "interactive-g5-empire":               ("bank.js", "INTERACTIVE_G5_EMPIRE_BANK"),
    "interactive-g5-life-pack1-empire":    ("bank.js", "G5_LIFE_PACK1_BANK"),
    "interactive-g5-life-pack1plus-empire": ("bank.js", "G5_LIFE_PACK1PLUS_BANK"),
    "interactive-g5-life-pack2-empire":    ("bank.js", "G5_LIFE_PACK2_BANK"),
    "interactive-g5-life-pack2plus-empire": ("bank.js", "G5_LIFE_PACK2PLUS_BANK"),
    "interactive-g56-core-foundation":     ("g56_core_foundation.json", None),
    "exam-sprint":                         ("bank.js", "EXAM_SPRINT_BANK"),
}

# =====================================================================
# Parsing
# =====================================================================

def parse_bank_js(path: Path, var_name: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    pat = rf"window\.{re.escape(var_name)}\s*=\s*\["
    m = re.search(pat, text)
    if not m:
        raise ValueError(f"window.{var_name} not found in {path}")
    start = m.end() - 1
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError(f"Unbalanced brackets in {path}")


def parse_bank(mod: str) -> list[dict[str, Any]]:
    fn, var = MODULES[mod]
    path = DOCS / mod / fn
    if var:
        return parse_bank_js(path, var)
    return json.loads(path.read_text(encoding="utf-8"))


def write_bank(mod: str, questions: list[dict[str, Any]]) -> None:
    fn, var = MODULES[mod]
    path = DOCS / mod / fn
    body = json.dumps(questions, ensure_ascii=False, indent=2)
    if var:
        content = f"window.{var} = {body};\n"
    else:
        content = body + "\n"
    path.write_text(content, encoding="utf-8")


# =====================================================================
# Boilerplate detection
# =====================================================================

_BOILERPLATE_FRAGS = [
    "請依前面步驟完成計算",
    "最後請自行寫出答案",
    "最後自行檢查單位並寫出答案",
]


def is_boilerplate(txt: str) -> bool:
    t = txt.strip()
    return any(f in t for f in _BOILERPLATE_FRAGS)


# =====================================================================
# Step analysis helpers
# =====================================================================

_NUM_RE = re.compile(r"\d")


def has_nums(s: str) -> bool:
    return bool(_NUM_RE.search(s))


def steps_are_concrete(steps: list[str]) -> bool:
    if not steps:
        return False
    return sum(has_nums(s) for s in steps) >= max(1, len(steps) * 0.4)


# =====================================================================
# Answer masking
# =====================================================================

def mask_answer_in_step(step: str, answer: str) -> str:
    ans = answer.strip()
    if ans in step:
        idx = step.rfind(ans)
        return step[:idx] + "？" + step[idx + len(ans) :]
    if "/" in ans:
        parts = ans.split("/")
        if len(parts) == 2:
            spaced = f"{parts[0].strip()} / {parts[1].strip()}"
            if spaced in step:
                idx = step.rfind(spaced)
                return step[:idx] + "？" + step[idx + len(spaced) :]
    if ":" in ans:
        alt = ans.lstrip("0")
        if alt in step:
            idx = step.rfind(alt)
            return step[:idx] + "？" + step[idx + len(alt) :]
    return step.rstrip("。．.") + " → ？"


# =====================================================================
# L3 generators
# =====================================================================

def gen_l3_from_concrete_steps(q: dict) -> str | None:
    steps = q.get("steps", [])
    answer = str(q.get("answer", ""))
    if not steps or not answer:
        return None

    ans_str = answer.strip()
    parts: list[str] = []
    for i, step in enumerate(steps):
        if i >= len(CIRCLED):
            break
        # Mask the answer in ANY step that contains it
        if ans_str and ans_str in step:
            parts.append(f"{CIRCLED[i]} {mask_answer_in_step(step, answer)}")
        else:
            parts.append(f"{CIRCLED[i]} {step}")

    return "📐 一步步算：\n" + "\n".join(parts) + "\n算完記得回頭檢查喔！✅"


def _extract_equation(hints: list[str]) -> str | None:
    for h in hints[1:3]:
        # NOTE: do NOT include ASCII '.' in terminators — it breaks decimal numbers
        m = re.search(r"列式[：:]\s*(.+?)(?=[。，；、！？\n]|\s*$)", h)
        if m:
            eq = m.group(1).strip()
            if has_nums(eq):
                return eq
        m2 = re.search(
            r"[\d./]+\s*[×÷+\-−*]\s*[\d./]+(?:\s*[×÷+\-−*]\s*[\d./]+)*", h
        )
        if m2:
            return m2.group(0).strip()
    return None


def gen_l3_from_equation(q: dict) -> str | None:
    hints = q.get("hints", [])
    eq = _extract_equation(hints)
    if not eq:
        return None

    if "÷" in eq:
        check = "算完用「商 × 除數」反算驗證 ✅"
    elif "×" in eq or "*" in eq:
        check = "算完和估算結果比比看是否合理 ✅"
    else:
        check = "算完記得回頭檢查 ✅"

    return f"📐 動手算算看：\n① 算式：{eq}\n② 一步一步仔細算出結果\n{check}"


def gen_l3_offline_math(q: dict) -> str | None:
    ts = q.get("teacherSteps")
    if not ts:
        return None
    answer = str(q.get("answer", ""))
    ans_str = answer.strip()

    parts: list[str] = []
    idx = 0
    for step in ts:
        k = step.get("k", "")
        say = step.get("say", "")
        if k in ("concept", "formula"):
            continue
        if not say or idx >= len(CIRCLED):
            continue
        # Mask answer in ALL steps
        if ans_str and ans_str in say:
            parts.append(f"{CIRCLED[idx]} {mask_answer_in_step(say, answer)}")
        else:
            parts.append(f"{CIRCLED[idx]} {say}")
        idx += 1

    if not parts:
        return None
    return "📐 一步步算：\n" + "\n".join(parts) + "\n算完記得回頭檢查喔！✅"


def gen_l3_g56core(q: dict) -> str | None:
    steps = q.get("steps", [])
    answer = str(q.get("answer", ""))
    if not steps:
        return None
    ans_str = answer.strip()

    parts: list[str] = []
    for i, step in enumerate(steps):
        if i >= len(CIRCLED):
            break
        s = re.sub(r"^步驟\d+[：:]\s*", "", step)
        if ans_str and ans_str in s:
            s = mask_answer_in_step(s, answer)
        parts.append(f"{CIRCLED[i]} {s}")

    return "📐 一步步算：\n" + "\n".join(parts) + "\n算完記得回頭檢查喔！✅"


# ---------- kind-specific better generics ----------
_KIND_GENERICS: dict[str, str] = {
    # Fraction basics
    "simplify":     "📐 動手算：找分子分母的最大公因數，各除以它。約分後檢查還有沒有共同因數？✅",
    "add_like":     "📐 動手算：分母不變，分子相加。假分數記得化帶分數或約分。✅",
    "sub_like":     "📐 動手算：分母不變，分子相減，最後約分到最簡。✅",
    "add_unlike":   "📐 動手算：先通分（找最小公倍數），分子相加，最後約分。✅",
    "sub_unlike":   "📐 動手算：先通分（找最小公倍數），分子相減，最後約分。✅",
    "equivalent":   "📐 動手算：找出倍數，分子分母同乘（或同除）。✅",
    "mul":          "📐 動手算：分子×分子、分母×分母。能先約分就先約！✅",
    "mul_int":      "📐 動手算：整數寫成「整數/1」再乘。分子乘分子，分母不變。✅",
    "mixed_convert":"📐 動手算：帶分數→假分數：整數×分母＋分子；假分數→帶分數：用除法。✅",
    # Fraction word problems
    "fraction_of_quantity":    "📐 動手算：全體 × 分數 = 部分。先約分更快！✅",
    "fraction_of_fraction":    "📐 動手算：做兩次乘法，先算第一段再算第二段。✅",
    "remaining_after_fraction":"📐 動手算：先算用掉多少，再用全體減。注意第二次對「剩下的量」算！✅",
    "remain_then_fraction":    "📐 動手算：先算第一次剩下，再對剩下的算分數。✅",
    "reverse_fraction":        "📐 動手算：已知部分和比例→用除法反推。除以分數 = 乘以倒數！✅",
    "average_division":        "📐 動手算：總量 ÷ 份數。除以整數 = 乘以 1/整數。✅",
    "generic_fraction_word":   "📐 動手算：找出「全體」和「分數」，判斷乘還是除再列式。✅",
    # Decimal
    "d_mul_int":    "📐 動手算：先當整數乘，再數小數位數放回小數點。✅",
    "d_mul_d":      "📐 動手算：先當整數乘，兩個因數的小數位數加起來，從右數回來放小數點。✅",
    "d_div_int":    "📐 動手算：直式除法，商的小數點對齊被除數。不夠除就補 0。✅",
    "int_mul_d":    "📐 動手算：整數×小數，先當整數算再放回小數點。✅",
    "x10_shift":    "📐 動手算：×10 右移 1 格，×100 右移 2 格，÷10 左移 1 格。不夠就補 0。✅",
    "int_div_int_to_decimal": "📐 動手算：除不盡就加小數點繼續除，到整除或指定位數。✅",
    # Volume
    "rect_cm3":     "📐 動手算：長×寬×高，一步步乘。記得寫「立方公分」。✅",
    "cube_cm3":     "📐 動手算：正方體→邊長×邊長×邊長。✅",
    "cube_find_edge":"📐 動手算：哪個數字連乘三次等於體積？試 1³, 2³, 3³, 4³…✅",
    "base_area_h":  "📐 動手算：體積 = 底面積 × 高。底面積題目已給！✅",
    "rect_find_height":"📐 動手算：高 = 體積 ÷ (長×寬)。先算底面積再除。✅",
    "composite":    "📐 動手算：分成幾塊長方體，各算體積再加起來。✅",
    "composite3":   "📐 動手算：分三塊長方體，各算各的，最後加總。✅",
    "decimal_dims": "📐 動手算：帶小數的長×寬×高，用估算先想答案大概多少。✅",
    "cm3_to_m3":    "📐 動手算：1m³ = 1,000,000 cm³。把 cm³ ÷ 1,000,000。✅",
    "m3_to_cm3":    "📐 動手算：1m³ = 1,000,000 cm³。把 m³ × 1,000,000。✅",
    "mixed_units":  "📐 動手算：先統一單位（都換 cm 或 m），再算體積。✅",
    # Ratio/Percent
    "ratio_part_total":      "📐 動手算：先算總份數，再算每份多少（全體÷總份數）。✅",
    "percent_discount":      "📐 動手算：打幾折→付原價幾％。先算付費比例再乘原價。✅",
    "percent_find_part":     "📐 動手算：全體 × 百分率 = 部分。百分率換小數再乘。✅",
    "percent_find_whole":    "📐 動手算：全體 = 部分 ÷ 百分率。百分率換小數再除。✅",
    "percent_find_percent":  "📐 動手算：百分率 = 部分 ÷ 全體 × 100。先除再乘。✅",
    "percent_interest":      "📐 動手算：利息 = 本金 × 年利率 × 年數。一步步乘。✅",
    "percent_increase_decrease":"📐 動手算：先算增減量，再除以原量得百分率。✅",
    "percent_tax_service":   "📐 動手算：含稅 = 原價 × (1 + 稅率)。✅",
    "decimal_to_percent":    "📐 動手算：小數 × 100 = 百分率。小數點右移 2 格。✅",
    "fraction_to_percent":   "📐 動手算：分數先除成小數，再 × 100 = 百分率。✅",
    "percent_to_decimal":    "📐 動手算：百分率 ÷ 100 = 小數。小數點左移 2 格。✅",
    "ratio_unit_rate":       "📐 動手算：單位量 = 全部 ÷ 份數。「每一個」用除法。✅",
    "ratio_missing_to_1":    "📐 動手算：缺的比 = 總份數 − 已知份數。✅",
    "ratio_remaining":       "📐 動手算：先算已知部分，全體 − 已知 = 剩下。✅",
    "ratio_add_decimal":     "📐 動手算：先用比值算各部分的小數量，再加法。✅",
    "ratio_sub_decimal":     "📐 動手算：先用比值算各部分的小數量，再減法。✅",
    "percent_meaning":       "📐 動手算：百分率 = 每 100 份裡有幾份，X/100。✅",
    # Life applications
    "buy_many":         "📐 動手算：單價 × 數量，小心小數點！✅",
    "discount":         "📐 動手算：先算付費比例（100% − 折扣%），再乘原價。✅",
    "unit_price":       "📐 動手算：單價 = 總價 ÷ 數量。用除法！✅",
    "make_change":      "📐 動手算：找零 = 付的錢 − 總價。先算總價再減。✅",
    "shopping_two_step":"📐 動手算：先算各品項金額，再加起來或減掉。✅",
    "time_add":         "📐 動手算：先加分鐘，超過 60 進位 1 小時。60 進位不是 100！✅",
    "temperature_change":"📐 動手算：溫度差 = 末溫 − 初溫。注意正負號。✅",
    "unit_convert":     "📐 動手算：查換算關係，用乘法或除法轉換。✅",
    "area_tiling":      "📐 動手算：先算面積（長×寬），再除以每塊磁磚面積。✅",
    "perimeter_fence":  "📐 動手算：先算周長，再看圍籬用多少材料。✅",
    "volume_fill":      "📐 動手算：先算容器體積，再算裝了多少 / 還差多少。✅",
    "proportional_split":"📐 動手算：總份數 → 每份多少 → 要求那方有幾份。✅",
    "table_stats":      "📐 動手算：看表格找數字，比大小或做加減。✅",
    "fraction_remaining":"📐 動手算：全體 − 已用 = 剩餘。分數減法記得通分。✅",
    # Empire kinds
    "decimal_mul":      "📐 動手算：先當整數算，再數總共幾位小數放回小數點。✅",
    "decimal_div":      "📐 動手算：直式除法，商的小數點對齊被除數，不夠除就補 0。✅",
    "fraction_addsub":  "📐 動手算：先通分再加減，最後約分。✅",
    "fraction_mul":     "📐 動手算：分子×分子、分母×分母，能先約分就先約。✅",
    "percent_of":       "📐 動手算：百分率換分數（÷100），再乘以全體。✅",
    "volume_rect_prism":"📐 動手算：長×寬×高，一步步乘出來。✅",
    # Grand-slam kinds
    "clock_angle":      "📐 動手算：分針 = 分鐘×6°，時針 = 小時×30°+分鐘×0.5°，夾角 = |差|。✅",
    "solve_ax":         "📐 動手算：等式兩邊做同樣的事，數字移一邊，未知數留另一邊。✅",
    "solve_x_plus_a":   "📐 動手算：兩邊同時減掉那個數字，x 就出來了。✅",
    "solve_x_div_d":    "📐 動手算：兩邊同時乘回那個數字，x 就出來了。✅",
    "gcd_word":         "📐 動手算：「分成一樣大且最大」→ 最大公因數。用短除法！✅",
    "lcm_word":         "📐 動手算：「同時出現」→ 最小公倍數。用短除法！✅",
    "area_triangle":    "📐 動手算：三角形面積 = 底×高÷2。先乘再除。✅",
    "area_parallelogram":"📐 動手算：平行四邊形 = 底×高。注意用「對應的高」！✅",
    "area_trapezoid":   "📐 動手算：梯形 = (上底+下底)×高÷2。✅",
    "reciprocal":       "📐 動手算：倒數 = 分子分母互換。整數 a 的倒數是 1/a。✅",
    "prime_or_composite":"📐 動手算：試除 2、3、5、7…，有因數→合數，沒有→質數。✅",
    "displacement":     "📐 動手算：液面差 × 底面積 = 放入物體的體積。✅",
    "surface_area_cube":"📐 動手算：正方體表面積 = 6 × 邊長 × 邊長。✅",
    "surface_area_rect_prism":"📐 動手算：2×(長×寬 + 長×高 + 寬×高)。一個個算再加。✅",
    "surface_area_contact_removed":"📐 動手算：黏起來要扣 2 個接觸面，從原表面積扣掉。✅",
    "time_add_cross_day":"📐 動手算：超過 24:00 就減 24。先換成分鐘算更方便。✅",
    "time_sub_cross_day":"📐 動手算：跨日減法，先換分鐘，減完再轉回 HH:MM。✅",
    "time_multiply":    "📐 動手算：先換成同一個小單位，乘完再換回。✅",
    # Life-pack kinds
    "u1_avg_fraction":           "📐 動手算：平均 = 總量 ÷ 份數。除以整數 = 乘以倒數。✅",
    "u2_frac_addsub_life":       "📐 動手算：先通分，再加或減，最後約分。✅",
    "u3_frac_times_int":         "📐 動手算：分子×整數，分母不變，最後約分。✅",
    "u4_money_decimal_addsub":   "📐 動手算：金額對齊小數點，再加或減。✅",
    "u5_decimal_muldiv_price":   "📐 動手算：單價×數量，先當整數算再放小數點。✅",
    "u6_frac_dec_convert":       "📐 動手算：分數→小數用除法，小數→分數看位數。✅",
    "u7_discount_percent":       "📐 動手算：打 N 折 = 付原價的 N/10。折後價 = 原價 × 折扣倍率。✅",
    "u8_ratio_recipe":           "📐 動手算：先算總份數，算每份多少，再乘要求份數。✅",
    "u9_unit_convert_decimal":   "📐 動手算：查換算關係，用乘法或除法。✅",
    "u10_rate_time_distance":    "📐 動手算：速率×時間=距離。看求哪個就用除法反推。✅",
}

_FALLBACK_L3 = "📐 動手算算看：用提示②的算式，一步一步仔細算出來，算完記得回頭檢查 ✅"


# =====================================================================
# Main generator
# =====================================================================

def generate_l3(q: dict, mod: str) -> str:
    steps = q.get("steps", [])

    if mod == "offline-math":
        r = gen_l3_offline_math(q)
        if r:
            return r
    if mod == "interactive-g56-core-foundation":
        r = gen_l3_g56core(q)
        if r:
            return r

    if steps_are_concrete(steps):
        r = gen_l3_from_concrete_steps(q)
        if r:
            return r

    r = gen_l3_from_equation(q)
    if r:
        return r

    kind = q.get("kind", "")
    for k in [kind, kind.split("｜")[0].strip()]:
        if k in _KIND_GENERICS:
            return _KIND_GENERICS[k]

    return _FALLBACK_L3


# =====================================================================
# Module optimizer
# =====================================================================

def optimize_module(mod: str, dry_run: bool = False) -> tuple[int, int]:
    questions = parse_bank(mod)
    changed = 0

    for q in questions:
        hints = q.get("hints", [])
        if not hints:
            continue
        last = len(hints) - 1
        if not is_boilerplate(hints[last]):
            continue
        new_l3 = generate_l3(q, mod)
        hints[last] = new_l3
        changed += 1

    if not dry_run and changed > 0:
        write_bank(mod, questions)

    return len(questions), changed


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    print("=" * 64)
    print("  L3 Hint Optimizer — Phase 1: Kill Boilerplate")
    print("  Strategy: 引導到倒數第二步 (guide to penultimate step)")
    print("=" * 64)
    if dry_run:
        print("  [DRY RUN — no files will be modified]\n")
    else:
        print()

    total_q = 0
    total_changed = 0

    for mod in MODULES:
        try:
            nq, nc = optimize_module(mod, dry_run)
            pct = nc / nq * 100 if nq else 0
            icon = "✅" if nc > 0 else "⏭️ "
            print(f"  {icon} {mod:<46} {nc:>4}/{nq:>4} ({pct:5.1f}%)")
            total_q += nq
            total_changed += nc
        except Exception as e:
            print(f"  ❌ {mod}: {e}")

    print(f"\n{'=' * 64}")
    print(f"  TOTAL: {total_changed}/{total_q} L3 hints optimized")
    if not dry_run and total_changed:
        print("  Files updated. Run cross-validation before committing!")
    print("=" * 64)


if __name__ == "__main__":
    main()
