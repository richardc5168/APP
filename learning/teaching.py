from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class TeachingGuide:
    skill_tag: str
    title: str
    key_ideas: List[str]
    common_mistakes: List[str]
    practice_goal: str
    mastery_check: str


_SKILL_GUIDES: Dict[str, TeachingGuide] = {
    "四則運算": TeachingGuide(
        skill_tag="四則運算",
        title="四則運算（含括號/乘除順序）",
        key_ideas=[
            "口訣：括號 → 乘除 → 加減；同級由左到右。",
            "每一步都要把中間結果寫出來，不跳步。",
            "做完回頭用估算檢查答案量級是否合理。",
        ],
        common_mistakes=[
            "把加減先算、忽略乘除優先。",
            "同級運算不按左到右。",
            "負號或括號漏寫，導致整串算錯。",
        ],
        practice_goal="連續 10 題運算順序題，正確率 ≥ 85%",
        mastery_check="最近 5 題中至少 4 題一次做對，且不靠提示。",
    ),
    "分數/小數": TeachingGuide(
        skill_tag="分數/小數",
        title="分數應用（先用掉/剩下/再用掉）與分數運算",
        key_ideas=[
            "先定義『整體=1』，分母代表分成幾等份。",
            "看到『剩下』先做 1 − 分數；看到『剩下的又…』第二段以『剩下量』為基準做乘法。",
            "加減要通分；乘法可先約分再乘，降低算錯率。",
        ],
        common_mistakes=[
            "把『剩下的又用掉』誤當成兩次都對原來整體（該用乘法卻用加法）。",
            "通分只乘分母不乘分子。",
            "最後問『剩下』卻回答『用掉』或反之。",
        ],
        practice_goal="同題型 3 題一組練習，連續 2 組都全對（共 6 題）。",
        mastery_check="能口頭說出：第一次剩下怎麼列式、第二次基準是什麼、最後問的是剩下還是用掉。",
    ),
    "比例": TeachingGuide(
        skill_tag="比例",
        title="比例（配方/放大縮小/路程關係）",
        key_ideas=[
            "先寫出對應關係（A:B = C:D），再決定用倍數或交叉相乘。",
            "單位要一致（公分/公尺、分鐘/小時）。",
            "先用簡單數字做『倍數感』檢查是否合理。",
        ],
        common_mistakes=[
            "把比值方向寫反（例如 A/B 與 B/A）。",
            "單位未統一就直接計算。",
        ],
        practice_goal="配方/比例縮放題 8 題，正確率 ≥ 85%",
        mastery_check="能說清楚：哪兩個量成比例、倍數從哪裡來。",
    ),
    "單位換算": TeachingGuide(
        skill_tag="單位換算",
        title="單位換算（長度/重量/容量/時間）",
        key_ideas=[
            "先寫換算表（例如 1 m = 100 cm）。",
            "乘/除 10、100、1000 的方向要用『比大比小』判斷。",
        ],
        common_mistakes=[
            "把乘除方向做反。",
            "少了 0 或多了 0。",
        ],
        practice_goal="同一種換算連續 10 題，錯題立刻訂正並再做 2 題。",
        mastery_check="看到題目能先判斷答案應變大或變小。",
    ),
    "路程時間": TeachingGuide(
        skill_tag="路程時間",
        title="路程-時間-速度（D=RT）",
        key_ideas=[
            "公式：路程 = 速度 × 時間；速度 = 路程 ÷ 時間；時間 = 路程 ÷ 速度。",
            "先統一單位（km/h 與 分鐘/小時）。",
        ],
        common_mistakes=[
            "公式套錯（把乘寫成除）。",
            "單位沒換就算。",
        ],
        practice_goal="D/R/T 三種問法各 3 題，共 9 題，正確率 ≥ 85%",
        mastery_check="能先說：題目問哪個量、已知哪兩個量。",
    ),
    "折扣": TeachingGuide(
        skill_tag="折扣",
        title="折扣（折後=原價×(1-折扣)；原價反推）",
        key_ideas=[
            "先求『折後比例』：1 − 折扣（或直接用折數換算）。",
            "原價反推用除法：原價 = 折後價 ÷ 折後比例。",
        ],
        common_mistakes=[
            "把反推原價也用乘法。",
            "把折扣比例與折後比例搞混。",
        ],
        practice_goal="折扣正推 5 題 + 反推 5 題，正確率 ≥ 85%",
        mastery_check="能說出：題目給的是原價/折後價/折扣？要用乘還是除。",
    ),
}


def get_teaching_guide(skill_tag: str) -> TeachingGuide:
    key = str(skill_tag or "unknown")
    return _SKILL_GUIDES.get(key) or TeachingGuide(
        skill_tag=key,
        title=f"加強：{key}",
        key_ideas=["先把題目關鍵字圈出來，列式後再算。"],
        common_mistakes=["跳步心算、沒檢查單位或題目問法。"],
        practice_goal="由易到難練習 10 題，正確率 ≥ 80%",
        mastery_check="最近 5 題中至少 4 題做對，且能解釋每一步。",
    )


def suggested_engine_topic_key(skill_tag: str) -> Optional[str]:
    """Map a high-level skill tag to an engine generator key.

    Returns None when no strong mapping exists.
    """

    skill_tag = str(skill_tag or "")

    if skill_tag == "四則運算":
        return "1"
    if skill_tag in ("分數/小數", "折扣"):
        # Fraction word problems cover many multi-step fraction/discount contexts.
        return "11"
    # Other skills may be covered by pack generators if available, but they are optional.
    return None
