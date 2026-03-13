#!/usr/bin/env node
// Expand volume-g5 from 147 → 200 questions (+53)
// Run: node tools/_expand_volume_g5.cjs
"use strict";
var fs = require("fs");
var path = require("path");

var SRC = path.join(__dirname, "..", "docs", "volume-g5", "bank.js");
var DIST = path.join(
  __dirname, "..", "dist_ai_math_web_pages", "docs", "volume-g5", "bank.js"
);
var TOPIC = "國小五年級｜體積（長方體/正方體）";

function pad(n) { return String(n).padStart(2, "0"); }

// ---------- helpers ----------
function makeQ(id, kind, diff, question, answer, hints, explanation, cm, unit) {
  return {
    id: id,
    kind: kind,
    topic: TOPIC,
    difficulty: diff,
    question: question,
    answer: String(answer),
    hints: hints,
    steps: [],
    meta: { unit: unit || "立方公分（cm³）" },
    explanation: explanation,
    common_mistakes: cm
  };
}

// Standard rect_cm3 hint template
function rectHints(l, w, h, ans) {
  var step1 = l + "×" + w;
  var base = l * w;
  return [
    "觀念：長方體的體積 V = 長 × 寬 × 高。",
    "列式：" + l + "×" + w + "×" + h + "。",
    "📐 動手算：\n① 長×寬×高 = " + l + " × " + w + " × " + h +
      "\n② 先算 " + step1 + " = " + base +
      "\n③ 再算 " + base + " × " + h +
      "\n記得寫 cm³ 或 m³ ✅",
    "📌 常見錯誤：把「長×寬」算完就停下來，忘了再乘「高」。體積一定有三個維度"
      + "相乘！"
  ];
}

function cubeHints(e) {
  return [
    "⭐ 觀念提醒\n正方體每邊都一樣長，體積 = 邊長³（邊長×邊長×邊長）。",
    "列式：" + e + " × " + e + " × " + e + "。",
    "📐 動手算：\n① " + e + "×" + e + " = " + (e*e) +
      "\n② " + (e*e) + " × " + e +
      "\n記得寫 cm³ 或 m³ ✅",
    "📌 常見錯誤：把 " + e + "×3 當結果（邊長乘 3 不是體積）。體積 = 邊長³。"
  ];
}

function baseHints(area, h) {
  return [
    "觀念：體積 V = 底面積 × 高。",
    "列式：" + area + " × " + h + "。",
    "📐 動手算：\n① 底面積 × 高 = " + area + " × " + h +
      "\n記得寫 cm³ ✅",
    "📌 常見錯誤：底面積和高的單位不統一就直接乘。一定要確認單位相同再算！"
  ];
}

function CM_VOL() {
  return [
    "只算了兩個維度（面積），忘了乘第三個維度。",
    "單位寫成 cm²（平方）而不是 cm³（立方）。"
  ];
}

function CM_UNIT() {
  return [
    "忘了把 m 換成 cm（或反過來），直接相乘。",
    "單位換算倍數搞錯，1 m³ = 1,000,000 cm³ 不是 100 或 1000。"
  ];
}

// ============ new questions ============
var newQs = [];

// ---- composite +4 (id 17-20) ----
var compData = [
  { n: 17, aL:10, aW:6, aH:8, bL:10, bW:4, bH:5 },
  { n: 18, aL:15, aW:8, aH:6, bL:15, bW:5, bH:4 },
  { n: 19, aL:12, aW:7, aH:9, bL:12, bW:3, bH:9 },
  { n: 20, aL:20, aW:10, aH:5, bL:20, bW:6, bH:3 }
];
compData.forEach(function(d) {
  var va = d.aL * d.aW * d.aH;
  var vb = d.bL * d.bW * d.bH;
  var ans = va + vb;
  newQs.push(makeQ(
    "vg5_comp_" + pad(d.n), "composite", "medium",
    "（複合形體）把形體分成兩個長方體來算：\n" +
    "A：長 " + d.aL + " 公分、寬 " + d.aW + " 公分、高 " + d.aH + " 公分\n" +
    "B：長 " + d.bL + " 公分、寬 " + d.bW + " 公分、高 " + d.bH + " 公分\n" +
    "這個複合形體的總體積是多少立方公分？",
    ans,
    [
      "觀念：複合形體先分解成幾個長方體/正方體，各自算體積再相加。",
      "列式：A 體積 + B 體積 = " + d.aL + "×" + d.aW + "×" + d.aH + " + " +
        d.bL + "×" + d.bW + "×" + d.bH + "。",
      "📐 動手算：\n① A = " + d.aL + "×" + d.aW + "×" + d.aH + " = " + va +
        "\n② B = " + d.bL + "×" + d.bW + "×" + d.bH + " = " + vb +
        "\n③ 總體積 = A + B\n記得寫 cm³ ✅",
      "📌 常見錯誤：只算了其中一塊就當答案，忘了把兩個部分加起來。"
    ],
    "A = " + va + "，B = " + vb + "，總體積 = " + ans + "（cm³）。",
    ["只算了一塊長方體就停下來。", "合併時把加法搞成乘法。"]
  ));
});

// ---- composite3 +6 (id 13-18) ----
var comp3Data = [
  { n:13, a:[8,6,4], b:[8,3,4], c:[8,4,2] },
  { n:14, a:[10,5,6], b:[10,3,6], c:[10,2,3] },
  { n:15, a:[12,8,5], b:[12,4,5], c:[12,3,3] },
  { n:16, a:[15,6,4], b:[15,3,4], c:[15,2,2] },
  { n:17, a:[9,7,5], b:[9,4,5], c:[9,3,3] },
  { n:18, a:[14,8,6], b:[14,5,6], c:[14,3,4] }
];
comp3Data.forEach(function(d) {
  var va = d.a[0]*d.a[1]*d.a[2];
  var vb = d.b[0]*d.b[1]*d.b[2];
  var vc = d.c[0]*d.c[1]*d.c[2];
  var ans = va + vb + vc;
  function dims(arr) { return "長 " + arr[0] + " 公分、寬 " + arr[1] + " 公分、高 " + arr[2] + " 公分"; }
  newQs.push(makeQ(
    "vg5_comp3_" + pad(d.n), "composite3", "medium",
    "（複合形體進階｜三段相加）把形體分成三個長方體來算：\n" +
    "A：" + dims(d.a) + "\nB：" + dims(d.b) + "\nC：" + dims(d.c) + "\n" +
    "總體積是多少立方公分？",
    ans,
    [
      "觀念：複合形體先分解成幾個長方體，各自算體積後相加。",
      "列式：A + B + C = " + d.a.join("×") + " + " + d.b.join("×") + " + " + d.c.join("×") + "。",
      "📐 動手算：\n① A = " + d.a.join("×") + " = " + va +
        "\n② B = " + d.b.join("×") + " = " + vb +
        "\n③ C = " + d.c.join("×") + " = " + vc +
        "\n④ 總體積 = A + B + C\n記得寫 cm³ ✅",
      "📌 常見錯誤：三段只算兩段就停，漏掉最小的那段。一定要逐塊核對！"
    ],
    "A=" + va + "，B=" + vb + "，C=" + vc + "，總體積 =" + ans + "（cm³）。",
    ["只算了兩塊就停。", "把相加誤寫成相乘。"]
  ));
});

// ---- cube_cm3 +5 (id 25-29) ----
var cubeEdges = [11, 13, 14, 17, 19];
cubeEdges.forEach(function(e, i) {
  var n = 25 + i;
  var ans = e * e * e;
  newQs.push(makeQ(
    "vg5_cube_" + pad(n), "cube_cm3", "easy",
    "（正方體體積）邊長 " + e + " 公分的正方體，體積是多少立方公分？",
    ans,
    cubeHints(e),
    "正方體體積：" + e + "³ = " + ans + "（cm³）。",
    ["把邊長乘 3 當成體積（那是周長的一部分）。", "忘了連乘三次，只乘兩次（那是面積）。"]
  ));
});

// ---- cube_find_edge +6 (id 9-14) ----
var cubeVolumes = [
  { n:9, e:4, v:64 },
  { n:10, e:6, v:216 },
  { n:11, e:9, v:729 },
  { n:12, e:11, v:1331 },
  { n:13, e:12, v:1728 },
  { n:14, e:15, v:3375 }
];
cubeVolumes.forEach(function(d) {
  newQs.push(makeQ(
    "vg5_cube_find_" + pad(d.n), "cube_find_edge", "medium",
    "（反求邊長）一個正方體的體積是 " + d.v + " 立方公分（cm³），它的邊長是多少公分？（請填整數）",
    d.e,
    [
      "觀念：正方體體積 V = 邊長³。反求邊長，就是找一個整數 n，使得 n³ = V。",
      "做法：試試看哪個整數連乘三次等於 " + d.v + "？",
      "📐 動手算：\n① 猜邊長 n\n② 驗算 n × n × n 是否 = " + d.v +
        "\n③ 找到的 n 就是邊長\n記得寫公分 ✅",
      "📌 常見錯誤：把體積直接除以 3 當邊長。正確做法是開立方根（或逐一試乘）。"
    ],
    "邊長 = " + d.e + "，因為 " + d.e + "³ = " + d.v + "（cm³）。",
    ["直接把體積除以 3。", "把開平方和開立方搞混。"]
  ));
});

// ---- decimal_dims +6 (id 13-18) ----
var decData = [
  { n:13, l:2.5, w:1.2, h:0.4 },
  { n:14, l:1.8, w:1.5, h:0.6 },
  { n:15, l:3.0, w:0.8, h:0.5 },
  { n:16, l:2.4, w:1.6, h:0.5 },
  { n:17, l:1.5, w:1.5, h:1.2 },
  { n:18, l:4.0, w:0.5, h:0.3 }
];
decData.forEach(function(d) {
  // Use integer arithmetic to avoid floating point issues
  var ansNum = Math.round(d.l * d.w * d.h * 10000) / 10000;
  // Clean up trailing zeros but keep decimal if needed
  var ansStr = String(ansNum);
  newQs.push(makeQ(
    "vg5_dec_" + pad(d.n), "decimal_dims", "medium",
    "（帶小數尺寸）一個長方體的長 " + d.l + " 公尺、寬 " + d.w + " 公尺、高 " +
      d.h + " 公尺。體積是多少立方公尺（m³）？（可填小數）",
    ansStr,
    [
      "觀念：單位都已經是公尺，直接用 V=長×寬×高 計算，答案單位是 m³。",
      "列式：" + d.l + " × " + d.w + " × " + d.h + "。",
      "📐 動手算：\n① 先算 " + d.l + " × " + d.w +
        "\n② 再乘以 " + d.h +
        "\n③ 注意小數點位置\n記得寫 m³ ✅",
      "📌 常見錯誤：小數乘法時小數點位數算錯。先用整數算，再看總共幾位小數。"
    ],
    d.l + "×" + d.w + "×" + d.h + " = " + ansStr + "（m³）。",
    ["小數點位數算錯。", "單位寫成 cm³，但題目用的是公尺。"],
    "立方公尺（m³）"
  ));
});

// ---- m3_to_cm3 +8 (id 12-19) ----
var m3Vals = [2, 3, 4, 7, 8, 10, 12, 15];
m3Vals.forEach(function(v, i) {
  var n = 12 + i;
  var ans = v * 1000000;
  newQs.push(makeQ(
    "vg5_m3_to_cm3_" + pad(n), "m3_to_cm3", "medium",
    "（單位換算）" + v + " 立方公尺（m³）等於多少立方公分（cm³）？",
    ans,
    [
      "觀念：1 m = 100 cm，所以 1 m³ = 100³ cm³。",
      "做法：100³ = 1,000,000，所以乘以 1,000,000。",
      "📐 動手算：\n① 1 m³ = 1,000,000 cm³\n② " + v +
        " m³ = " + v + " × 1,000,000\n記得寫 cm³ ✅",
      "📌 常見錯誤：乘以 100 或 1000 而不是 1,000,000。立方要連乘三次 100！"
    ],
    v + " × 1,000,000 = " + ans + "（cm³）。",
    CM_UNIT()
  ));
});

// ---- cm3_to_m3 +8 (id 12-19) ----
var cm3Vals = [2000000, 3000000, 4000000, 5000000, 7000000, 8000000, 11000000, 14000000];
cm3Vals.forEach(function(v, i) {
  var n = 12 + i;
  var ans = v / 1000000;
  newQs.push(makeQ(
    "vg5_cm3_to_m3_" + pad(n), "cm3_to_m3", "medium",
    "（單位換算）" + v.toLocaleString() + " 立方公分（cm³）等於多少立方公尺（m³）？（請填整數）",
    ans,
    [
      "觀念：1 m³ = 1,000,000 cm³。",
      "做法：÷ 1,000,000 即可。",
      "📐 動手算：\n① 1 m³ = 1,000,000 cm³\n② " + v.toLocaleString() +
        " ÷ 1,000,000\n記得寫 m³ ✅",
      "📌 常見錯誤：÷ 100 或 ÷ 1000 而不是 ÷ 1,000,000。立方單位，要 ÷ 100 三次！"
    ],
    v.toLocaleString() + " ÷ 1,000,000 = " + ans + "（m³）。",
    CM_UNIT(),
    "立方公尺（m³）"
  ));
});

// ---- mixed_units +6 (id 13-18) ----
var mixedData = [
  { n:13, lm:1, wcm:50, hcm:20 },
  { n:14, lm:2, wcm:30, hcm:25 },
  { n:15, lm:1, wcm:80, hcm:10 },
  { n:16, lm:3, wcm:20, hcm:15 },
  { n:17, lm:1, wcm:40, hcm:50 },
  { n:18, lm:2, wcm:60, hcm:40 }
];
mixedData.forEach(function(d) {
  var lcm = d.lm * 100;
  var ans = lcm * d.wcm * d.hcm;
  newQs.push(makeQ(
    "vg5_mixed_" + pad(d.n), "mixed_units", "medium",
    "（單位混合）一個長方體的長是 " + d.lm + " 公尺、寬是 " + d.wcm +
      " 公分、高是 " + d.hcm + " 公分。體積是多少立方公分（cm³）？",
    ans,
    [
      "觀念：先把長、寬、高的單位統一（都換成 cm），再用 V=長×寬×高。",
      "列式：" + d.lm + " 公尺 = " + lcm + " 公分，所以 " + lcm + "×" + d.wcm + "×" + d.hcm + "。",
      "📐 動手算：\n① " + d.lm + " m = " + lcm + " cm\n② " + lcm + "×" + d.wcm + "×" + d.hcm +
        "\n記得寫 cm³ ✅",
      "📌 常見錯誤：沒統一單位就直接 " + d.lm + "×" + d.wcm + "×" + d.hcm + "，漏乘了 100！"
    ],
    d.lm + " m = " + lcm + " cm，" + lcm + "×" + d.wcm + "×" + d.hcm + " = " + ans + "（cm³）。",
    CM_UNIT()
  ));
});

// ---- rect_find_height +4 (id 13-16) ----
var rfhData = [
  { n:13, l:12, w:8, h:7 },
  { n:14, l:15, w:6, h:9 },
  { n:15, l:20, w:4, h:11 },
  { n:16, l:18, w:5, h:8 }
];
rfhData.forEach(function(d) {
  var v = d.l * d.w * d.h;
  var base = d.l * d.w;
  newQs.push(makeQ(
    "vg5_rect_find_h_" + pad(d.n), "rect_find_height", "medium",
    "（反求高）一個長方體的長是 " + d.l + " 公分、寬是 " + d.w +
      " 公分，體積是 " + v + " 立方公分（cm³）。它的高是多少公分？（請填整數）",
    d.h,
    [
      "觀念：長方體體積 V = 長×寬×高；要反求高，可以用 高 = 體積 ÷ (長×寬)。",
      "列式：高 = " + v + " ÷ (" + d.l + "×" + d.w + ")。",
      "📐 動手算：\n① 底面積 = " + d.l + "×" + d.w + " = " + base +
        "\n② 高 = " + v + " ÷ " + base +
        "\n記得寫公分 ✅",
      "📌 常見錯誤：直接用體積÷長或÷寬（只除了一個維度）。要先算底面積再除！"
    ],
    "底面積 = " + base + "，高 = " + v + " ÷ " + base + " = " + d.h + "（公分）。",
    ["直接體積÷長，忘了還要÷寬。", "把除法算反了（用底面積÷體積）。"]
  ));
});

// ============ append & write ============
var src = fs.readFileSync(SRC, "utf8");
// Find the closing ]; of the array
var closeIdx = src.lastIndexOf("];");
if (closeIdx === -1) { console.error("Cannot find ]; in bank.js"); process.exit(1); }

var before = src.substring(0, closeIdx);
// Ensure trailing comma on last existing entry
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
console.log("New total:", 147 + newQs.length);
console.log("Synced to dist.");
