from __future__ import annotations

import argparse
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any


TYPE_KEY = "external_web_fraction_app_v1"


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _pick_note(raw_notes: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    if not raw_notes:
        return {
            "note_id": "extnote_0000",
            "source_url": "(mock)",
            "title": "(mock)",
            "quoted_fact": "(mock)",
            "retrieved_at": _now_iso(),
        }
    return rng.choice(raw_notes)


def _hints(level1: str, level2: str, level3: str, answer: str) -> dict[str, str]:
    answer_norm = "".join(str(answer or "").split()).lower()
    for level_name, value in (("level1", level1), ("level2", level2), ("level3", level3)):
        normalized = "".join(str(value or "").split()).lower()
        if answer_norm and answer_norm in normalized:
            raise ValueError(f"{level_name} leaks final answer")
    return {
        "level1": str(level1).strip(),
        "level2": str(level2).strip(),
        "level3": str(level3).strip(),
    }


def _hint_ladder(h1: str, h2: str, h3: str, h4: str, answer: str) -> dict[str, str]:
    answer_norm = "".join(str(answer or "").split()).lower()
    for level_name, value in (("h1_strategy", h1), ("h4_check_reflect", h4)):
        normalized = "".join(str(value or "").split()).lower()
        if answer_norm and answer_norm in normalized:
            raise ValueError(f"{level_name} leaks final answer")
    return {
        "h1_strategy": h1.strip(),
        "h2_equation": h2.strip(),
        "h3_compute": h3.strip(),
        "h4_check_reflect": h4.strip(),
    }


def _default_error_diagnostics() -> list[dict[str, str]]:
    return [
        {"code": "E_UNIT", "message": "單位未統一", "remedy": "先把單位換成同一種再列式。"},
        {"code": "E_RATE", "message": "比率解讀錯誤", "remedy": "確認是折扣率還是付款率。"},
        {"code": "E_DEN", "message": "分母用錯", "remedy": "平均分配時分母應是份數或人數。"},
        {"code": "E_SIMPLIFY", "message": "約分遺漏", "remedy": "最後檢查分子分母是否可同除。"},
        {"code": "E_CHECK", "message": "未做反向檢查", "remedy": "將答案代回原題確認合理性。"},
    ]


def _item(
    *,
    idx: int,
    category: str,
    question: str,
    answer: str,
    difficulty: str,
    hints: dict[str, str],
    hint_ladder: dict[str, str],
    steps: list[str],
    validator: dict[str, Any],
    topic_tags: list[str],
    concept_points: list[str],
    note: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": f"extfrac_{idx:04d}",
        "type_key": TYPE_KEY,
        "category": category,
        "topic_tags": topic_tags,
        "concept_points": concept_points,
        "difficulty": difficulty,
        "question": question,
        "answer": answer,
        "hints": hints,
        "hint_ladder": hint_ladder,
        "steps": steps,
        "error_diagnostics": _default_error_diagnostics(),
        "validator": validator,
        "evidence": {
            "note_id": str(note.get("note_id") or ""),
            "source_url": str(note.get("source_url") or ""),
            "title": str(note.get("title") or ""),
            "quoted_fact": str((((note.get("quotes") or [{}])[0] or {}).get("text") if isinstance(note.get("quotes"), list) else "") or ""),
            "retrieved_at": str(note.get("retrieved_at") or ""),
        },
        "generated_at": _now_iso(),
    }


def _reduce_fraction(num: int, den: int) -> str:
    from math import gcd

    g = gcd(num, den)
    return f"{num // g}/{den // g}"


def _gen_shopping_discount(rng: random.Random, notes: list[dict[str, Any]], idx: int) -> dict[str, Any]:
    price = rng.choice([180, 240, 360, 480, 600])
    discount = rng.choice([10, 20, 25, 30])
    pay_num = 100 - discount
    answer = str(int(price * pay_num / 100))

    question = f"（購物折扣）一本書原價 {price} 元，打 {discount}% 折扣後，需付多少元？（填整數）"
    hints = _hints("先把折扣轉成付款率。", "現價 = 原價 × (1 - 折扣率)。", "把百分率改成分數後再計算。", answer)
    hint_ladder = _hint_ladder(
        "策略：先求付款率，再算現價。",
        "列式：現價 = 原價 × 付款率。",
        "計算：先將百分率轉分數，再完成乘法。",
        "檢查：折後價應小於原價。",
        answer,
    )
    steps = [
        f"步驟 1：付款率 = {pay_num}% = {pay_num}/100。",
        f"步驟 2：現價 = {price}×{pay_num}/100。",
        f"步驟 3：計算得 {answer} 元。",
    ]
    note = _pick_note(notes, rng)
    return _item(
        idx=idx,
        category="shopping_discount",
        question=question,
        answer=answer,
        difficulty="easy",
        hints=hints,
        hint_ladder=hint_ladder,
        steps=steps,
        validator={"type": "number", "tolerance": 0},
        topic_tags=["shopping_discount", "ratio"],
        concept_points=["折扣率要轉付款率", "現價=原價×付款率"],
        note=note,
    )


def _gen_average_distribution(rng: random.Random, notes: list[dict[str, Any]], idx: int) -> dict[str, Any]:
    whole = rng.choice([18, 24, 30, 36, 42])
    numerator = rng.choice([1, 2, 3, 4])
    denominator = rng.choice([3, 4, 5, 6])
    people = rng.choice([2, 3, 4, 6])
    part = whole * numerator / denominator
    answer_fraction = _reduce_fraction(int(part), people)

    question = (
        f"（平均分配）一桶果汁共 {whole} 公升，先用掉 {numerator}/{denominator}，"
        f"剩下平均分給 {people} 人，每人可得多少公升？（最簡分數）"
    )
    hints = _hints("先算剩下量，再除以人數。", "剩下量 = 全部×(1-已用分率)。", "把剩下量除以人數並約分。", answer_fraction)
    hint_ladder = _hint_ladder(
        "策略：兩段式，先求剩下再平均。",
        "列式：每人量 = [總量×(1-已用分率)]÷人數。",
        "計算：先做分數減法，再做除法與約分。",
        "檢查：每人份量×人數應回到剩下量。",
        answer_fraction,
    )
    remain_num = whole * (denominator - numerator)
    remain_den = denominator
    steps = [
        f"步驟 1：剩下量 = {whole}×({denominator-numerator}/{denominator}) = {remain_num}/{remain_den}。",
        f"步驟 2：每人 = ({remain_num}/{remain_den})÷{people}。",
        f"步驟 3：約分後得到 {answer_fraction}。",
    ]
    note = _pick_note(notes, rng)
    return _item(
        idx=idx,
        category="average_distribution",
        question=question,
        answer=answer_fraction,
        difficulty="medium",
        hints=hints,
        hint_ladder=hint_ladder,
        steps=steps,
        validator={"type": "fraction"},
        topic_tags=["average_distribution", "remaining_amount"],
        concept_points=["先算剩下量", "平均分配用除法"],
        note=note,
    )


def _gen_unit_conversion(rng: random.Random, notes: list[dict[str, Any]], idx: int) -> dict[str, Any]:
    liters = rng.choice([1, 1.5, 2, 2.5, 3.2, 4])
    frac_num = rng.choice([1, 2, 3])
    frac_den = rng.choice([4, 5, 8])
    whole_ml = int(liters * 1000)
    take_ml = int(whole_ml * frac_num / frac_den)
    answer = str(take_ml)

    question = f"（單位換算）{liters:g} 公升牛奶取出 {frac_num}/{frac_den}，取出的量是多少毫升？（整數）"
    hints = _hints("先把公升換成毫升。", "總毫升×分率就是取出量。", "先換單位再做分數乘法。", answer)
    hint_ladder = _hint_ladder(
        "策略：先統一到毫升再運算。",
        "列式：取出量 = (總公升×1000)×分率。",
        "計算：先換單位，再乘分率。",
        "檢查：取出量不可超過總量。",
        answer,
    )
    steps = [
        f"步驟 1：{liters:g} 公升 = {whole_ml} 毫升。",
        f"步驟 2：取出量 = {whole_ml}×{frac_num}/{frac_den}。",
        f"步驟 3：計算得 {answer} 毫升。",
    ]
    note = _pick_note(notes, rng)
    return _item(
        idx=idx,
        category="unit_conversion",
        question=question,
        answer=answer,
        difficulty="easy",
        hints=hints,
        hint_ladder=hint_ladder,
        steps=steps,
        validator={"type": "number", "tolerance": 0},
        topic_tags=["unit_conversion", "fraction"],
        concept_points=["先換單位再運算", "分率乘總量"],
        note=note,
    )


def _gen_distance_time(rng: random.Random, notes: list[dict[str, Any]], idx: int) -> dict[str, Any]:
    speed = rng.choice([48, 54, 60, 72])
    minute_num = rng.choice([20, 30, 45, 50])
    minute_den = 60
    answer = _reduce_fraction(speed * minute_num, minute_den)

    question = f"（路程時間）一台車每小時行 {speed} 公里，行駛 {minute_num} 分鐘可走多少公里？（最簡分數）"
    hints = _hints("先把分鐘換成小時。", "距離=速度×時間。", "時間換成分數小時再代入。", answer)
    hint_ladder = _hint_ladder(
        "策略：先做時間換算，再用路程公式。",
        "列式：路程 = 速度 × (分鐘/60)。",
        "計算：先約分，再完成乘法。",
        "檢查：時間不到 1 小時，距離應小於時速值。",
        answer,
    )
    steps = [
        f"步驟 1：{minute_num} 分鐘 = {minute_num}/60 小時。",
        f"步驟 2：距離 = {speed}×{minute_num}/60。",
        f"步驟 3：約分後得到 {answer} 公里。",
    ]
    note = _pick_note(notes, rng)
    return _item(
        idx=idx,
        category="distance_time",
        question=question,
        answer=answer,
        difficulty="hard",
        hints=hints,
        hint_ladder=hint_ladder,
        steps=steps,
        validator={"type": "fraction"},
        topic_tags=["distance_time", "unit_conversion"],
        concept_points=["先換時間單位", "distance=speed×time"],
        note=note,
    )


def build_pack(raw_jsonl: Path, out_json: Path, n: int, seed: int) -> dict[str, Any]:
    raw_notes = _read_jsonl(raw_jsonl)
    rng = random.Random(int(seed))

    generators = [
        _gen_shopping_discount,
        _gen_average_distribution,
        _gen_unit_conversion,
        _gen_distance_time,
    ]

    items: list[dict[str, Any]] = []
    used_questions: set[str] = set()
    idx = 1
    attempts = 0
    while len(items) < n and attempts < n * 200:
        attempts += 1
        generator = rng.choice(generators)
        item = generator(rng, raw_notes, idx)
        if item["question"] in used_questions:
            continue
        used_questions.add(item["question"])
        items.append(item)
        idx += 1

    if len(items) < n:
        raise RuntimeError(f"Unable to build pack target={n}, got={len(items)}")

    pack = {
        "type_key": TYPE_KEY,
        "version": f"v{datetime.now().strftime('%Y%m%d')}",
        "seed": int(seed),
        "generated_at": _now_iso(),
        "items": items,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    return pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="data/external_web_notes/external_web_fraction_app_notes.jsonl")
    parser.add_argument("--out", default="data/external_web_fraction_app_v1_pack.json")
    parser.add_argument("--n", type=int, default=40)
    parser.add_argument("--seed", type=int, default=60223)
    args = parser.parse_args(argv)

    pack = build_pack(Path(args.raw), Path(args.out), n=int(args.n), seed=int(args.seed))
    print(f"Wrote {args.out} (items={len(pack['items'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
