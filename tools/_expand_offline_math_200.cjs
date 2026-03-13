#!/usr/bin/env node
// Expand offline-math from 170 → 200 questions (+30)
// Run: node tools/_expand_offline_math_200.cjs
"use strict";
var fs = require("fs");
var path = require("path");

var SRC = path.join(__dirname, "..", "docs", "offline-math", "bank.js");
var DIST = path.join(__dirname, "..", "dist_ai_math_web_pages", "docs", "offline-math", "bank.js");

function makeQ(id, topicName, type, prompt, answer, steps, cmText) {
  var computeSteps = steps.map(function(s){ return { k:"compute", say:s }; });
  var allSteps = [{ k:"concept", say: steps[0] }].concat(computeSteps.slice(1));
  return {
    id: id,
    grade: 5,
    topic: topicName,
    type: type,
    params: {},
    prompt: prompt,
    answer: String(answer),
    teacherSteps: allSteps,
    source: "generated",
    meta: {},
    question: prompt,
    kind: "general",
    difficulty: "medium",
    hints: [
      steps[0],
      steps.length > 1 ? steps[1] : "想想看怎麼列式。",
      "📐 一步步算：\n" + steps.slice(1).map(function(s,i){ return "① " + s; }).join("\n") + "\n算完記得回頭檢查喔！✅",
      "👉 " + cmText
    ],
    steps: steps.slice(1),
    explanation: prompt.replace(" = ?","").replace("？","") + " = " + answer + "。",
    common_mistakes: [cmText, "計算粗心。"]
  };
}

var newQs = [];

// ---- time +6 (31-36) ----
var timeData = [
  { n:31, p:"2小時15分 + 3小時50分 = ?小時?分", a:"6小時5分", s:["時間加法要分開小時和分鐘算","2+3=5小時","15+50=65分=1小時5分","合計5+1=6小時5分"], cm:"60分=1小時，進位搞錯。" },
  { n:32, p:"5小時20分 − 2小時45分 = ?小時?分", a:"2小時35分", s:["時間減法不夠減要借位","20分不夠減45分","借1小時=60分，80−45=35分","5−1−2=2小時"], cm:"借位忘了從小時減1。" },
  { n:33, p:"上午9:40出發，走了2小時30分，到達時間是幾點？", a:"12:10", s:["出發時間+經過時間=到達時間","9:40+2小時=11:40","11:40+30分=12:10"], cm:"跨12點時忘了換成下午。" },
  { n:34, p:"下午1:50到3:25一共經過多少分鐘？", a:"95", s:["結束時間−開始時間=經過時間","3小時25分−1小時50分","2小時85分−1小時50分=1小時35分","1×60+35=95分鐘"], cm:"小時和分鐘的換算搞錯。" },
  { n:35, p:"每節課40分鐘，下課10分鐘，連上3節後是幾分鐘？", a:"140", s:["3節課+2次下課","3×40=120分鐘","2×10=20分鐘（最後一節後不下課）","120+20=140分鐘"], cm:"下課次數多算一次。" },
  { n:36, p:"一部電影2小時15分，從下午2:30開始播，幾點結束？", a:"4:45", s:["開始時間+播放時間","2:30+2小時=4:30","4:30+15分=4:45"], cm:"跨整點加法出錯。" }
];
timeData.forEach(function(d) {
  newQs.push(makeQ("offline_time-"+String(d.n).padStart(3,"0"), "time", "time_calc", d.p, d.a, d.s, d.cm));
});

// ---- div +6 (36-41) ----
var divData = [
  { n:36, p:"756 ÷ 12 = ?", a:"63", s:["先估商：756÷12","75÷12≈6，放十位","756−720=36","36÷12=3，放個位","商=63"], cm:"估商時位值放錯。" },
  { n:37, p:"918 ÷ 27 = ?", a:"34", s:["先估商：918÷27","91÷27≈3，放十位","918−810=108","108÷27=4，放個位","商=34"], cm:"兩位數除法估商不夠精準。" },
  { n:38, p:"624 ÷ 16 = ?", a:"39", s:["先估商：624÷16","62÷16≈3，放十位","624−480=144","144÷16=9，放個位","商=39"], cm:"減法算錯導致餘數錯誤。" },
  { n:39, p:"1050 ÷ 25 = ?", a:"42", s:["先估商：1050÷25","105÷25≈4，放十位","1050−1000=50","50÷25=2，放個位","商=42"], cm:"四位數除法容易看錯位數。" },
  { n:40, p:"864 ÷ 18 = ?", a:"48", s:["先估商：864÷18","86÷18≈4，放十位","864−720=144","144÷18=8，放個位","商=48"], cm:"乘法驗算沒做，商少了一位。" },
  { n:41, p:"575 ÷ 23 = ?", a:"25", s:["先估商：575÷23","57÷23≈2，放十位","575−460=115","115÷23=5，放個位","商=25"], cm:"除數是兩位數時估商容易偏大。" }
];
divData.forEach(function(d) {
  newQs.push(makeQ("offline_div-"+String(d.n).padStart(3,"0"), "division", "long_div", d.p, d.a, d.s, d.cm));
});

// ---- dist +6 (36-41) ----
var distData = [
  { n:36, p:"時速80公里，開了3小時，行了多少公里？", a:"240", s:["速度×時間=距離","80×3=240公里","距離=240"], cm:"速度和時間的乘法算錯。" },
  { n:37, p:"跑了450公尺用了90秒，每秒跑幾公尺？", a:"5", s:["速度=距離÷時間","450÷90=5","每秒5公尺"], cm:"除法方向搞反。" },
  { n:38, p:"腳踏車時速15公里，騎了60公里，花了幾小時？", a:"4", s:["時間=距離÷速度","60÷15=4","花了4小時"], cm:"用速度÷距離搞反了。" },
  { n:39, p:"甲車時速60公里，乙車時速40公里，同向出發2小時後相距多少公里？", a:"40", s:["速度差×時間=距離差","60−40=20公里/時","20×2=40公里"], cm:"忘了用速度差而是用速度和。" },
  { n:40, p:"火車時速120公里，客車時速80公里，相向出發3小時後相距多少公里（原本相距600公里）？", a:"0", s:["速度和×時間=靠近距離","120+80=200公里/時","200×3=600公里","600−600=0，剛好相遇"], cm:"相向應該用速度和，不是速度差。" },
  { n:41, p:"從家到學校1200公尺，走路每分鐘80公尺，幾分鐘到？", a:"15", s:["時間=距離÷速度","1200÷80=15","走15分鐘"], cm:"距離和速度的單位不統一。" }
];
distData.forEach(function(d) {
  newQs.push(makeQ("offline_dist-"+String(d.n).padStart(3,"0"), "distance", "dist_calc", d.p, d.a, d.s, d.cm));
});

// ---- frac +6 (36-41) ----
var fracData = [
  { n:36, p:"2/5 + 1/3 = ?", a:"11/15", s:["異分母加法先通分","lcm(5,3)=15","2/5=6/15，1/3=5/15","6+5=11，分母15"], cm:"通分時分子忘了同倍數。" },
  { n:37, p:"7/8 − 1/2 = ?", a:"3/8", s:["異分母減法先通分","lcm(8,2)=8","7/8=7/8，1/2=4/8","7−4=3，分母8"], cm:"分母不同不能直接減。" },
  { n:38, p:"3/4 × 2/5 = ?", a:"3/10", s:["分數乘法：分子×分子、分母×分母","3×2=6，4×5=20","6/20約分=3/10"], cm:"忘了約分到最簡。" },
  { n:39, p:"5/6 ÷ 2 = ?", a:"5/12", s:["分數÷整數=分母×整數","5/6 ÷ 2 = 5/(6×2)","= 5/12"], cm:"把分子也乘了2。" },
  { n:40, p:"1 − 3/7 = ?", a:"4/7", s:["1化成7/7","7/7 − 3/7 = 4/7"], cm:"1忘了化成同分母分數。" },
  { n:41, p:"2/3 + 1/6 + 1/2 = ?", a:"4/3", s:["找三個分母的lcm=6","2/3=4/6，1/6=1/6，1/2=3/6","4+1+3=8，分母6","8/6約分=4/3"], cm:"三個分數通分錯誤。" }
];
fracData.forEach(function(d) {
  newQs.push(makeQ("offline_frac-"+String(d.n).padStart(3,"0"), "fraction", "frac_calc", d.p, d.a, d.s, d.cm));
});

// ---- dec +6 (36-41) ----
var decData = [
  { n:36, p:"3.6 + 2.45 = ?", a:"6.05", s:["小數加法要小數點對齊","3.60+2.45","= 6.05"], cm:"小數點沒對齊。" },
  { n:37, p:"7.2 − 3.85 = ?", a:"3.35", s:["小數減法要小數點對齊","7.20−3.85","十分位借位後計算"], cm:"借位搞錯。" },
  { n:38, p:"0.4 × 0.3 = ?", a:"0.12", s:["先當整數乘：4×3=12","兩個因數各一位小數，共兩位","放回小數點→0.12"], cm:"小數位數數錯。" },
  { n:39, p:"6.3 ÷ 7 = ?", a:"0.9", s:["小數÷整數直接除","63÷7=9","小數點對齊→0.9"], cm:"小數點忘了對齊。" },
  { n:40, p:"2.5 × 4 = ?", a:"10", s:["先當整數：25×4=100","一位小數→10.0=10"], cm:"忘了移回小數點。" },
  { n:41, p:"0.75 + 0.25 = ?", a:"1", s:["小數加法：小數點對齊","0.75+0.25=1.00","=1"], cm:"進位沒處理好。" }
];
decData.forEach(function(d) {
  newQs.push(makeQ("offline_dec-"+String(d.n).padStart(3,"0"), "decimal", "dec_calc", d.p, d.a, d.s, d.cm));
});

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
console.log("New total:", 170 + newQs.length);
console.log("Synced to dist.");
