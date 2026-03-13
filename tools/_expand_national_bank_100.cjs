#!/usr/bin/env node
/**
 * Expand interactive-g5-national-bank from 46 → 100 questions.
 * +54 self-contained computational questions across 15 kinds.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const BANK_PATHS = [
  path.join(__dirname, '..', 'docs', 'interactive-g5-national-bank', 'bank.js'),
  path.join(__dirname, '..', 'dist_ai_math_web_pages', 'docs', 'interactive-g5-national-bank', 'bank.js'),
];

const NEW_QS = [

// ═══ fraction_addsub (5) ═══
{
  id:"g5_national_exp_1", kind:"fraction_addsub", topic:"fraction_addsub",
  question:"計算 2/5 + 1/4 = ？",
  answer:"13/20",
  hints:[
    "⭐ 觀念提醒\n分母不同要先通分。",
    "🔍 列式引導\n5 和 4 的最小公倍數是 20。\n2/5 = 8/20，1/4 = 5/20",
    "📐 一步步算：\n① 2/5 = 8/20\n② 1/4 = 5/20\n③ 8/20 + 5/20 = ？",
    "👉 通分後分子相加，分母不變。"
  ],
  common_mistakes:["分母直接相加。","通分時分子沒同步擴大。"]
},
{
  id:"g5_national_exp_2", kind:"fraction_addsub", topic:"fraction_addsub",
  question:"計算 7/8 − 1/6 = ？",
  answer:"17/24",
  hints:[
    "⭐ 觀念提醒\n8 和 6 的最小公倍數是 24。",
    "🔍 列式引導\n7/8 = 21/24，1/6 = 4/24",
    "📐 一步步算：\n① 7/8 = 21/24\n② 1/6 = 4/24\n③ 21/24 − 4/24 = ？",
    "👉 先通分再減，結果檢查能否約分。"
  ],
  common_mistakes:["最小公倍數找錯。","通分時分子忘記同步擴大。"]
},
{
  id:"g5_national_exp_3", kind:"fraction_addsub", topic:"fraction_addsub",
  question:"計算 1/2 + 2/9 = ？",
  answer:"13/18",
  hints:[
    "⭐ 觀念提醒\n2 和 9 的最小公倍數是 18。",
    "🔍 列式引導\n1/2 = 9/18，2/9 = 4/18",
    "📐 一步步算：\n① 1/2 = 9/18\n② 2/9 = 4/18\n③ 9/18 + 4/18 = ？",
    "👉 分母不同時一定要先通分。"
  ],
  common_mistakes:["1/2 通分成 1/18（忘記分子也要乘 9）。","分母相加。"]
},
{
  id:"g5_national_exp_4", kind:"fraction_addsub", topic:"fraction_addsub",
  question:"計算 5/6 − 3/8 = ？",
  answer:"11/24",
  hints:[
    "⭐ 觀念提醒\n6 和 8 的最小公倍數是 24。",
    "🔍 列式引導\n5/6 = 20/24，3/8 = 9/24",
    "📐 一步步算：\n① 5/6 = 20/24\n② 3/8 = 9/24\n③ 20/24 − 9/24 = ？",
    "👉 先通分再相減。"
  ],
  common_mistakes:["最小公倍數算成 48（可以但不是最簡）。","通分後分子算錯。"]
},
{
  id:"g5_national_exp_5", kind:"fraction_addsub", topic:"fraction_addsub",
  question:"計算 1 − 3/11 = ？",
  answer:"8/11",
  hints:[
    "⭐ 觀念提醒\n1 = 11/11。",
    "🔍 列式引導\n列式：11/11 − 3/11",
    "📐 一步步算：\n① 1 = 11/11\n② 11/11 − 3/11 = ？",
    "👉 把 1 寫成和減數同分母的分數。"
  ],
  common_mistakes:["1 寫成 1/11。","11−3 算成 7。"]
},

// ═══ fraction_mul (5) ═══
{
  id:"g5_national_exp_6", kind:"fraction_mul", topic:"fraction_mul",
  question:"計算 5/6 × 3/10 = ？",
  answer:"1/4",
  hints:[
    "⭐ 觀念提醒\n分數乘法：分子×分子 / 分母×分母。",
    "🔍 列式引導\n5/6 × 3/10，可以先約分：5 和 10 約 5，3 和 6 約 3。",
    "📐 一步步算：\n① 分子 5×3=15，分母 6×10=60\n② 15/60 約分 → ？",
    "👉 先約分再乘可以簡化計算。"
  ],
  common_mistakes:["約分不完全。","分子乘分母或分母乘分子搞混。"]
},
{
  id:"g5_national_exp_7", kind:"fraction_mul", topic:"fraction_mul",
  question:"計算 4/7 × 21 = ？",
  answer:"12",
  hints:[
    "⭐ 觀念提醒\n分數 × 整數：分子 × 整數 ÷ 分母。",
    "🔍 列式引導\n4/7 × 21，先約：21÷7=3，再 4×3",
    "📐 一步步算：\n① 21 ÷ 7 = 3\n② 4 × 3 = ？",
    "👉 整數和分母先約分，避免大數運算。"
  ],
  common_mistakes:["4×21=84 忘了÷7。","分數乘整數的規則搞錯。"]
},
{
  id:"g5_national_exp_8", kind:"fraction_mul", topic:"fraction_mul",
  question:"計算 3/8 × 4/9 = ？",
  answer:"1/6",
  hints:[
    "⭐ 觀念提醒\n分數乘法：分子×分子 / 分母×分母，再約分。",
    "🔍 列式引導\n3 和 9 約 3，4 和 8 約 4。",
    "📐 一步步算：\n① 分子 3×4=12，分母 8×9=72\n② 12/72 約分 → ？",
    "👉 12 和 72 的最大公因數是 12。"
  ],
  common_mistakes:["約分不完全，寫成 2/12。","分子分母乘錯。"]
},
{
  id:"g5_national_exp_9", kind:"fraction_mul", topic:"fraction_mul",
  question:"計算 6 × 5/8 = ？",
  answer:"15/4",
  hints:[
    "⭐ 觀念提醒\n整數 × 分數：整數 × 分子 / 分母。",
    "🔍 列式引導\n6 × 5 ÷ 8，6 和 8 可先約 2。",
    "📐 一步步算：\n① 6 × 5 = 30\n② 30/8 約分 → ？",
    "👉 30/8 = 15/4 = 3 又 3/4。"
  ],
  common_mistakes:["分母也乘了 6。","約分忘記做。"]
},
{
  id:"g5_national_exp_10", kind:"fraction_mul", topic:"fraction_mul",
  question:"計算 2/9 × 3/5 = ？",
  answer:"2/15",
  hints:[
    "⭐ 觀念提醒\n分子×分子 / 分母×分母。",
    "🔍 列式引導\n3 和 9 可以先約（公因數 3）。",
    "📐 一步步算：\n① 分子 2×3=6，分母 9×5=45\n② 6/45 約分 → ？",
    "👉 6 和 45 最大公因數是 3。"
  ],
  common_mistakes:["6/45 沒有約分。","約分不正確。"]
},

// ═══ fraction_of_quantity (4) ═══
{
  id:"g5_national_exp_11", kind:"fraction_of_quantity", topic:"fraction_of_quantity",
  question:"農場有 270 隻羊，其中 2/9 是小羊，小羊有幾隻？",
  answer:"60",
  hints:[
    "⭐ 觀念提醒\n求全部的幾分之幾 → 乘法。",
    "🔍 列式引導\n列式：270 × 2/9",
    "📐 一步步算：\n① 270 ÷ 9 = 30\n② 30 × 2 = ？",
    "👉 先除後乘避免大數。"
  ],
  common_mistakes:["270÷2×9（分子分母搞反）。","270×2 忘了÷9。"]
},
{
  id:"g5_national_exp_12", kind:"fraction_of_quantity", topic:"fraction_of_quantity",
  question:"花店有 320 朵花，其中 3/8 是玫瑰花，玫瑰花有幾朵？",
  answer:"120",
  hints:[
    "⭐ 觀念提醒\n求某部分佔全體的量 → 乘法。",
    "🔍 列式引導\n列式：320 × 3/8",
    "📐 一步步算：\n① 320 ÷ 8 = 40\n② 40 × 3 = ？",
    "👉 320 能被 8 整除，先除比較好算。"
  ],
  common_mistakes:["320÷3×8。","乘除順序搞錯。"]
},
{
  id:"g5_national_exp_13", kind:"fraction_of_quantity", topic:"fraction_of_quantity",
  question:"學校有 540 位學生，其中 5/6 通過體適能檢測，通過的有幾位？",
  answer:"450",
  hints:[
    "⭐ 觀念提醒\n求全體的幾分之幾 → 數量 × 分數。",
    "🔍 列式引導\n列式：540 × 5/6",
    "📐 一步步算：\n① 540 ÷ 6 = 90\n② 90 × 5 = ？",
    "👉 先除後乘最簡便。"
  ],
  common_mistakes:["540÷5×6=648（分子分母搞反）。","90×5 進位算錯。"]
},
{
  id:"g5_national_exp_14", kind:"fraction_of_quantity", topic:"fraction_of_quantity",
  question:"果園收成 480 顆橘子，其中 7/12 已裝箱，裝箱了幾顆？",
  answer:"280",
  hints:[
    "⭐ 觀念提醒\n求部分量 = 全體 × 分數。",
    "🔍 列式引導\n列式：480 × 7/12",
    "📐 一步步算：\n① 480 ÷ 12 = 40\n② 40 × 7 = ？",
    "👉 480÷12=40，再乘 7。"
  ],
  common_mistakes:["480÷7×12。","480÷12 算錯。"]
},

// ═══ remaining_after_fraction (4) ═══
{
  id:"g5_national_exp_15", kind:"remaining_after_fraction", topic:"remaining_after_fraction",
  question:"一袋米有 630 公克，用了 3/7 煮飯，還剩幾公克？",
  answer:"360",
  hints:[
    "⭐ 觀念提醒\n用了 3/7 → 剩 4/7。",
    "🔍 列式引導\n用掉：630 × 3/7 = 270。\n剩：630 − 270",
    "📐 一步步算：\n① 630 ÷ 7 = 90\n② 90 × 3 = 270\n③ 630 − 270 = ？",
    "👉 也可以直接 630 × 4/7。"
  ],
  common_mistakes:["搞混用了的和剩下的。","630÷3×7 分子分母搞反。"]
},
{
  id:"g5_national_exp_16", kind:"remaining_after_fraction", topic:"remaining_after_fraction",
  question:"彩色筆一盒有 48 支，小華用了 5/8，還剩幾支？",
  answer:"18",
  hints:[
    "⭐ 觀念提醒\n用了 5/8 → 剩 3/8。",
    "🔍 列式引導\n用掉：48 × 5/8 = 30。\n剩：48 − 30",
    "📐 一步步算：\n① 48 ÷ 8 = 6\n② 6 × 5 = 30\n③ 48 − 30 = ？",
    "👉 也可以直接 48 × 3/8。"
  ],
  common_mistakes:["寫了用掉的量當答案。","48÷5×8 分子分母搞反。"]
},
{
  id:"g5_national_exp_17", kind:"remaining_after_fraction", topic:"remaining_after_fraction",
  question:"一條繩子長 84 公分，剪掉 4/7 做手工，剩幾公分？",
  answer:"36",
  hints:[
    "⭐ 觀念提醒\n剪掉 4/7 → 剩 3/7。",
    "🔍 列式引導\n剪掉：84 × 4/7 = 48。\n剩：84 − 48",
    "📐 一步步算：\n① 84 ÷ 7 = 12\n② 12 × 4 = 48\n③ 84 − 48 = ？",
    "👉 注意問剩下的不是剪掉的。"
  ],
  common_mistakes:["答成 48（那是剪掉的）。","84÷4×7 搞反。"]
},
{
  id:"g5_national_exp_18", kind:"remaining_after_fraction", topic:"remaining_after_fraction",
  question:"花店有 150 朵花，賣出 2/5 後，還剩幾朵？",
  answer:"90",
  hints:[
    "⭐ 觀念提醒\n賣出 2/5 → 剩 3/5。",
    "🔍 列式引導\n賣出：150 × 2/5 = 60。\n剩：150 − 60",
    "📐 一步步算：\n① 150 ÷ 5 = 30\n② 30 × 2 = 60\n③ 150 − 60 = ？",
    "👉 也可 150 × 3/5 = 90。"
  ],
  common_mistakes:["只算了賣出的。","150÷2×5 搞反。"]
},

// ═══ fraction_of_fraction (3) ═══
{
  id:"g5_national_exp_19", kind:"fraction_of_fraction", topic:"fraction_of_fraction",
  question:"一瓶牛奶有 5/6 公升，喝了其中的 3/5，喝了幾公升？",
  answer:"1/2",
  hints:[
    "⭐ 觀念提醒\n「其中的幾分之幾」→ 分數×分數。",
    "🔍 列式引導\n列式：5/6 × 3/5",
    "📐 一步步算：\n① 分子 5×3=15，分母 6×5=30\n② 15/30 約分 → ？",
    "👉 5 和 5 可以先約掉。"
  ],
  common_mistakes:["分數乘法規則搞混。","約分忘記做。"]
},
{
  id:"g5_national_exp_20", kind:"fraction_of_fraction", topic:"fraction_of_fraction",
  question:"一塊地有 3/4 公頃種菜，其中 2/3 種番茄，番茄佔整塊地的幾分之幾？",
  answer:"1/2",
  hints:[
    "⭐ 觀念提醒\n菜園的 2/3 種番茄 → 3/4 × 2/3。",
    "🔍 列式引導\n列式：3/4 × 2/3",
    "📐 一步步算：\n① 分子 3×2=6，分母 4×3=12\n② 6/12 約分 → ？",
    "👉 3 和 3 先約掉更簡單。"
  ],
  common_mistakes:["以為是 3/4 + 2/3。","約分不完全。"]
},
{
  id:"g5_national_exp_21", kind:"fraction_of_fraction", topic:"fraction_of_fraction",
  question:"繩子 4/9 公尺，用了其中 3/8 綁禮物，用了幾公尺？",
  answer:"1/6",
  hints:[
    "⭐ 觀念提醒\n「其中的 3/8」→ 乘法。",
    "🔍 列式引導\n列式：4/9 × 3/8",
    "📐 一步步算：\n① 分子 4×3=12，分母 9×8=72\n② 12/72 約分 → ？",
    "👉 12 和 72 最大公因數是 12。"
  ],
  common_mistakes:["分子分母乘法算錯。","約分不正確。"]
},

// ═══ volume_calculation (3) ═══
{
  id:"g5_national_exp_22", kind:"volume_calculation", topic:"volume_calculation",
  question:"一個長方體水族箱長 40 公分、寬 25 公分、高 30 公分，體積是多少立方公分？",
  answer:"30000",
  hints:[
    "⭐ 觀念提醒\n長方體體積 = 長 × 寬 × 高。",
    "🔍 列式引導\n列式：40 × 25 × 30",
    "📐 一步步算：\n① 40 × 25 = 1000\n② 1000 × 30 = ？",
    "👉 先挑容易算的兩個數相乘。"
  ],
  common_mistakes:["少乘了一個維度。","單位搞錯。"]
},
{
  id:"g5_national_exp_23", kind:"volume_calculation", topic:"volume_calculation",
  question:"正方體魔術方塊邊長 6 公分，體積是多少立方公分？",
  answer:"216",
  hints:[
    "⭐ 觀念提醒\n正方體體積 = 邊長 × 邊長 × 邊長。",
    "🔍 列式引導\n列式：6 × 6 × 6",
    "📐 一步步算：\n① 6 × 6 = 36\n② 36 × 6 = ？",
    "👉 正方體三個邊都一樣長。"
  ],
  common_mistakes:["6×6=36 就停了（那是面積）。","6×3=18（那是邊長之和）。"]
},
{
  id:"g5_national_exp_24", kind:"volume_calculation", topic:"volume_calculation",
  question:"一個長方體禮物盒長 15 公分、寬 12 公分、高 8 公分，體積是多少立方公分？",
  answer:"1440",
  hints:[
    "⭐ 觀念提醒\n長方體體積 = 長 × 寬 × 高。",
    "🔍 列式引導\n列式：15 × 12 × 8",
    "📐 一步步算：\n① 15 × 12 = 180\n② 180 × 8 = ？",
    "👉 也可以 15 × 8 = 120 再 × 12。"
  ],
  common_mistakes:["15×12 計算錯誤。","漏乘高度。"]
},

// ═══ decimal_multiplication (4) ═══
{
  id:"g5_national_exp_25", kind:"decimal_multiplication", topic:"decimal_multiplication",
  question:"一塊蛋糕重 0.45 公斤，買了 8 塊，共重幾公斤？",
  answer:"3.6",
  hints:[
    "⭐ 觀念提醒\n相同重量 × 數量 = 總重。",
    "🔍 列式引導\n列式：0.45 × 8",
    "📐 一步步算：\n① 45 × 8 = 360\n② 0.45 有 2 位小數\n③ 放回小數點 → ？",
    "👉 先算整數乘法再放小數點。"
  ],
  common_mistakes:["小數位數數錯。","45×8 算錯。"]
},
{
  id:"g5_national_exp_26", kind:"decimal_multiplication", topic:"decimal_multiplication",
  question:"鐵絲每公尺 12.6 元，買 5 公尺要多少元？",
  answer:"63",
  hints:[
    "⭐ 觀念提醒\n單價 × 數量 = 總價。",
    "🔍 列式引導\n列式：12.6 × 5",
    "📐 一步步算：\n① 126 × 5 = 630\n② 12.6 有 1 位小數\n③ 放回小數點 → ？",
    "👉 630 放 1 位小數 = 63.0 = 整數。"
  ],
  common_mistakes:["小數點放錯位置。","126×5 算錯。"]
},
{
  id:"g5_national_exp_27", kind:"decimal_multiplication", topic:"decimal_multiplication",
  question:"一條彩帶長 2.35 公尺，需要 4 條，共幾公尺？",
  answer:"9.4",
  hints:[
    "⭐ 觀念提醒\n每條 × 條數 = 總長。",
    "🔍 列式引導\n列式：2.35 × 4",
    "📐 一步步算：\n① 235 × 4 = 940\n② 2.35 有 2 位小數\n③ 放回小數點 → ？",
    "👉 940 放 2 位小數 = 9.40 = 9.4。"
  ],
  common_mistakes:["235×4 算錯。","小數位數算成 3 位。"]
},
{
  id:"g5_national_exp_28", kind:"decimal_multiplication", topic:"decimal_multiplication",
  question:"每公升汽油 32.5 元，加了 20 公升要付多少元？",
  answer:"650",
  hints:[
    "⭐ 觀念提醒\n單價 × 數量 = 總價。",
    "🔍 列式引導\n列式：32.5 × 20",
    "📐 一步步算：\n① 325 × 20 = 6500\n② 32.5 有 1 位小數\n③ 放回小數點 → ？",
    "👉 6500 放 1 位小數 = 650.0 = 整數。"
  ],
  common_mistakes:["小數點位置錯。","325×20 算錯。"]
},

// ═══ division_application (4) ═══
{
  id:"g5_national_exp_29", kind:"division_application", topic:"division_application",
  question:"有 195 本練習簿要分給 15 位同學，每人幾本？",
  answer:"13",
  hints:[
    "⭐ 觀念提醒\n平均分配 → 除法。",
    "🔍 列式引導\n列式：195 ÷ 15",
    "📐 一步步算：\n① 15 × 13 = 195\n② 每人 = ？\n驗算：？ × 15 = 195 ✅",
    "👉 可以先試 15×10=150，再逐步調整。"
  ],
  common_mistakes:["直式除法商算錯。","被除數與除數搞反。"]
},
{
  id:"g5_national_exp_30", kind:"division_application", topic:"division_application",
  question:"工廠生產了 342 個零件，每箱裝 18 個，最多可以裝幾箱？",
  answer:"19",
  hints:[
    "⭐ 觀念提醒\n等分裝箱 → 除法。",
    "🔍 列式引導\n列式：342 ÷ 18 = 19…0",
    "📐 一步步算：\n① 18 × 19 = 342\n② 可裝 = ？\n驗算：？ × 18 = 342 ✅",
    "👉 也可先試 18×20=360 太多，再減。"
  ],
  common_mistakes:["除法筆算時商的位數搞錯。","18×19 計算錯誤。"]
},
{
  id:"g5_national_exp_31", kind:"division_application", topic:"division_application",
  question:"校外教學 47 名學生要分組，每組 6 人，至少要分幾組？",
  answer:"8",
  hints:[
    "⭐ 觀念提醒\n有餘數時「至少」要多一組。",
    "🔍 列式引導\n47 ÷ 6 = 7…5，剩 5 人要再一組。",
    "📐 一步步算：\n① 47 ÷ 6 = 7 餘 5\n② 7 + 1 = ？",
    "👉 至少 → 有餘數就要無條件進入。"
  ],
  common_mistakes:["答 7 忘了剩下的人。","除法餘數算錯。"]
},
{
  id:"g5_national_exp_32", kind:"division_application", topic:"division_application",
  question:"媽媽有 156 元，要買每個 12 元的飯糰，最多可以買幾個？",
  answer:"13",
  hints:[
    "⭐ 觀念提醒\n最多可以買 → 除法取商。",
    "🔍 列式引導\n列式：156 ÷ 12",
    "📐 一步步算：\n① 12 × 13 = 156\n② 可買 = ？\n驗算：？ × 12 = 156 ✅",
    "👉 「最多」→ 有餘數時只取商（無條件捨去）。"
  ],
  common_mistakes:["除法算錯。","搞混「至少」和「最多」的取整方式。"]
},

// ═══ area_difference (4) ═══
{
  id:"g5_national_exp_33", kind:"area_difference", topic:"area_difference",
  question:"一塊長方形草皮長 20 公尺、寬 15 公尺，中間有一個正方形花壇邊長 5 公尺，草皮面積是多少平方公尺？",
  answer:"275",
  hints:[
    "⭐ 觀念提醒\n草皮面積 = 長方形面積 − 正方形面積。",
    "🔍 列式引導\n列式：20×15 − 5×5",
    "📐 一步步算：\n① 20 × 15 = 300\n② 5 × 5 = 25\n③ 300 − 25 = ？",
    "👉 扣掉中間的花壇。"
  ],
  common_mistakes:["忘記減花壇面積。","正方形面積算成 5×4。"]
},
{
  id:"g5_national_exp_34", kind:"area_difference", topic:"area_difference",
  question:"甲長方形長 28 公尺、寬 16 公尺，乙長方形長 22 公尺、寬 13 公尺，甲的面積比乙多幾平方公尺？",
  answer:"162",
  hints:[
    "⭐ 觀念提醒\n分別算面積再相減。",
    "🔍 列式引導\n甲＝28×16＝448，乙＝22×13＝286，差＝448−286",
    "📐 一步步算：\n① 28 × 16 = 448\n② 22 × 13 = 286\n③ 448 − 286 = ？",
    "👉 大面積減小面積。"
  ],
  common_mistakes:["28×16 或 22×13 算錯。","減法搞反。"]
},
{
  id:"g5_national_exp_35", kind:"area_difference", topic:"area_difference",
  question:"正方形紙邊長 16 公分，剪掉一個長 10 公分寬 6 公分的長方形，剩餘面積是多少平方公分？",
  answer:"196",
  hints:[
    "⭐ 觀念提醒\n剩餘 = 正方形面積 − 長方形面積。",
    "🔍 列式引導\n列式：16×16 − 10×6",
    "📐 一步步算：\n① 16 × 16 = 256\n② 10 × 6 = 60\n③ 256 − 60 = ？",
    "👉 正方形面積 = 邊長²。"
  ],
  common_mistakes:["16×16 算成 246。","長方形面積少乘一邊。"]
},
{
  id:"g5_national_exp_36", kind:"area_difference", topic:"area_difference",
  question:"教室地板長 10 公尺、寬 8 公尺，講台佔了一個長 4 公尺、寬 2 公尺的長方形，扣除講台後地板面積是多少平方公尺？",
  answer:"72",
  hints:[
    "⭐ 觀念提醒\n扣除 = 大面積 − 小面積。",
    "🔍 列式引導\n列式：10×8 − 4×2",
    "📐 一步步算：\n① 10 × 8 = 80\n② 4 × 2 = 8\n③ 80 − 8 = ？",
    "👉 地板面積 − 講台面積。"
  ],
  common_mistakes:["忘記減講台。","4×2 算錯。"]
},

// ═══ unit_convert (4) ═══
{
  id:"g5_national_exp_37", kind:"unit_convert", topic:"unit_convert",
  question:"一條河長 2.8 公里，等於多少公尺？",
  answer:"2800",
  hints:[
    "⭐ 觀念提醒\n1 公里 = 1000 公尺。",
    "🔍 列式引導\n列式：2.8 × 1000",
    "📐 一步步算：\n① 2.8 × 1000\n② 小數點右移 3 位 → ？",
    "👉 公里→公尺 × 1000。"
  ],
  common_mistakes:["乘錯倍率。","小數點移動位數搞錯。"]
},
{
  id:"g5_national_exp_38", kind:"unit_convert", topic:"unit_convert",
  question:"一隻大象重 3600 公斤，等於幾噸？",
  answer:"3.6",
  hints:[
    "⭐ 觀念提醒\n1 噸 = 1000 公斤。",
    "🔍 列式引導\n列式：3600 ÷ 1000",
    "📐 一步步算：\n① 3600 ÷ 1000\n② 小數點左移 3 位 → ？",
    "👉 公斤→噸，除以 1000。"
  ],
  common_mistakes:["除以 100（噸和公斤的比是 1000）。","小數點移錯方向。"]
},
{
  id:"g5_national_exp_39", kind:"unit_convert", topic:"unit_convert",
  question:"3 公頃 50 公畝等於幾平方公尺？",
  answer:"35000",
  hints:[
    "⭐ 觀念提醒\n1 公頃 = 10000 平方公尺，1 公畝 = 100 平方公尺。",
    "🔍 列式引導\n列式：3 × 10000 + 50 × 100",
    "📐 一步步算：\n① 3 × 10000 = 30000\n② 50 × 100 = 5000\n③ 30000 + 5000 = ？",
    "👉 分開轉換再相加。"
  ],
  common_mistakes:["公畝和公頃的換算搞混。","忘了相加。"]
},
{
  id:"g5_national_exp_40", kind:"unit_convert", topic:"unit_convert",
  question:"一杯水有 250 毫升，等於幾公升？",
  answer:"0.25",
  hints:[
    "⭐ 觀念提醒\n1 公升 = 1000 毫升。",
    "🔍 列式引導\n列式：250 ÷ 1000",
    "📐 一步步算：\n① 250 ÷ 1000\n② 小數點左移 3 位 → ？",
    "👉 毫升→公升，除以 1000。"
  ],
  common_mistakes:["除以 100 而非 1000。","小數點放錯。"]
},

// ═══ average_division (4) ═══
{
  id:"g5_national_exp_41", kind:"average_division", topic:"average_division",
  question:"4 位同學的身高分別是 138、142、145、135 公分，平均身高幾公分？",
  answer:"140",
  hints:[
    "⭐ 觀念提醒\n平均 = 總和 ÷ 人數。",
    "🔍 列式引導\n列式：(138+142+145+135) ÷ 4",
    "📐 一步步算：\n① 138+142+145+135 = 560\n② 560 ÷ 4 = ？",
    "👉 答案應在 135～145 之間。"
  ],
  common_mistakes:["加總算錯。","除以 5（人數數錯）。"]
},
{
  id:"g5_national_exp_42", kind:"average_division", topic:"average_division",
  question:"小明 3 天看的書頁數分別是 36、42、48 頁，平均每天看幾頁？",
  answer:"42",
  hints:[
    "⭐ 觀念提醒\n平均 = 總頁數 ÷ 天數。",
    "🔍 列式引導\n列式：(36+42+48) ÷ 3",
    "📐 一步步算：\n① 36+42+48 = 126\n② 126 ÷ 3 = ？",
    "👉 驗算：答案 × 3 = 126。"
  ],
  common_mistakes:["加法進位錯誤。","除以 2。"]
},
{
  id:"g5_national_exp_43", kind:"average_division", topic:"average_division",
  question:"5 顆蘋果重量分別是 180、195、210、170、195 公克，平均每顆幾公克？",
  answer:"190",
  hints:[
    "⭐ 觀念提醒\n平均 = 總重 ÷ 顆數。",
    "🔍 列式引導\n列式：(180+195+210+170+195) ÷ 5",
    "📐 一步步算：\n① 180+195+210+170+195 = 950\n② 950 ÷ 5 = ？",
    "👉 先湊整數再加比較不容易出錯。"
  ],
  common_mistakes:["加總時漏算一顆。","950÷5 算錯。"]
},
{
  id:"g5_national_exp_44", kind:"average_division", topic:"average_division",
  question:"期中考 5 科成績分別是 78、92、86、88、81，平均幾分？",
  answer:"85",
  hints:[
    "⭐ 觀念提醒\n平均 = 總分 ÷ 科數。",
    "🔍 列式引導\n列式：(78+92+86+88+81) ÷ 5",
    "📐 一步步算：\n① 78+92+86+88+81 = 425\n② 425 ÷ 5 = ？",
    "👉 答案應在 78～92 之間。"
  ],
  common_mistakes:["加總錯誤。","除錯科目數。"]
},

// ═══ perimeter_fence (3) ═══
{
  id:"g5_national_exp_45", kind:"perimeter_fence", topic:"perimeter_fence",
  question:"長方形花圃長 18 公尺、寬 9 公尺，四周圍上柵欄，需要多少公尺的柵欄？",
  answer:"54",
  hints:[
    "⭐ 觀念提醒\n四周圍柵欄 = 周長。",
    "🔍 列式引導\n列式：(18+9) × 2",
    "📐 一步步算：\n① 18 + 9 = 27\n② 27 × 2 = ？",
    "👉 長方形周長 = (長+寬) × 2。"
  ],
  common_mistakes:["18×9=162（那是面積）。","忘記乘 2。"]
},
{
  id:"g5_national_exp_46", kind:"perimeter_fence", topic:"perimeter_fence",
  question:"正方形庭院邊長 15 公尺，有兩面靠牆，需要幾公尺的圍牆？",
  answer:"30",
  hints:[
    "⭐ 觀念提醒\n兩面靠牆 → 圍 2 面。",
    "🔍 列式引導\n列式：15 × 2",
    "📐 一步步算：\n① 正方形 4 面各 15 公尺\n② 扣掉靠牆的 2 面\n③ 15 × 2 = ？",
    "👉 靠牆的面不用圍。"
  ],
  common_mistakes:["15×4=60（沒扣靠牆的）。","只扣一面。"]
},
{
  id:"g5_national_exp_47", kind:"perimeter_fence", topic:"perimeter_fence",
  question:"長方形跑道長 60 公尺、寬 25 公尺，跑 3 圈共幾公尺？",
  answer:"510",
  hints:[
    "⭐ 觀念提醒\n一圈 = 周長，跑 3 圈 = 周長 × 3。",
    "🔍 列式引導\n一圈 = (60+25) × 2 = 170。\n列式：170 × 3",
    "📐 一步步算：\n① (60+25) × 2 = 170\n② 170 × 3 = ？",
    "👉 先算一圈再乘圈數。"
  ],
  common_mistakes:["只算一圈的長度。","周長忘記乘 2。"]
},

// ═══ d_div_int (3) ═══
{
  id:"g5_national_exp_48", kind:"d_div_int", topic:"d_div_int",
  question:"一段繩子長 12.6 公尺，平均剪成 7 段，每段多少公尺？",
  answer:"1.8",
  hints:[
    "⭐ 觀念提醒\n平均分 → 除法。",
    "🔍 列式引導\n列式：12.6 ÷ 7",
    "📐 一步步算：\n① 12 ÷ 7 = 1 餘 5\n② 56 ÷ 7 = 8\n③ 商 = ？\n驗算：？ × 7 = 12.6 ✅",
    "👉 小數除法小數點要對齊。"
  ],
  common_mistakes:["小數點放錯。","12÷7 的餘數帶下來搞錯。"]
},
{
  id:"g5_national_exp_49", kind:"d_div_int", topic:"d_div_int",
  question:"18.9 公升的水平均倒入 9 個杯子，每杯幾公升？",
  answer:"2.1",
  hints:[
    "⭐ 觀念提醒\n平均分 → 除法。",
    "🔍 列式引導\n列式：18.9 ÷ 9",
    "📐 一步步算：\n① 18 ÷ 9 = 2\n② 9 ÷ 9 = 1\n③ 商 = ？\n驗算：？ × 9 = 18.9 ✅",
    "👉 這題剛好整除。"
  ],
  common_mistakes:["小數點位置錯。","18÷9 後忘了十分位。"]
},
{
  id:"g5_national_exp_50", kind:"d_div_int", topic:"d_div_int",
  question:"一袋糖果重 6.48 公斤，分成 8 袋，每袋幾公斤？",
  answer:"0.81",
  hints:[
    "⭐ 觀念提醒\n平均分 → 除法。商可能小於 1。",
    "🔍 列式引導\n列式：6.48 ÷ 8",
    "📐 一步步算：\n① 6 ÷ 8 不夠，商個位 0\n② 64 ÷ 8 = 8\n③ 8 ÷ 8 = 1\n④ 商 = ？",
    "👉 個位不夠除就寫 0，繼續除。"
  ],
  common_mistakes:["忘記寫 0 在個位。","小數點放錯位置。"]
},

// ═══ surface_area_rect_prism (2) ═══
{
  id:"g5_national_exp_51", kind:"surface_area_rect_prism", topic:"surface_area_rect_prism",
  question:"一個長方體長 9 公分、寬 7 公分、高 5 公分，表面積是多少平方公分？",
  answer:"286",
  hints:[
    "⭐ 觀念提醒\n表面積 = 2(長×寬 + 長×高 + 寬×高)。",
    "🔍 列式引導\n列式：2 × (9×7 + 9×5 + 7×5)",
    "📐 一步步算：\n① 9×7=63，9×5=45，7×5=35\n② 63+45+35=143\n③ 143×2 = ？",
    "👉 三組面積先各算再加再乘 2。"
  ],
  common_mistakes:["忘記乘 2。","三個面積加總錯誤。"]
},
{
  id:"g5_national_exp_52", kind:"surface_area_rect_prism", topic:"surface_area_rect_prism",
  question:"正方體邊長 7 公分，表面積是多少平方公分？",
  answer:"294",
  hints:[
    "⭐ 觀念提醒\n正方體表面積 = 6 × 邊長 × 邊長。",
    "🔍 列式引導\n列式：6 × 7 × 7",
    "📐 一步步算：\n① 7 × 7 = 49\n② 49 × 6 = ？",
    "👉 49×6：可拆成 50×6 − 1×6 = 300 − 6。"
  ],
  common_mistakes:["7×7 算成 14。","6×49 計算錯誤。"]
},

// ═══ percent_of (2) ═══
{
  id:"g5_national_exp_53", kind:"percent_of", topic:"percent_of",
  question:"農場有 600 隻鴨，其中 35% 是母鴨，母鴨有幾隻？",
  answer:"210",
  hints:[
    "⭐ 觀念提醒\n求百分比 → 數量 × 百分比。",
    "🔍 列式引導\n列式：600 × 35% = 600 × 0.35",
    "📐 一步步算：\n① 600 × 0.35\n② = 600 × 35 ÷ 100\n③ = 21000 ÷ 100 = ？",
    "👉 百分比先化成小數再乘。"
  ],
  common_mistakes:["35% 沒有÷100。","600×35 忘了÷100。"]
},
{
  id:"g5_national_exp_54", kind:"percent_of", topic:"percent_of",
  question:"一本書有 250 頁，小明已經讀了 72%，讀了幾頁？",
  answer:"180",
  hints:[
    "⭐ 觀念提醒\n求某數的百分率 → 乘法。",
    "🔍 列式引導\n列式：250 × 72% = 250 × 0.72",
    "📐 一步步算：\n① 250 × 0.72\n② = 250 × 72 ÷ 100\n③ = 18000 ÷ 100 = ？",
    "👉 也可以 250 × 0.7 + 250 × 0.02 = 175 + 5。"
  ],
  common_mistakes:["72% 換算成 7.2。","250×72 忘記÷100。"]
}

]; // END NEW_QS

// ─── Main ────────────────────────────────────────────────────
for (const bp of BANK_PATHS) {
  if (!fs.existsSync(bp)) {
    console.error('NOT FOUND:', bp);
    process.exit(1);
  }
  const src = fs.readFileSync(bp, 'utf8');
  const window = {};
  new Function('window', src)(window);
  const bank = window.FRACTION_WORD_G5_BANK;
  if (!bank) { console.error('Cannot parse bank in', bp); process.exit(1); }

  console.log(bp + ': existing ' + bank.length + ' questions');
  const existingIds = new Set(bank.map(q => q.id));
  const toAdd = NEW_QS.filter(q => !existingIds.has(q.id));
  const newBank = [...bank, ...toAdd];
  console.log('  → new total: ' + newBank.length);

  const out = 'window.FRACTION_WORD_G5_BANK = ' + JSON.stringify(newBank, null, 2) + ';\n';
  fs.writeFileSync(bp, out, 'utf8');
  console.log('  WRITTEN ' + bp);
}
console.log('\nDone. Run validator to verify.');
