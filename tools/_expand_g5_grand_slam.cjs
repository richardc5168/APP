#!/usr/bin/env node
// Expand g5-grand-slam from 188 → 200 questions (+12)
// Run: node tools/_expand_g5_grand_slam.cjs
"use strict";
var fs = require("fs");
var path = require("path");

var SRC = path.join(__dirname, "..", "docs", "g5-grand-slam", "bank.js");
var DIST = path.join(__dirname, "..", "dist_ai_math_web_pages", "docs", "g5-grand-slam", "bank.js");
var TOPIC = "國小五年級｜大滿貫複習";

function makeQ(id, kind, diff, question, answer, hints, explanation, cm) {
  return {
    id: id,
    kind: kind,
    topic: TOPIC,
    difficulty: diff,
    question: question,
    answer: String(answer),
    hints: hints,
    steps: [],
    meta: {},
    explanation: explanation,
    common_mistakes: cm
  };
}

var newQs = [];

// Add to under-represented kinds (2-3 count ones)
// line_omit_rule +2, area_parallelogram +2, area_triangle +1, surface_area_cube +1,
// cm3_to_ml +1, solve_x_div_d +1, symmetry_axes +1, cheng_increase +1,
// time_multiply +1, percent_to_ppm +1 = 12

// ---- line_omit_rule +2 ----
newQs.push(makeQ(
  "g5gs_line_omit_10", "line_omit_rule", "easy",
  "（折線圖）一個折線圖的縱軸從 0 開始，數據都在 85~100 之間。為了讓差異更明顯，可以怎麼做？",
  "省略 0 到 80 的部分",
  [
    "觀念：折線圖可以用「省略符號」省掉一段沒有數據的區間。",
    "做法：找出數據最小值附近，把下方空白省略。",
    "📐 想一想：\n① 數據在 85~100\n② 0~80 沒有數據\n③ 可以省略哪段？\n想好再回答 ✅",
    "📌 常見錯誤：省略了有數據的區間，導致折線圖失真。只能省略「沒有數據」的區間！"
  ],
  "省略 0~80 的部分，讓 85~100 的差異更明顯。",
  ["省略了有數據的區間。", "忘了標示省略符號。"]
));

newQs.push(makeQ(
  "g5gs_line_omit_11", "line_omit_rule", "easy",
  "（折線圖）折線圖上出現鋸齒狀波浪符號（〰），代表什麼意思？",
  "省略了一段數值",
  [
    "觀念：鋸齒狀波浪符號是「省略符號」，代表那段數值被省略了。",
    "做法：直接想省略符號的定義。",
    "📐 想一想：\n① 波浪符號出現在數軸上\n② 表示那段距離被跳過了\n③ 為什麼要跳過？ ✅",
    "📌 常見錯誤：以為波浪符號代表「數據波動」。它只是代表省略了一段！"
  ],
  "波浪符號代表省略了中間一段數值。",
  ["以為代表數據波動。", "不知道符號的意思。"]
));

// ---- area_parallelogram +2 ----
newQs.push(makeQ(
  "g5gs_geo_para_15", "area_parallelogram", "easy",
  "（面積）一個平行四邊形，底 14 公分，高 9 公分，面積是多少平方公分？",
  126,
  [
    "觀念：平行四邊形面積 = 底 × 高。",
    "列式：14 × 9。",
    "📐 動手算：\n① 底 × 高 = 14 × 9\n記得寫 cm² ✅",
    "📌 常見錯誤：用斜邊長來算（要用「高」，也就是底邊到對邊的垂直距離）！"
  ],
  "14 × 9 = 126（cm²）。",
  ["用斜邊長而不是高來算。", "單位寫成 cm 而不是 cm²。"]
));

newQs.push(makeQ(
  "g5gs_geo_para_16", "area_parallelogram", "medium",
  "（面積）一個平行四邊形面積是 108 平方公分，底 12 公分，高是多少公分？",
  9,
  [
    "觀念：面積 = 底 × 高，反求高就是 高 = 面積 ÷ 底。",
    "列式：108 ÷ 12。",
    "📐 動手算：\n① 高 = 面積 ÷ 底\n② 108 ÷ 12\n記得寫公分 ✅",
    "📌 常見錯誤：除法方向搞反（用底÷面積）。高 = 面積 ÷ 底！"
  ],
  "108 ÷ 12 = 9（公分）。",
  ["除法方向搞反。", "計算粗心。"]
));

// ---- area_triangle +1 ----
newQs.push(makeQ(
  "g5gs_geo_tri_14", "area_triangle", "easy",
  "（面積）一個三角形，底 16 公分，高 7 公分，面積是多少平方公分？",
  56,
  [
    "觀念：三角形面積 = 底 × 高 ÷ 2。",
    "列式：16 × 7 ÷ 2。",
    "📐 動手算：\n① 底 × 高 = 16 × 7 = 112\n② 112 ÷ 2\n記得寫 cm² ✅",
    "📌 常見錯誤：忘了 ÷ 2（那是平行四邊形的面積，不是三角形）！"
  ],
  "16 × 7 ÷ 2 = 56（cm²）。",
  ["忘了除以 2。", "底和高搞混了。"]
));

// ---- surface_area_cube +1 ----
newQs.push(makeQ(
  "g5gs_sa_cube_08", "surface_area_cube", "easy",
  "（表面積）一個正方體的邊長是 7 公分，表面積是多少平方公分？",
  294,
  [
    "觀念：正方體有 6 個相同的正方形面，表面積 = 6 × 邊長²。",
    "列式：6 × 7 × 7。",
    "📐 動手算：\n① 一面面積 = 7 × 7 = 49\n② 表面積 = 6 × 49\n記得寫 cm² ✅",
    "📌 常見錯誤：只算了一面或四面。正方體有 6 個面！"
  ],
  "6 × 7² = 6 × 49 = 294（cm²）。",
  ["面的數量算錯。", "邊長平方算錯。"]
));

// ---- cm3_to_ml +1 ----
newQs.push(makeQ(
  "g5gs_vol_cm3ml_12", "cm3_to_ml", "easy",
  "（容量）350 立方公分（cm³）等於多少毫升（mL）？",
  350,
  [
    "觀念：1 cm³ = 1 mL，體積和容量可以直接換算。",
    "做法：直接看數字即可。",
    "📐 想一想：\n① 1 cm³ = 1 mL\n② 所以 350 cm³ = ？ mL\n直接對應 ✅",
    "📌 常見錯誤：以為要乘或除以某個數。1 cm³ 就是 1 mL，不用換算！"
  ],
  "350 cm³ = 350 mL。",
  ["以為要乘以 1000。", "混淆了 cm³ 和 m³。"]
));

// ---- solve_x_div_d +1 ----
newQs.push(makeQ(
  "g5gs_alg_div_10", "solve_x_div_d", "medium",
  "（解方程）x ÷ 9 = 7，x = ?",
  63,
  [
    "觀念：x ÷ a = b → x = b × a。",
    "列式：x = 7 × 9。",
    "📐 動手算：\n① 兩邊同乘 9\n② x = 7 × 9\n算完記得回頭檢查 ✅",
    "📌 常見錯誤：用除法（7 ÷ 9）而不是乘法。x ÷ a = b → x = b × a！"
  ],
  "x = 7 × 9 = 63。",
  ["乘除搞反了。", "算錯乘法。"]
));

// ---- symmetry_axes +1 ----
newQs.push(makeQ(
  "g5gs_sym_axes_11", "symmetry_axes", "easy",
  "（對稱）一個正六邊形有幾條對稱軸？",
  6,
  [
    "觀念：正 n 邊形有 n 條對稱軸。",
    "做法：正六邊形 = 正 6 邊形，所以有 6 條。",
    "📐 想一想：\n① 正多邊形的對稱軸：頂點到對邊中點，或兩頂點連線\n② 正六邊形有幾條？ ✅",
    "📌 常見錯誤：以為只有 3 條（只數了頂點到對面的線）。正六邊形有 6 條對稱軸！"
  ],
  "正六邊形有 6 條對稱軸。",
  ["只數了一半。", "跟正方形搞混了。"]
));

// ---- cheng_increase +1 ----
newQs.push(makeQ(
  "g5gs_rp_cheng_11", "cheng_increase", "medium",
  "（成數）一件商品原價 500 元，加價二成出售，售價是多少元？",
  600,
  [
    "觀念：加幾成 = 原價 × (1 + 成數/10)。一成 = 10%。",
    "列式：500 × (1 + 0.2) = 500 × 1.2。",
    "📐 動手算：\n① 二成 = 20% = 0.2\n② 售價 = 500 × 1.2\n算完記得回頭檢查 ✅",
    "📌 常見錯誤：只算了加的部分（500 × 0.2 = 100），沒加回原價。售價 = 原價 + 加的！"
  ],
  "500 × 1.2 = 600（元）。",
  ["只算了加的部分。", "成的換算搞錯。"]
));

// ---- time_multiply +1 ----
newQs.push(makeQ(
  "g5gs_time_mul_10", "time_multiply", "medium",
  "（時間計算）做一道菜需要 25 分鐘，連續做 4 道菜共需要多少小時多少分鐘？",
  "1小時40分鐘",
  [
    "觀念：先算總分鐘數，再換算成小時和分鐘。",
    "列式：25 × 4 = 100 分鐘 → 換算。",
    "📐 動手算：\n① 25 × 4 = 100 分鐘\n② 100 ÷ 60 = 1...40\n③ 1 小時 40 分鐘 ✅",
    "📌 常見錯誤：60 分 = 1 小時搞成 100 分 = 1 小時。時間是 60 進位！"
  ],
  "25 × 4 = 100 分鐘 = 1 小時 40 分鐘。",
  ["用 100 進位而不是 60 進位。", "乘法算錯。"]
));

// ---- percent_to_ppm +1 ----
newQs.push(makeQ(
  "g5gs_rp_ppm_12", "percent_to_ppm", "medium",
  "（百萬分率）3% 等於多少 ppm（百萬分之幾）？",
  30000,
  [
    "觀念：1% = 10,000 ppm。百萬分率 = 百分率 × 10,000。",
    "列式：3 × 10,000。",
    "📐 動手算：\n① 1% = 10,000 ppm\n② 3% = 3 × 10,000\n算完記得回頭檢查 ✅",
    "📌 常見錯誤：乘以 100 而不是 10,000。ppm 是百萬分之一，% 是百分之一，差 10,000 倍！"
  ],
  "3 × 10,000 = 30,000 ppm。",
  ["乘錯倍數。", "% 和 ppm 的關係搞混。"]
));

// ============ append & write ============
var src = fs.readFileSync(SRC, "utf8");
var closeIdx = src.lastIndexOf("];");
if (closeIdx === -1) { console.error("Cannot find ]; in bank.js"); process.exit(1); }

var before = src.substring(0, closeIdx);
if (before.trimEnd().slice(-1) !== ",") {
  before = before.trimEnd() + ",\n";
}

var newBlock = newQs.map(function(q) {
  return JSON.stringify(q, null, 2);
}).join(",\n");

var after = before + newBlock + "\n];\n";
fs.writeFileSync(SRC, after, "utf8");
fs.writeFileSync(DIST, after, "utf8");

console.log("Added:", newQs.length);
console.log("New total:", 188 + newQs.length);
console.log("Synced to dist.");
