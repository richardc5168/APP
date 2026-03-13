#!/usr/bin/env node
'use strict';
var fs = require('fs');
var path = require('path');

var DOCS = path.join(__dirname, '..', 'docs', 'interactive-g5-empire', 'bank.js');
var DIST = path.join(__dirname, '..', 'dist_ai_math_web_pages', 'docs', 'interactive-g5-empire', 'bank.js');

// ---- Helpers ----
function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { var t = b; b = a % t; a = t; } return a; }
function lcmFn(a, b) { return a * b / gcd(a, b); }
function fracStr(n, d) { var g = gcd(n, d); n /= g; d /= g; return d === 1 ? String(n) : n + '/' + d; }
function dp(s) { return (String(s).split('.')[1] || '').length; }
function ips(intVal, places) {
  if (places === 0) return String(intVal);
  var s = String(Math.abs(intVal)).padStart(places + 1, '0');
  var ip = s.slice(0, s.length - places);
  var dp2 = s.slice(s.length - places).replace(/0+$/, '');
  var sign = intVal < 0 ? '-' : '';
  return dp2 ? sign + ip + '.' + dp2 : sign + ip;
}
function pad3(n) { return String(n).padStart(3, '0'); }
function pad2(n) { return String(n).padStart(2, '0'); }
function addMins(startStr, mins) {
  var p = startStr.split(':');
  var h = parseInt(p[0]), m = parseInt(p[1]);
  m += mins;
  while (m >= 60) { h++; m -= 60; }
  while (h >= 24) h -= 24;
  return pad2(h) + ':' + pad2(m);
}

// ---- Read ----
var src = fs.readFileSync(DOCS, 'utf8');
var w = {};
new Function('window', src)(w);
var bank = w.INTERACTIVE_G5_EMPIRE_BANK;
console.log('Before:', bank.length);
if (bank.length !== 320) { console.error('Expected 320'); process.exit(1); }

var topics = {};
bank.forEach(function(q) { if (!topics[q.kind]) topics[q.kind] = q.topic; });

// ===== 1. volume_rect_prism +10 (IDs 41-50) =====
[
  [8,12,5],[14,7,3],[11,9,6],[6,16,4],[18,5,8],
  [9,11,7],[15,8,3],[7,13,9],[4,17,6],[12,6,11]
].forEach(function(d, i) {
  var l = d[0], ww = d[1], h = d[2];
  var ans = l * ww * h;
  bank.push({
    id: 'g5e_volume_' + pad3(41 + i), kind: 'volume_rect_prism', topic: topics.volume_rect_prism, difficulty: 'easy',
    question: '（帝國｜體積）長方體長 ' + l + ' cm、寬 ' + ww + ' cm、高 ' + h + ' cm，體積是多少 cm³？',
    answer: String(ans), answer_mode: 'number',
    hints: [
      '⭐ 觀念提醒\n長方體體積 = 長 × 寬 × 高。',
      '📊 列式：' + l + ' × ' + ww + ' × ' + h,
      '📐 一步步算：\n① 列式：' + l + ' × ' + ww + ' × ' + h + '\n② 先算 ' + l + ' × ' + ww + ' = ' + (l * ww) + '\n③ 再乘以 ' + h + '\n④ 自己算出答案\n算完記得回頭檢查喔！✅',
      '👉 體積 = 長 × 寬 × 高，注意單位是 cm³。'
    ],
    steps: ['列式：' + l + ' × ' + ww + ' × ' + h, l + ' × ' + ww + ' = ' + (l * ww), (l * ww) + ' × ' + h + ' = ' + ans, '體積 = ' + ans + ' cm³'],
    meta: { l: l, w: ww, h: h, unit: 'cm³' },
    explanation: l + ' × ' + ww + ' × ' + h + ' = ' + ans + ' cm³。',
    common_mistakes: ['長寬高數字看錯。', '乘法計算粗心。']
  });
});

// ===== 2. fraction_mul +10 (IDs 41-50) =====
// [aN, aD, bN, bD]
[
  [3,7,5,6],[4,5,3,8],[7,9,3,14],[5,6,2,15],[8,11,3,4],
  [2,3,9,10],[5,12,4,7],[7,8,2,5],[6,7,1,3],[9,10,5,6]
].forEach(function(d, i) {
  var aN = d[0], aD = d[1], bN = d[2], bD = d[3];
  var resN = aN * bN, resD = aD * bD;
  var ans = fracStr(resN, resD);
  var aStr = aN + '/' + aD, bStr = bN + '/' + bD;
  bank.push({
    id: 'g5e_fraction_mul_' + pad3(41 + i), kind: 'fraction_mul', topic: topics.fraction_mul, difficulty: 'easy',
    question: '（帝國｜分數乘法）' + aStr + ' × ' + bStr + ' = ？（答案寫最簡分數）',
    answer: ans, answer_mode: 'fraction',
    hints: [
      '⭐ 觀念提醒\n分數乘法：分子×分子、分母×分母，最後約分。',
      '📊 ' + aStr + ' × ' + bStr + ' = (' + aN + '×' + bN + ')/(' + aD + '×' + bD + ')',
      '📐 一步步算：\n① 分子相乘：' + aN + ' × ' + bN + ' = ' + resN + '\n② 分母相乘：' + aD + ' × ' + bD + ' = ' + resD + '\n③ 約分成最簡分數\n④ 檢查\n算完記得回頭檢查喔！✅',
      '👉 分數×分數：上×上、下×下，約分到最簡。'
    ],
    steps: ['分子：' + aN + ' × ' + bN + ' = ' + resN, '分母：' + aD + ' × ' + bD + ' = ' + resD, '約分', '= ' + ans],
    meta: { a: aStr, b: bStr },
    explanation: aStr + ' × ' + bStr + ' = ' + ans + '。',
    common_mistakes: ['分子分母算錯。', '忘了約分。']
  });
});

// ===== 3. decimal_mul +10 (IDs 41-50) =====
var dmItems = ['白米','麵粉','油','果汁','砂糖','花生','紅茶','蜂蜜','牛奶','咖啡'];
var dmUnits = ['公斤','公斤','公升','公升','公斤','公斤','公升','公斤','公升','公斤'];
[
  ['0.35',6],['1.45',4],['0.82',7],['2.36',3],['0.15',9],
  ['3.14',5],['0.68',8],['1.92',6],['0.47',3],['2.55',4]
].forEach(function(d, i) {
  var a = d[0], b = d[1];
  var ap = dp(a);
  var ai = Math.round(Number(a) * Math.pow(10, ap));
  var raw = ai * b;
  var ans = ips(raw, ap);
  bank.push({
    id: 'g5e_decimal_mul_' + pad3(41 + i), kind: 'decimal_mul', topic: topics.decimal_mul, difficulty: 'medium',
    question: '（帝國｜小數乘法）每份' + dmItems[i] + '有 ' + a + ' ' + dmUnits[i] + '，有 ' + b + ' 份，一共多少 ' + dmUnits[i] + '？（可寫小數）',
    answer: ans, answer_mode: 'number',
    hints: [
      '⭐ 觀念提醒\n小數 × 整數，先去掉小數點做整數乘法，再放回小數點。',
      '📊 去掉小數點：' + ai + ' × ' + b + ' = ' + raw,
      '📐 一步步算：\n① 列式：' + a + ' × ' + b + '\n② 去掉小數點做整數乘法\n③ 放回小數點（' + a + ' 有 ' + ap + ' 位小數）\n④ 估算檢查\n算完記得回頭檢查喔！✅',
      '👉 小數乘整數：先去小數點算整數乘法，再按原小數位數放回。'
    ],
    steps: ['列式：' + a + ' × ' + b, '去掉小數點：' + ai + ' × ' + b + ' = ' + raw, '放回小數點 → ' + ans, '估算檢查 ✓'],
    meta: { a: a, b: String(b), a_int: ai, b_int: b, a_places: ap, raw_int_product: raw, total_places: ap, unit: dmUnits[i] },
    explanation: a + ' × ' + b + ' = ' + ans + ' ' + dmUnits[i] + '。',
    common_mistakes: ['忘了放回小數點。', '小數位數數錯。']
  });
});

// ===== 4. decimal_div +10 (IDs 41-50) =====
var ddItems = ['米','果汁','油','麵粉','水','牛奶','砂糖','紅茶','蜂蜜','咖啡豆'];
var ddUnits = ['公斤','公升','公升','公斤','公升','公升','公斤','公升','公斤','公斤'];
// [dividend_str, divisor] — must divide exactly
[
  ['3.6',4],['15.5',5],['4.86',6],['9.24',3],['12.8',8],
  ['24.5',7],['5.76',9],['8.46',9],['7.28',4],['16.5',3]
].forEach(function(d, i) {
  var a = d[0], b = d[1];
  var ap = dp(a);
  var ai = Math.round(Number(a) * Math.pow(10, ap));
  if (ai % b !== 0) { console.error('NOT EXACT:', a, '/', b); process.exit(1); }
  var ansI = ai / b;
  var ans = ips(ansI, ap);
  bank.push({
    id: 'g5e_decimal_div_' + pad3(41 + i), kind: 'decimal_div', topic: topics.decimal_div, difficulty: 'easy',
    question: '（帝國｜小數除法）有 ' + a + ' ' + ddUnits[i] + '的' + ddItems[i] + '，平均分成 ' + b + ' 份，每份多少' + ddUnits[i] + '？（可寫小數）',
    answer: ans, answer_mode: 'number',
    hints: [
      '⭐ 觀念提醒\n小數 ÷ 整數，用直式除法，小數點對齊。',
      '📊 列式：' + a + ' ÷ ' + b,
      '📐 一步步算：\n① 列式：' + a + ' ÷ ' + b + '\n② 做到小數點就往上點到商\n③ 不夠除就補 0\n④ 檢查小數點對齊\n算完記得回頭檢查喔！✅',
      '👉 小數除以整數：商的小數點和被除數對齊。不夠除補 0。'
    ],
    steps: ['列式：' + a + ' ÷ ' + b, '做直式除法', '商 = ' + ans, '驗算 ✓'],
    meta: { a: a, b: String(b), a_int: ai, a_places: ap, ans_int: ansI, ans_places: ap, unit: ddUnits[i] },
    explanation: a + ' ÷ ' + b + ' = ' + ans + ' ' + ddUnits[i] + '。',
    common_mistakes: ['商的小數點沒對齊。', '不夠除時忘了補 0。']
  });
});

// ===== 5. time_add +10 (IDs 41-50) =====
[
  ['08:45',35],['14:30',95],['10:15',48],['17:50',75],['06:25',110],
  ['21:40',45],['13:55',68],['09:10',125],['16:35',87],['07:50',53]
].forEach(function(d, i) {
  var start = d[0], addM = d[1];
  var end = addMins(start, addM);
  bank.push({
    id: 'g5e_time_add_' + pad3(41 + i), kind: 'time_add', topic: topics.time_add, difficulty: 'medium',
    question: '（帝國｜時間加法）從 ' + start + ' 開始，過了 ' + addM + ' 分鐘，時間是幾點幾分？（用 HH:MM）',
    answer: end, answer_mode: 'hhmm',
    hints: [
      '⭐ 觀念提醒\n時間加法：分鐘超過 60 就要進位到小時。',
      '📊 ' + start + ' + ' + addM + ' 分 = ?',
      '📐 一步步算：\n① 先加分鐘\n② 分鐘 ≥ 60 就進位（-60 分，+1 小時）\n③ 寫出最終時間\n④ 檢查合理\n算完記得回頭檢查喔！✅',
      '👉 時間加法：分鐘滿 60 進位。注意跨時段要再進位一次。'
    ],
    steps: [start + ' + ' + addM + ' 分', '分鐘部分相加', '進位', '= ' + end],
    meta: { start: start, add_m: addM, end: end },
    explanation: start + ' + ' + addM + ' 分 = ' + end + '。',
    common_mistakes: ['分鐘進位時忘了加小時。', '超過 120 分時只進了 1 小時。']
  });
});

// ===== 6. unit_convert +10 (IDs 41-50) =====
[
  [2,350],[3,75],[5,500],[4,125],[1,800],
  [6,42],[7,210],[3,650],[8,15],[2,999]
].forEach(function(d, i) {
  var l = d[0], ml = d[1];
  var ans = l * 1000 + ml;
  bank.push({
    id: 'g5e_unit_convert_' + pad3(41 + i), kind: 'unit_convert', topic: topics.unit_convert, difficulty: 'easy',
    question: '（帝國｜單位換算）' + l + ' 公升 ' + ml + ' 毫升 = 多少毫升？',
    answer: String(ans), answer_mode: 'number',
    hints: [
      '⭐ 觀念提醒\n1 公升 = 1000 毫升。先把公升化為毫升再相加。',
      '📊 ' + l + ' 公升 = ' + (l * 1000) + ' 毫升',
      '📐 一步步算：\n① ' + l + ' 公升 = ' + (l * 1000) + ' 毫升\n② 再加上 ' + ml + ' 毫升\n③ 自己算出合計\n④ 檢查\n算完記得回頭檢查喔！✅',
      '👉 先換算公升為毫升（×1000），再加上多的毫升數。'
    ],
    steps: [l + ' 公升 = ' + (l * 1000) + ' 毫升', '加上 ' + ml + ' 毫升', '= ' + ans + ' 毫升', '檢查 ✓'],
    meta: { l: l, ml: ml, convert_kind: 'l_ml' },
    explanation: l + ' 公升 ' + ml + ' 毫升 = ' + ans + ' 毫升。',
    common_mistakes: ['1 公升 = 1000 毫升記錯。', '加法算錯。']
  });
});

// ===== 7. fraction_addsub +10 (IDs 41-50) =====
// [op, aN, aD, bN, bD]
[
  ['+',2,5,1,3],['-',7,8,1,6],['+',3,4,2,9],['-',5,6,3,10],['+',1,7,2,3],
  ['-',4,5,1,4],['+',3,8,5,12],['-',11,12,1,3],['+',2,9,1,6],['-',5,8,1,12]
].forEach(function(d, i) {
  var op = d[0], aN = d[1], aD = d[2], bN = d[3], bD = d[4];
  var lcd = lcmFn(aD, bD);
  var lN = aN * (lcd / aD), rN = bN * (lcd / bD);
  var resN = op === '+' ? lN + rN : lN - rN;
  var ans = fracStr(resN, lcd);
  var aStr = aN + '/' + aD, bStr = bN + '/' + bD;
  bank.push({
    id: 'g5e_fraction_addsub_' + pad3(41 + i), kind: 'fraction_addsub', topic: topics.fraction_addsub, difficulty: 'medium',
    question: '（帝國｜分數加減）' + aStr + ' ' + op + ' ' + bStr + ' = ？（答案寫最簡分數）',
    answer: ans, answer_mode: 'fraction',
    hints: [
      '⭐ 觀念提醒\n分數加減法要先通分（找最小公倍數），再加減分子。',
      '📊 通分：' + aD + ' 和 ' + bD + ' 的最小公倍數是 ' + lcd + '。',
      '📐 一步步算：\n① 通分到同分母 ' + lcd + '\n② ' + aStr + ' → ' + lN + '/' + lcd + '\n③ ' + bStr + ' → ' + rN + '/' + lcd + '\n④ 分子相' + (op === '+' ? '加' : '減') + '再約分\n算完記得回頭檢查喔！✅',
      '👉 分數加減：先通分再計算分子。最後約分成最簡分數。'
    ],
    steps: ['通分到 ' + lcd, aStr + ' → ' + lN + '/' + lcd, bStr + ' → ' + rN + '/' + lcd, '= ' + ans],
    meta: { a: aStr, b: bStr, lcm: lcd, op: op },
    explanation: aStr + ' ' + op + ' ' + bStr + ' = ' + ans + '。',
    common_mistakes: ['忘了通分直接加減。', '約分沒約到最簡。']
  });
});

// ===== 8. percent_of +10 (IDs 41-50) =====
[
  [200,15],[360,25],[150,40],[800,5],[160,75],
  [350,20],[250,30],[170,50],[115,60],[110,80]
].forEach(function(d, i) {
  var base = d[0], p = d[1];
  var ans = base * p / 100;
  if (!Number.isInteger(ans)) { console.error('NOT INTEGER:', base, p); process.exit(1); }
  bank.push({
    id: 'g5e_percent_of_' + pad3(41 + i), kind: 'percent_of', topic: topics.percent_of, difficulty: 'easy',
    question: '（帝國｜百分率）' + p + '% 的 ' + base + ' 是多少？（可寫整數或小數）',
    answer: String(ans), answer_mode: 'number',
    hints: [
      '⭐ 觀念提醒\n百分率計算：X% 的 Y = Y × X ÷ 100。',
      '📊 ' + base + ' × ' + p + ' ÷ 100 = ?',
      '📐 一步步算：\n① 列式：' + base + ' × ' + p + ' ÷ 100\n② 先算 ' + base + ' × ' + p + '\n③ 再除以 100\n④ 檢查答案合理\n算完記得回頭檢查喔！✅',
      '👉 X% = X/100。先乘再除以 100。'
    ],
    steps: [base + ' × ' + p + ' = ' + (base * p), (base * p) + ' ÷ 100 = ' + ans, '答案 = ' + ans, '檢查 ✓'],
    meta: { base: base, p: p },
    explanation: p + '% 的 ' + base + ' = ' + ans + '。',
    common_mistakes: ['忘了除以 100。', '乘法算錯。']
  });
});

// ---- Verify ----
console.log('After:', bank.length);
if (bank.length !== 400) { console.error('EXPECTED 400, got', bank.length); process.exit(1); }
var ids = {};
for (var qi = 0; qi < bank.length; qi++) {
  if (ids[bank[qi].id]) { console.error('DUPLICATE ID:', bank[qi].id); process.exit(1); }
  ids[bank[qi].id] = true;
}
for (var ni = 320; ni < 400; ni++) {
  var q = bank[ni];
  if (!q.answer || q.answer === 'undefined') { console.error('BAD ANSWER:', q.id); process.exit(1); }
  if (q.hints[2].indexOf(q.answer) !== -1 && q.answer.length > 1) {
    console.error('L3 HINT LEAK:', q.id, 'answer=' + q.answer); process.exit(1);
  }
}
console.log('All 80 new questions verified.');

// ---- Write ----
var out = '/* eslint-disable */\nwindow.INTERACTIVE_G5_EMPIRE_BANK = ' + JSON.stringify(bank, null, 2) + ';\n';
fs.writeFileSync(DOCS, out, 'utf8');
fs.writeFileSync(DIST, out, 'utf8');
console.log('Done. 320 → 400. Written to docs/ and dist/.');
