import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT_JS = ROOT / "docs" / "life-applications-g5" / "bank.js"

random.seed(20260203)
getcontext().prec = 28


def _strip_trailing_zeros(s: str) -> str:
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def fmt_decimal(d: Decimal) -> str:
    return _strip_trailing_zeros(format(d, "f"))


def fmt_decimal_from_fraction(fr: Fraction) -> str:
    d = Decimal(fr.numerator) / Decimal(fr.denominator)
    return fmt_decimal(d)


def fmt_money2(x: Decimal) -> str:
    # keep 2 decimals for money answer, but strip if .00
    s = format(x.quantize(Decimal("0.01")), "f")
    return _strip_trailing_zeros(s)


def fmt_fraction(fr: Fraction) -> str:
    fr = Fraction(fr.numerator, fr.denominator)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def hhmm(h: int, m: int) -> str:
    h = h % 24
    m = m % 60
    return f"{h:02d}:{m:02d}"


def add_minutes(t: str, minutes: int) -> str:
    hh, mm = t.split(":")
    base = datetime(2026, 2, 3, int(hh), int(mm))
    out = base + timedelta(minutes=minutes)
    return hhmm(out.hour, out.minute)


@dataclass(frozen=True)
class Q:
    id: str
    kind: str
    difficulty: str
    question: str
    answer: str
    answer_mode: str
    hints: List[str]
    steps: List[str]
    meta: Dict[str, Any]
    explanation: str


TOPIC = "國小五年級｜生活應用題（講義+練習）"


def q_buy_many(i: int) -> Q:
    unit = random.choice(["瓶", "包", "本", "盒彩", "顆", "支", "罐", "條"])
    item = random.choice(["果汁", "餅乾", "筆記本", "巧克力", "牛奶", "麵包", "果凍", "原子筆", "橡皮擦", "酸奶"])
    price = Decimal(random.randint(85, 650)) / Decimal(10)  # 8.5 ~ 65.0
    qty = random.randint(2, 12)
    total = price * Decimal(qty)

    question = f"（買多份）{item} 每{unit} {fmt_money2(price)} 元，買 {qty} {unit}，一共多少元？（可寫小數）"
    answer = fmt_money2(total)

    hints = [
        "觀念：同一個單價買很多份 → 用乘法。",
        f"列式：{fmt_money2(price)} × {qty}。先估算：{qty} 份，所以答案一定比 {fmt_money2(price)} 大。",
        "Level 3｜步驟\n"
        f"1) 列式：{fmt_money2(price)}×{qty}\n"
        "2) 先當整數算，再放回小數點（或直接用乘法計算）\n"
        f"3) 得到：{answer} 元\n"
        "4) 檢查：乘的是 >1 的整數，答案應該變大。",
    ]

    steps = [
        "同單價多份 → 乘法",
        f"列式：{fmt_money2(price)}×{qty}",
        f"計算得到 {answer}",
        "寫上單位：元",
    ]

    return Q(
        id=f"la5_buy_{i:03d}",
        kind="buy_many",
        difficulty="easy",
        question=question,
        answer=answer,
        answer_mode="money2",
        hints=hints,
        steps=steps,
        meta={"unit": "元"},
        explanation=f"總價 = 單價×數量 = {fmt_money2(price)}×{qty} = {answer}（元）。",
    )


def q_discount(i: int) -> Q:
    item = random.choice(["外套", "球鞋", "背包", "文具組", "玩具", "書本", "帽子", "水壺"])
    price = Decimal(random.randrange(80, 505, 5))
    off = random.choice([5, 10, 15, 20, 25, 30, 35, 40, 45])
    pay_rate = Decimal(100 - off) / Decimal(100)
    pay = price * pay_rate

    question = f"（打折）一個{item}原價 {fmt_money2(price)} 元，打 {off}% 折扣，折扣後要付多少元？（可寫小數）"
    answer = fmt_money2(pay)

    hints = [
        "觀念：打折就是『付原價的幾%』。",
        f"方法：先算要付的百分率：100%−{off}% = {100-off}%。再用 原價×{100-off}% 。",
        "Level 3｜步驟\n"
        f"1) 付費比例：{100-off}% = {fmt_decimal(pay_rate)}\n"
        f"2) 列式：{fmt_money2(price)}×{fmt_decimal(pay_rate)}\n"
        f"3) 得到：{answer} 元",
    ]

    steps = [
        "付費比例 = 1 − 折扣%",
        "原價 × 付費比例",
        "金額取到小數點後 2 位（或題目允許可省略尾端 0）",
    ]

    return Q(
        id=f"la5_disc_{i:03d}",
        kind="discount",
        difficulty="easy",
        question=question,
        answer=answer,
        answer_mode="money2",
        hints=hints,
        steps=steps,
        meta={"unit": "元"},
        explanation=f"付 {100-off}% = {fmt_decimal(pay_rate)}；所以 {fmt_money2(price)}×{fmt_decimal(pay_rate)}={answer}（元）。",
    )


def q_unit_price(i: int) -> Q:
    qty = random.randint(3, 15)
    unit = random.choice(["瓶", "盒", "支", "包", "本", "個"])
    item = random.choice(["礦泉水", "牛奶", "餅乾", "鉛筆", "橡皮擦", "筆記本", "果汁"])
    price = Decimal(random.randint(40, 320)) / Decimal(10)  # 4.0 ~ 32.0
    total = price * Decimal(qty)

    question = f"（單價）買 {qty} {unit}{item} 一共 {fmt_money2(total)} 元，平均每{unit}多少元？"
    answer = fmt_money2(price)

    hints = [
        "觀念：平均每一份多少 → 用除法（總量 ÷ 份數）。",
        f"列式：{fmt_money2(total)} ÷ {qty}。",
        "Level 3｜步驟\n"
        f"1) 列式：{fmt_money2(total)}÷{qty}\n"
        f"2) 計算得到：{answer} 元/每{unit}",
    ]

    steps = [
        "平均 = 總價 ÷ 數量",
        f"{fmt_money2(total)} ÷ {qty}",
        f"得到 {answer}",
    ]

    return Q(
        id=f"la5_unit_{i:03d}",
        kind="unit_price",
        difficulty="easy",
        question=question,
        answer=answer,
        answer_mode="money2",
        hints=hints,
        steps=steps,
        meta={"unit": f"元/每{unit}"},
        explanation=f"平均單價 = {fmt_money2(total)}÷{qty} = {answer}（元/每{unit}）。",
    )


def q_time_add(i: int) -> Q:
    start_h = random.randint(6, 20)
    start_m = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
    dur = random.choice([25, 35, 45, 55, 65, 75, 90])

    start = hhmm(start_h, start_m)
    end = add_minutes(start, dur)

    question = f"（時間）小明在 {start} 開始寫作業，寫了 {dur} 分鐘，幾點完成？（用 HH:MM）"

    hints = [
        "觀念：時間計算先把『分鐘』加到『分鐘』，超過 60 要進位到小時。",
        f"列式：{start} + {dur} 分鐘。先加分鐘，不夠就進位。",
        "Level 3｜步驟\n"
        f"1) {start} 的分鐘 + {dur} 分鐘\n"
        "2) 若分鐘 ≥ 60，就 +1 小時，分鐘 −60\n"
        f"3) 得到：{end}",
    ]

    steps = [
        "把分鐘相加",
        "超過 60 分鐘要進位",
        f"得到結束時間 {end}",
    ]

    return Q(
        id=f"la5_time_{i:03d}",
        kind="time_add",
        difficulty="easy",
        question=question,
        answer=end,
        answer_mode="hhmm",
        hints=hints,
        steps=steps,
        meta={"unit": "時間"},
        explanation=f"從 {start} 起算 {dur} 分鐘，進位後得到 {end}。",
    )


def q_unit_convert(i: int) -> Q:
    mode = random.choice(["L_to_mL", "kg_to_g", "m_to_cm"])
    if mode == "L_to_mL":
        x = Decimal(random.randint(1, 50)) / Decimal(10)  # 0.1 ~ 5.0
        ans = int((x * Decimal(1000)).to_integral_value())
        question = f"（單位換算）{fmt_decimal(x)} 公升 = 多少毫升？（只寫數字）"
        hints = [
            "觀念：1 公升 = 1000 毫升。",
            f"列式：{fmt_decimal(x)} × 1000。",
            f"Level 3｜計算：{fmt_decimal(x)}×1000 = {ans}（毫升）。",
        ]
        steps = ["1 L = 1000 mL", "乘 1000", f"得到 {ans}"]
        return Q(
            id=f"la5_ucv_{i:03d}",
            kind="unit_convert",
            difficulty="easy",
            question=question,
            answer=str(ans),
            answer_mode="number",
            hints=hints,
            steps=steps,
            meta={"unit": "毫升"},
            explanation=f"{fmt_decimal(x)} 公升 = {ans} 毫升。",
        )

    if mode == "kg_to_g":
        x = Decimal(random.randint(1, 50)) / Decimal(10)  # 0.1 ~ 5.0
        ans = int((x * Decimal(1000)).to_integral_value())
        question = f"（單位換算）{fmt_decimal(x)} 公斤 = 多少公克？（只寫數字）"
        hints = [
            "觀念：1 公斤 = 1000 公克。",
            f"列式：{fmt_decimal(x)} × 1000。",
            f"Level 3｜計算：{fmt_decimal(x)}×1000 = {ans}（公克）。",
        ]
        steps = ["1 kg = 1000 g", "乘 1000", f"得到 {ans}"]
        return Q(
            id=f"la5_ucv_{i:03d}",
            kind="unit_convert",
            difficulty="easy",
            question=question,
            answer=str(ans),
            answer_mode="number",
            hints=hints,
            steps=steps,
            meta={"unit": "公克"},
            explanation=f"{fmt_decimal(x)} 公斤 = {ans} 公克。",
        )

    # m_to_cm
    x = Decimal(random.randint(1, 300)) / Decimal(100)  # 0.01 ~ 3.00
    ans = int((x * Decimal(100)).to_integral_value())
    question = f"（單位換算）{fmt_decimal(x)} 公尺 = 多少公分？（只寫數字）"
    hints = [
        "觀念：1 公尺 = 100 公分。",
        f"列式：{fmt_decimal(x)} × 100。",
        f"Level 3｜計算：{fmt_decimal(x)}×100 = {ans}（公分）。",
    ]
    steps = ["1 m = 100 cm", "乘 100", f"得到 {ans}"]
    return Q(
        id=f"la5_ucv_{i:03d}",
        kind="unit_convert",
        difficulty="easy",
        question=question,
        answer=str(ans),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "公分"},
        explanation=f"{fmt_decimal(x)} 公尺 = {ans} 公分。",
    )


def q_fraction_remaining(i: int) -> Q:
    thing = random.choice(["繩子", "緞帶", "布條", "木條"])
    whole = random.randint(12, 90)
    fr = random.choice(
        [
            Fraction(1, 2),
            Fraction(1, 3),
            Fraction(1, 4),
            Fraction(1, 5),
            Fraction(2, 3),
            Fraction(3, 4),
            Fraction(2, 5),
            Fraction(3, 8),
            Fraction(5, 6),
        ]
    )
    eaten = whole * fr
    left = whole - eaten

    question = f"（分數應用）一條長 {whole} 公尺的{thing}，用掉了 {fmt_fraction(fr)}，還剩多少公尺？"
    eaten_s = fmt_decimal_from_fraction(eaten)
    left_s = fmt_decimal_from_fraction(left)

    hints = [
        "觀念：『用掉了幾分之幾』＝用掉 全體×分數；剩下＝全體−用掉。",
        f"列式：用掉 = {whole}×{fmt_fraction(fr)}；剩下 = {whole} − 用掉。",
        "Level 3｜步驟\n"
        f"1) 用掉：{whole}×{fmt_fraction(fr)} = {eaten_s}\n"
        f"2) 剩下：{whole} − {eaten_s} = {left_s}\n"
        f"3) 所以剩下 {left_s} 公尺",
    ]

    steps = [
        "用掉 = 全體 × 分數",
        "剩下 = 全體 − 用掉",
        "寫上單位：公尺",
    ]

    return Q(
        id=f"la5_frac_{i:03d}",
        kind="fraction_remaining",
        difficulty="medium",
        question=question,
        answer=left_s,
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "公尺"},
        explanation=f"用掉 {whole}×{fmt_fraction(fr)}={eaten_s}；剩下 {whole}-{eaten_s}={left_s}（公尺）。",
    )


def q_make_change(i: int) -> Q:
    item = random.choice(["早餐", "午餐便當", "文具", "飲料", "點心"])
    price = Decimal(random.choice(["35", "48", "56", "63", "75", "88", "105", "128", "156", "175"]))

    pay_choices = [
        ((price // Decimal(50)) + 1) * Decimal(50),
        ((price // Decimal(100)) + 1) * Decimal(100),
        ((price // Decimal(200)) + 1) * Decimal(200),
    ]
    pay = random.choice([p for p in pay_choices if p >= price])
    change = pay - price

    question = (
        f"（找零/湊整）買{item}花了 {fmt_money2(price)} 元，"
        f"用 {fmt_money2(pay)} 元付款，找回多少元？（可寫小數）"
    )
    answer = fmt_money2(change)

    hints = [
        "觀念：找零＝付款金額 − 實際金額。",
        f"列式：{fmt_money2(pay)} − {fmt_money2(price)}。",
        "Level 3｜步驟\n"
        f"1) 列式：{fmt_money2(pay)}-{fmt_money2(price)}\n"
        f"2) 計算：{answer}（元）",
    ]

    steps = [
        "找零 = 付款 − 總價",
        f"{fmt_money2(pay)} − {fmt_money2(price)} = {answer}",
        "寫上單位：元",
    ]

    return Q(
        id=f"la5_chg_{i:03d}",
        kind="make_change",
        difficulty="easy",
        question=question,
        answer=answer,
        answer_mode="money2",
        hints=hints,
        steps=steps,
        meta={"unit": "元"},
        explanation=f"找零 = {fmt_money2(pay)} − {fmt_money2(price)} = {answer}（元）。",
    )


def q_two_step_shopping(i: int) -> Q:
    item1 = random.choice(["果汁", "牛奶", "餅乾", "橡皮擦", "鉛筆"]) 
    unit1 = random.choice(["瓶", "盒", "包", "個", "支"]) 
    p1 = Decimal(random.choice(["8.5", "12.5", "15.2", "18.8", "25.6"]))
    q1 = random.randint(2, 6)

    item2 = random.choice(["麵包", "巧克力", "筆記本", "貼紙", "果凍"]) 
    unit2 = random.choice(["個", "包", "本", "張", "盒"]) 
    p2 = Decimal(random.choice(["9.6", "16.5", "20.5", "36.5", "45.0"]))
    q2 = random.randint(2, 6)

    total = p1 * Decimal(q1) + p2 * Decimal(q2)

    coupon = Decimal(random.choice(["10", "20", "30", "40"]))
    if coupon >= total:
        coupon = Decimal("10")
    pay = total - coupon

    question = (
        "（兩段式購物）"
        f"{item1} 每{unit1} {fmt_money2(p1)} 元，買 {q1} {unit1}；"
        f"{item2} 每{unit2} {fmt_money2(p2)} 元，買 {q2} {unit2}。"
        f"結帳時用了 {fmt_money2(coupon)} 元折價券，實付多少元？（可寫小數）"
    )
    answer = fmt_money2(pay)

    hints = [
        "觀念：兩段式＝先算各自小計，再合計，最後做加/減。",
        f"列式：({fmt_money2(p1)}×{q1}) + ({fmt_money2(p2)}×{q2}) − {fmt_money2(coupon)}。",
        "Level 3｜步驟\n"
        f"1) 小計1：{fmt_money2(p1)}×{q1} = {fmt_money2(p1*Decimal(q1))}\n"
        f"2) 小計2：{fmt_money2(p2)}×{q2} = {fmt_money2(p2*Decimal(q2))}\n"
        f"3) 合計：{fmt_money2(total)}\n"
        f"4) 減折價券：{fmt_money2(total)}-{fmt_money2(coupon)} = {answer}（元）",
    ]

    steps = [
        "分別算小計：單價×數量",
        "合計：小計相加",
        "實付：合計 − 折價券",
    ]

    return Q(
        id=f"la5_2st_{i:03d}",
        kind="shopping_two_step",
        difficulty="medium",
        question=question,
        answer=answer,
        answer_mode="money2",
        hints=hints,
        steps=steps,
        meta={"unit": "元"},
        explanation=f"先算各自小計再合計 {fmt_money2(total)}，最後減 {fmt_money2(coupon)} 得 {answer}（元）。",
    )


def q_table_stats(i: int) -> Q:
    cats = random.sample(["蘋果", "香蕉", "橘子", "葡萄", "草莓", "梨子"], 4)
    a, b, c, d = [random.randint(6, 28) for _ in range(4)]
    table = (
        f"{cats[0]}：{a} 個\n"
        f"{cats[1]}：{b} 個\n"
        f"{cats[2]}：{c} 個\n"
        f"{cats[3]}：{d} 個"
    )

    mode = random.choice(["total", "diff", "most"])
    if mode == "total":
        ans = a + b + c + d
        question = f"（表格統計）水果數量如下：\n{table}\n一共多少個水果？（只寫數字）"
        hints = [
            "觀念：總數＝把各項數量相加。",
            f"列式：{a}+{b}+{c}+{d}。",
            f"Level 3｜計算：{a}+{b}+{c}+{d} = {ans}。",
        ]
        steps = ["把四個數相加", f"得到 {ans}"]
        explanation = f"總數 = {a}+{b}+{c}+{d} = {ans}（個）。"
    elif mode == "diff":
        ans = abs(a - b)
        question = f"（表格統計）水果數量如下：\n{table}\n{cats[0]}比{cats[1]}多(或少)多少個？（只寫數字）"
        hints = [
            "觀念：比較多/少多少 → 用減法，取差。",
            f"列式：|{a}−{b}|。",
            f"Level 3｜計算：|{a}−{b}| = {ans}。",
        ]
        steps = ["用減法求差", f"|{a}−{b}| = {ans}"]
        explanation = f"差 = |{a}−{b}| = {ans}（個）。"
    else:
        values = {cats[0]: a, cats[1]: b, cats[2]: c, cats[3]: d}
        best = max(values, key=values.get)
        ans = values[best]
        question = f"（表格統計）水果數量如下：\n{table}\n最多的是哪一種水果？（請輸入它的數量，只寫數字）"
        hints = [
            "觀念：先找最大值。",
            "方法：比較四個數，找出最大那個。",
            f"Level 3｜最大的是 {best}，數量 {ans}。",
        ]
        steps = ["比較四個數大小", f"最大值是 {ans}"]
        explanation = f"四項中最大的是 {best}，共有 {ans}（個）。"

    return Q(
        id=f"la5_tbl_{i:03d}",
        kind="table_stats",
        difficulty="easy",
        question=question,
        answer=str(ans),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "個"},
        explanation=explanation,
    )


def q_area_tiling(i: int) -> Q:
    room_m_l = random.randint(2, 8)
    room_m_w = random.randint(2, 7)
    tile_cm = random.choice([25, 30, 40, 50])

    room_cm_l = room_m_l * 100
    room_cm_w = room_m_w * 100
    room_area = room_cm_l * room_cm_w
    tile_area = tile_cm * tile_cm

    if room_area % tile_area != 0:
        # make it divisible by adjusting width
        room_cm_w = (room_cm_w // tile_cm) * tile_cm
        if room_cm_w == 0:
            room_cm_w = tile_cm
        room_area = room_cm_l * room_cm_w

    tiles = room_area // tile_area
    question = (
        "（面積鋪地磚）"
        f"房間長 {room_m_l} 公尺、寬 {room_cm_w//100} 公尺，"
        f"要鋪 {tile_cm} 公分×{tile_cm} 公分的正方形地磚，至少需要幾塊？（只寫數字）"
    )

    hints = [
        "觀念：先算房間面積，再算每塊地磚面積，最後用除法。",
        "方法：把公尺換成公分後，用 面積=長×寬。",
        "Level 3｜步驟\n"
        f"1) 房間：{room_cm_l}×{room_cm_w} = {room_area}（平方公分）\n"
        f"2) 地磚：{tile_cm}×{tile_cm} = {tile_area}（平方公分）\n"
        f"3) 需要：{room_area}÷{tile_area} = {tiles}（塊）",
    ]

    steps = [
        "公尺換算成公分",
        "房間面積 = 長×寬",
        "地磚面積 = 邊長×邊長",
        "用除法求塊數",
    ]

    return Q(
        id=f"la5_area_{i:03d}",
        kind="area_tiling",
        difficulty="medium",
        question=question,
        answer=str(tiles),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "塊"},
        explanation=f"房間面積 {room_area}（cm²），每塊 {tile_area}（cm²），所以需要 {tiles}（塊）。",
    )


def q_proportional_split(i: int) -> Q:
    names = random.sample(["甲", "乙", "丙", "丁"], 3)
    a = random.randint(1, 5)
    b = random.randint(1, 6)
    c = random.randint(1, 7)
    s = a + b + c
    k = random.randint(6, 20)
    total = s * k
    pick = random.choice([(names[0], a), (names[1], b), (names[2], c)])
    who, part = pick
    share = part * k

    question = (
        "（比例分配）"
        f"把 {total} 顆糖按 {names[0]}:{names[1]}:{names[2]} = {a}:{b}:{c} 分配，"
        f"{who} 分到幾顆？（只寫數字）"
    )

    hints = [
        "觀念：先把比的各部分加起來，算出『總份數』。",
        f"方法：總份數={a}+{b}+{c}={s}；每份={total}÷{s}。",
        "Level 3｜步驟\n"
        f"1) 每份：{total}÷{s} = {k}\n"
        f"2) {who} 有 {part} 份：{part}×{k} = {share}（顆）",
    ]

    steps = [
        "總份數 = 比的各部分相加",
        "每份 = 總數 ÷ 總份數",
        "某人份數 × 每份 = 分到的數量",
    ]

    return Q(
        id=f"la5_prop_{i:03d}",
        kind="proportional_split",
        difficulty="medium",
        question=question,
        answer=str(share),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "顆"},
        explanation=f"總份數 {s}，每份 {k}；{who} {part} 份，所以 {part}×{k}={share}（顆）。",
    )


def q_perimeter_fence(i: int) -> Q:
    shape = random.choice(["長方形", "正方形"])
    if shape == "正方形":
        side_m = random.choice([6, 8, 10, 12, 14, 15, 18, 20])
        per = 4 * side_m
        question = f"（圍籬/周長）一個正方形花圃邊長 {side_m} 公尺，要用圍籬把四周圍起來，需要多少公尺圍籬？（只寫數字）"
        hints = [
            "觀念：周長＝四邊長度的總和。正方形周長＝邊長×4。",
            f"列式：{side_m}×4。",
            f"Level 3｜計算：{side_m}×4 = {per}（公尺）。",
        ]
        steps = ["正方形周長 = 邊長×4", f"{side_m}×4={per}"]
        explanation = f"正方形周長 = {side_m}×4 = {per}（公尺）。"
    else:
        l = random.choice([8, 10, 12, 15, 18, 20, 24, 25])
        w = random.choice([5, 6, 7, 8, 9, 10, 12, 14])
        per = 2 * (l + w)
        question = f"（圍籬/周長）一個長方形花圃長 {l} 公尺、寬 {w} 公尺，要用圍籬把四周圍起來，需要多少公尺圍籬？（只寫數字）"
        hints = [
            "觀念：長方形周長＝(長+寬)×2。",
            f"列式：({l}+{w})×2。",
            f"Level 3｜計算：({l}+{w})×2 = {per}（公尺）。",
        ]
        steps = ["長方形周長 = (長+寬)×2", f"({l}+{w})×2={per}"]
        explanation = f"周長 = (長+寬)×2 = ({l}+{w})×2 = {per}（公尺）。"

    return Q(
        id=f"la5_per_{i:03d}",
        kind="perimeter_fence",
        difficulty="easy",
        question=question,
        answer=str(per),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "公尺"},
        explanation=explanation,
    )


def q_volume_fill(i: int) -> Q:
    container = random.choice(["水桶", "水壺", "量杯", "水箱"])
    cap_l = random.choice([2, 3, 5, 8, 10, 12])
    have_ml = random.randrange(250, cap_l * 1000, 50)
    need_ml = cap_l * 1000 - have_ml

    question = (
        f"（容積/容量）一個{container}最多裝 {cap_l} 公升水，"
        f"現在裡面有 {have_ml} 毫升水，還要再加多少毫升才會裝滿？（只寫數字）"
    )

    hints = [
        "觀念：先把單位統一，再用『總容量−已有』。1 公升 = 1000 毫升。",
        f"方法：總容量={cap_l}×1000={cap_l*1000}（毫升）。列式：{cap_l*1000}−{have_ml}。",
        f"Level 3｜計算：{cap_l*1000}−{have_ml} = {need_ml}（毫升）。",
    ]

    steps = [
        "把公升換成毫升",
        "需要量 = 總容量 − 已有量",
        f"得到 {need_ml}",
    ]

    return Q(
        id=f"la5_vol_{i:03d}",
        kind="volume_fill",
        difficulty="easy",
        question=question,
        answer=str(need_ml),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "毫升"},
        explanation=f"總容量 {cap_l}L={cap_l*1000}mL，還要加 {cap_l*1000}-{have_ml}={need_ml}（mL）。",
    )


def q_temperature_change(i: int) -> Q:
    place = random.choice(["教室", "戶外", "山上", "冰箱旁", "運動場"])
    start = random.randint(-2, 28)
    delta = random.choice([3, 4, 5, 6, 7, 8, 9, 10, 12])
    direction = random.choice(["up", "down"])
    end = start + delta if direction == "up" else start - delta

    if direction == "up":
        question = f"（溫度變化）{place}一開始是 {start}°C，過了一會兒上升了 {delta}°C，現在是多少°C？（只寫數字）"
        hints = [
            "觀念：上升→用加法；下降→用減法。",
            f"列式：{start}+{delta}。",
            f"Level 3｜計算：{start}+{delta} = {end}（°C）。",
        ]
        steps = ["上升用加法", f"{start}+{delta}={end}"]
        explanation = f"上升 {delta}°C，所以 {start}+{delta}={end}（°C）。"
    else:
        question = f"（溫度變化）{place}一開始是 {start}°C，過了一會兒下降了 {delta}°C，現在是多少°C？（只寫數字）"
        hints = [
            "觀念：上升→用加法；下降→用減法。",
            f"列式：{start}−{delta}。",
            f"Level 3｜計算：{start}−{delta} = {end}（°C）。",
        ]
        steps = ["下降用減法", f"{start}-{delta}={end}"]
        explanation = f"下降 {delta}°C，所以 {start}-{delta}={end}（°C）。"

    return Q(
        id=f"la5_tmp_{i:03d}",
        kind="temperature_change",
        difficulty="easy",
        question=question,
        answer=str(end),
        answer_mode="number",
        hints=hints,
        steps=steps,
        meta={"unit": "°C"},
        explanation=explanation,
    )


def build_bank(target_total: int = 300) -> List[Dict[str, Any]]:
    generators: Dict[str, Any] = {
        "buy_many": q_buy_many,
        "discount": q_discount,
        "unit_price": q_unit_price,
        "time_add": q_time_add,
        "unit_convert": q_unit_convert,
        "fraction_remaining": q_fraction_remaining,
        "make_change": q_make_change,
        "shopping_two_step": q_two_step_shopping,
        "table_stats": q_table_stats,
        "area_tiling": q_area_tiling,
        "proportional_split": q_proportional_split,
        "perimeter_fence": q_perimeter_fence,
        "volume_fill": q_volume_fill,
        "temperature_change": q_temperature_change,
    }

    quotas: Dict[str, int] = {
        "buy_many": 28,
        "unit_price": 25,
        "discount": 25,
        "make_change": 22,
        "shopping_two_step": 22,
        "table_stats": 20,
        "area_tiling": 20,
        "proportional_split": 20,
        "perimeter_fence": 18,
        "volume_fill": 20,
        "temperature_change": 20,
        "time_add": 20,
        "unit_convert": 20,
        "fraction_remaining": 20,
    }

    seen_questions: set[str] = set()
    out: List[Dict[str, Any]] = []
    idx = 1

    def _emit(q: Q) -> None:
        out.append(
            {
                "id": q.id,
                "kind": q.kind,
                "topic": TOPIC,
                "difficulty": q.difficulty,
                "question": q.question,
                "answer": q.answer,
                "answer_mode": q.answer_mode,
                "hints": q.hints,
                "steps": q.steps,
                "meta": q.meta,
                "explanation": q.explanation,
            }
        )

    # Fill per-kind quotas with retry to avoid duplicates.
    for kind, target in quotas.items():
        made = 0
        attempts = 0
        gen = generators[kind]
        while made < target:
            attempts += 1
            if attempts > target * 800:
                raise RuntimeError(f"Unable to fill quota kind={kind} target={target} made={made}")

            q = gen(idx)
            if q.question in seen_questions:
                continue
            seen_questions.add(q.question)
            _emit(q)
            idx += 1
            made += 1

    # If quotas don't sum to target_total, fill remaining with a balanced mix.
    if len(out) < target_total:
        kinds = list(generators.keys())
        attempts = 0
        while len(out) < target_total:
            attempts += 1
            if attempts > (target_total - len(out)) * 1200:
                raise RuntimeError(f"Unable to reach target_total={target_total} got={len(out)}")
            kind = random.choice(kinds)
            q = generators[kind](idx)
            if q.question in seen_questions:
                continue
            seen_questions.add(q.question)
            _emit(q)
            idx += 1

    return out


def main() -> None:
    bank = build_bank(target_total=300)
    OUT_JS.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(bank, ensure_ascii=False, indent=2)
    header = "/* Auto-generated offline question bank. */\nwindow.LIFE_APPLICATIONS_G5_BANK = "
    OUT_JS.write_text(header + payload + ";\n", encoding="utf-8")

    kinds = sorted({x["kind"] for x in bank})
    print(f"Wrote {OUT_JS} (n={len(bank)} kinds={len(kinds)}: {', '.join(kinds)})")


if __name__ == "__main__":
    main()
