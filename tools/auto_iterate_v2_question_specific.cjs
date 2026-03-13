#!/usr/bin/env node
/**
 * auto_iterate_v2_question_specific.cjs
 * ──────────────────────────────────────
 * Phase 2 quality optimizer: question-specific L3 hints + CM.
 *
 * Unlike v1 (kind-level templates), this tool generates L3 hints and
 * common_mistakes that embed the ACTUAL numbers/context from each question.
 *
 * Three phases:
 *   A) L3 → question-specific using `steps`, `meta`, or extracted numbers
 *   B) CM → question-specific using `meta`/question analysis
 *   C) Answer-leak guard (final pass)
 *
 * Usage:
 *   node tools/auto_iterate_v2_question_specific.cjs             # dry-run
 *   node tools/auto_iterate_v2_question_specific.cjs --apply     # apply
 *   node tools/auto_iterate_v2_question_specific.cjs --report    # stats only
 */
'use strict';
const fs   = require('fs');
const path = require('path');
const vm   = require('vm');

const apply      = process.argv.includes('--apply');
const reportOnly = process.argv.includes('--report');
const DOCS  = path.resolve(__dirname, '..', 'docs');
const DIST  = path.resolve(__dirname, '..', 'dist_ai_math_web_pages', 'docs');
const CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩';

/* ════════════════════════════════════════════════════════════════════
   Module registry
   ════════════════════════════════════════════════════════════════════ */
const MODULES = [
  ['exam-sprint',                         'EXAM_SPRINT_BANK',            'bank.js'],
  ['interactive-g5-empire',               'INTERACTIVE_G5_EMPIRE_BANK',  'bank.js'],
  ['life-applications-g5',                'LIFE_APPLICATIONS_G5_BANK',   'bank.js'],
  ['interactive-g5-life-pack2plus-empire', 'G5_LIFE_PACK2PLUS_BANK',     'bank.js'],
  ['interactive-decimal-g5',              'INTERACTIVE_DECIMAL_G5_BANK', 'bank.js'],
  ['interactive-g5-life-pack1plus-empire', 'G5_LIFE_PACK1PLUS_BANK',     'bank.js'],
  ['interactive-g5-life-pack1-empire',    'G5_LIFE_PACK1_BANK',          'bank.js'],
  ['interactive-g5-life-pack2-empire',    'G5_LIFE_PACK2_BANK',          'bank.js'],
  ['ratio-percent-g5',                    'RATIO_PERCENT_G5_BANK',       'bank.js'],
  ['volume-g5',                           'VOLUME_G5_BANK',              'bank.js'],
  ['fraction-g5',                         'FRACTION_G5_BANK',            'bank.js'],
  ['decimal-unit4',                       'DECIMAL_UNIT4_BANK',          'bank.js'],
  ['offline-math',                        'OFFLINE_MATH_BANK',           'bank.js'],
  ['g5-grand-slam',                       'G5_GRAND_SLAM_BANK',          'bank.js'],
  ['fraction-word-g5',                    'FRACTION_WORD_G5_BANK',       'bank.js'],
  ['commercial-pack1-fraction-sprint',    'COMMERCIAL_PACK1_FRACTION_SPRINT_BANK', 'bank.js'],
  ['interactive-g5-midterm1',             'FRACTION_WORD_G5_BANK',       'bank.js'],
  ['interactive-g5-national-bank',        'FRACTION_WORD_G5_BANK',       'bank.js'],
];
const JSON_MODULES = [
  ['interactive-g56-core-foundation',     'g56_core_foundation.json'],
];

/* ════════════════════════════════════════════════════════════════════
   Number extraction helpers
   ════════════════════════════════════════════════════════════════════ */
function extractFractions(text) {
  const fracs = [];
  const re = /(\d+)\s*[\/／]\s*(\d+)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    fracs.push({ n: parseInt(m[1]), d: parseInt(m[2]), str: m[0].replace(/\s/g, '') });
  }
  return fracs;
}

function extractDecimals(text) {
  const decs = [];
  const re = /(\d+\.\d+)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    decs.push(parseFloat(m[1]));
  }
  return decs;
}

function extractIntegers(text) {
  // Extract integers not part of fractions or decimals
  const cleaned = text.replace(/\d+\.\d+/g, '').replace(/\d+\s*[\/／]\s*\d+/g, '');
  const ints = [];
  const re = /\b(\d+)\b/g;
  let m;
  while ((m = re.exec(cleaned)) !== null) {
    ints.push(parseInt(m[1]));
  }
  return ints;
}

function decimalPlaces(n) {
  const s = String(n);
  const dot = s.indexOf('.');
  return dot < 0 ? 0 : s.length - dot - 1;
}

function gcd(a, b) { return b === 0 ? a : gcd(b, a % b); }
function lcm(a, b) { return a * b / gcd(a, b); }

/* ════════════════════════════════════════════════════════════════════
   Answer masking (safety against hint leaks)
   ════════════════════════════════════════════════════════════════════ */

/**
 * Mirror of Python validator's hint_leak() — non-strict mode.
 * Returns true if the text would be flagged by the validator.
 */
function validatorLeakCheck(text, answer) {
  if (!text || !answer) return false;
  var a = String(answer).trim();
  if (!a || a.length > 24) return false;
  var esc = a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Pattern 1: 答案[：:是為]\s*<answer>(\b|\s|。|$)
  if (new RegExp('答案[：:是為]\\s*' + esc + '(\\b|\\s|。|$)').test(text)) return true;
  // Pattern 2: =\s*<answer>(\b|\s|。|$)
  if (new RegExp('=\\s*' + esc + '(\\b|\\s|。|$)').test(text)) return true;
  return false;
}

/**
 * Mask ALL occurrences of the answer that would trigger the validator's
 * leak patterns: `= <answer>` and `答案：<answer>`.
 * Then also mask any bare word-boundary occurrences at the end of text.
 */
function maskAnswer(text, answer) {
  if (!text || !answer) return text;
  var a = String(answer).trim();
  if (a.length < 1) return text;
  var esc = a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Mask pattern: = <answer> (validator pattern 2)
  text = text.replace(new RegExp('(=\\s*)' + esc + '(?=\\b|\\s|。|$)', 'g'), '$1？');

  // Mask pattern: 答案[：:是為]<answer> (validator pattern 1)
  text = text.replace(new RegExp('(答案[：:是為]\\s*)' + esc + '(?=\\b|\\s|。|$)', 'g'), '$1？');

  // Also mask the LAST word-boundary occurrence (original behaviour for safety)
  var reWord = new RegExp('(?<![\\d./])' + esc + '(?![\\d./])', 'g');
  var matches = [];
  var mm;
  while ((mm = reWord.exec(text)) !== null) matches.push(mm);
  if (matches.length > 0) {
    var last = matches[matches.length - 1];
    text = text.substring(0, last.index) + '？' + text.substring(last.index + last[0].length);
  }

  return text;
}

/**
 * Check if text contains the answer in any form — used as a gate
 * before deciding whether to mask. For Phase A L3 generation,
 * we use the validator-compatible check.
 */
function containsAnswer(text, answer) {
  if (!text || !answer) return false;
  var a = String(answer).trim();
  if (!a) return false;
  // Use the validator's exact patterns
  return validatorLeakCheck(text, a);
}

/* ════════════════════════════════════════════════════════════════════
   Phase A: Question-Specific L3 Generation
   ════════════════════════════════════════════════════════════════════ */

/**
 * Generate L3 from `steps` field — best quality: uses actual computation steps.
 */
function genL3FromSteps(q) {
  const steps = q.steps;
  if (!steps || !steps.length) return null;
  const answer = String(q.answer || '');
  if (!answer) return null;

  const parts = [];
  let idx = 0;
  for (const step of steps) {
    if (idx >= 6) break; // max 6 steps shown
    // Skip pure "read question" steps
    if (/^讀題/.test(step) && idx === 0) continue;
    // Skip pure "check" steps at the end
    if (/^檢查/.test(step) && idx > 0) {
      parts.push(CIRCLED[idx] + ' ' + step);
      idx++;
      continue;
    }
    // Mask the answer in the step
    let s = step.replace(/^步驟\d+[：:]\s*/, '');
    if (answer && containsAnswer(s, answer)) {
      s = maskAnswer(s, answer);
    }
    parts.push(CIRCLED[idx] + ' ' + s);
    idx++;
  }
  if (parts.length < 2) return null;
  return '📐 一步步算：\n' + parts.join('\n') + '\n算完記得回頭檢查喔！✅';
}

/**
 * Generate L3 from meta fields — for questions with structured meta.
 */
function genL3FromMeta(q) {
  const meta = q.meta;
  const kind = q.kind || '';
  const answer = String(q.answer || '');
  if (!meta) return null;

  // Volume with meta.l, meta.w, meta.h
  if (/volume_rect|rect_prism/.test(kind) && meta.l && meta.w && meta.h) {
    var u = meta.unit || 'cm³';
    return '📐 動手算：\n' +
      '① 長×寬×高 = ' + meta.l + ' × ' + meta.w + ' × ' + meta.h + '\n' +
      '② 先算 ' + meta.l + '×' + meta.w + ' = ' + (meta.l * meta.w) + '\n' +
      '③ 再 × ' + meta.h + ' → ？\n' +
      '記得寫 ' + u + ' ✅';
  }

  // Fraction multiplication with meta.a, meta.b
  if (/fraction_mul|frac_mul/.test(kind) && meta.a && meta.b) {
    var fa = String(meta.a).split('/');
    var fb = String(meta.b).split('/');
    if (fa.length === 2 && fb.length === 2) {
      return '📐 動手算：\n' +
        '① 分子×分子：' + fa[0] + '×' + fb[0] + '\n' +
        '② 分母×分母：' + fa[1] + '×' + fb[1] + '\n' +
        '③ 約分到最簡 → ？\n' +
        '驗算：結果應比兩個分數都小 ✅';
    }
  }

  // Time addition with meta.start, meta.add_m
  if (/time_add/.test(kind) && meta.start && meta.add_m) {
    var parts = String(meta.start).split(':');
    var hr = parseInt(parts[0]) || 0;
    var mn = parseInt(parts[1]) || 0;
    return '📐 動手算：\n' +
      '① 起始 ' + meta.start + '，加 ' + meta.add_m + ' 分鐘\n' +
      '② 分鐘：' + mn + ' + ' + meta.add_m + '，超過 60 要進位\n' +
      '③ 得出 HH:MM → ？\n' +
      '注意 60 分鐘 = 1 小時 ✅';
  }

  // Unit conversion with meta.convert_kind
  if (/unit_convert/.test(kind) && meta.convert_kind) {
    var ck = meta.convert_kind;
    if (/kg_g/.test(ck) && typeof meta.kg !== 'undefined') {
      return '📐 動手算：\n' +
        '① 1 公斤 = 1000 公克\n' +
        '② ' + meta.kg + ' 公斤 = ' + meta.kg + ' × 1000 = ' + (meta.kg * 1000) + ' 公克\n' +
        '③ 再加 ' + (meta.g || 0) + ' 公克 → ？\n' +
        '驗算：結果 ÷ 1000 看看對不對 ✅';
    }
    return '📐 動手算：\n' +
      '① 找出換算倍率\n' +
      '② 大→小乘，小→大除\n' +
      '③ 仔細算出結果 → ？\n' +
      '驗算：換回原單位看是否一致 ✅';
  }

  // Fraction add/sub with meta.a, meta.b, meta.op
  if (/frac_addsub|fraction_addsub/.test(kind) && meta.a && meta.b && meta.op) {
    const a = meta.a, b = meta.b, op = meta.op;
    const opStr = op === '+' ? '加' : '減';
    const d1 = meta.d1 || parseInt(String(a).split('/')[1]) || 0;
    const d2 = meta.d2 || parseInt(String(b).split('/')[1]) || 0;
    if (d1 && d2) {
      const cm = lcm(d1, d2);
      return '📐 動手算：\n' +
        '① 分母不同（' + d1 + ' 和 ' + d2 + '），先通分：LCM(' + d1 + ',' + d2 + ') = ' + cm + '\n' +
        '② 把 ' + a + ' 和 ' + b + ' 都變成分母 ' + cm + '\n' +
        '③ 分子' + opStr + '，分母不變\n' +
        '④ 約分到最簡 → ？\n' +
        '驗算：結果' + (op === '+' ? '應比兩個加數都大' : '應比被減數小') + ' ✅';
    }
  }

  // Rate-time-distance with meta.rate, meta.mode
  if (/rate_time_distance/.test(kind) && meta.rate) {
    const distances = extractIntegers(q.question).filter(n => n > meta.rate);
    const dist = distances.length ? distances[0] : null;
    if (meta.mode === 't' && dist) {
      return '📐 動手算：\n' +
        '① 公式：時間 = 距離 ÷ 速率\n' +
        '② 列式：' + dist + ' ÷ ' + meta.rate + '\n' +
        '③ 做直式除法 → ？\n' +
        '驗算：速率 × 時間 = 距離（檢查是否成立）✅';
    }
    if (meta.mode === 'd' && typeof meta.time !== 'undefined') {
      return '📐 動手算：\n' +
        '① 公式：距離 = 速率 × 時間\n' +
        '② 列式：' + meta.rate + ' × ' + meta.time + '\n' +
        '③ 乘法 → ？\n' +
        '驗算：距離 ÷ 時間 = 速率 ✅';
    }
    if (meta.mode === 'v') {
      return '📐 動手算：\n' +
        '① 公式：速率 = 距離 ÷ 時間\n' +
        '② 找出題目中的距離和時間，列除法式\n' +
        '③ 做直式除法 → ？\n' +
        '驗算：速率 × 時間 = 距離 ✅';
    }
  }

  // Fraction average with meta.people, meta.total
  if (/avg_fraction/.test(kind) && meta.people && meta.total) {
    return '📐 動手算：\n' +
      '① 總量 ÷ 人數 = 平均\n' +
      '② 列式：' + meta.total + ' ÷ ' + meta.people + '\n' +
      '③ 除以整數 = 乘以 1/' + meta.people + '（分母×' + meta.people + '）\n' +
      '④ 約分 → ？\n' +
      '驗算：答案 × ' + meta.people + ' 應= ' + meta.total + ' ✅';
  }

  // Fraction × integer
  if (/frac_times_int/.test(kind) && meta.a) {
    const ints = extractIntegers(q.question);
    const multiplier = ints.find(n => n > 1) || '';
    if (multiplier) {
      return '📐 動手算：\n' +
        '① 分數 × 整數：分子 × ' + multiplier + '，分母不變\n' +
        '② 列式：' + meta.a + ' × ' + multiplier + '\n' +
        '③ 算出結果，約分到最簡 → ？\n' +
        '驗算：結果應比原分數大 ' + multiplier + ' 倍 ✅';
    }
  }

  // Discount/percent with meta
  if (/discount_percent/.test(kind)) {
    const nums = extractIntegers(q.question);
    const prices = nums.filter(n => n >= 10);
    const discounts = nums.filter(n => n >= 1 && n <= 9);
    if (prices.length && discounts.length) {
      const price = prices[0];
      const disc = discounts[discounts.length - 1];
      return '📐 動手算：\n' +
        '① 打 ' + disc + ' 折 = 付原價的 ' + disc + '/10 = ' + (disc * 10) + '%\n' +
        '② 列式：' + price + ' × ' + disc + '/10 = ' + price + ' × 0.' + disc + '\n' +
        '③ 算出折後價 → ？\n' +
        '驗算：折後價應 < 原價 ' + price + ' 元 ✅';
    }
  }

  // Ratio/recipe with meta
  if (/ratio_recipe/.test(kind)) {
    const nums = extractIntegers(q.question);
    if (nums.length >= 2) {
      return '📐 動手算：\n' +
        '① 先算比的總份數（各項的比加起來）\n' +
        '② 每份 = 全部量 ÷ 總份數\n' +
        '③ 求某項 = 該項份數 × 每份量 → ？\n' +
        '驗算：各項加起來 = 全部量 ✅';
    }
  }

  // Unit conversion (decimal)
  if (/unit_convert_decimal/.test(kind)) {
    const decs = extractDecimals(q.question);
    const ints = extractIntegers(q.question);
    return '📐 動手算：\n' +
      '① 找出換算倍率（如 1 公里=1000 公尺）\n' +
      '② 有小數就注意小數點移動方向和位數\n' +
      '③ 做乘法或除法 → ？\n' +
      '驗算：換回原單位看是否一致 ✅';
  }

  return null;
}

/**
 * Generate L3 from question text numbers — fallback for questions without steps/meta.
 */
function genL3FromQuestionText(q) {
  const kind = q.kind || '';
  const text = q.question || '';
  const answer = String(q.answer || '');

  // Decimal multiplication kinds
  if (/d_mul|decimal_mul|decimal_times/.test(kind)) {
    const decs = extractDecimals(text);
    const ints = extractIntegers(text);
    if (decs.length >= 1) {
      const dec = decs[0];
      const dp = decimalPlaces(dec);
      const otherNum = decs.length >= 2 ? decs[1] : (ints.length ? ints[ints.length - 1] : null);
      if (otherNum !== null) {
        const totalDp = dp + decimalPlaces(otherNum);
        return '📐 動手算：\n' +
          '① 去掉小數點：把 ' + dec + ' 當成 ' + Math.round(dec * Math.pow(10, dp)) + '\n' +
          '② 當整數做乘法：' + Math.round(dec * Math.pow(10, dp)) + ' × ' + (Number.isInteger(otherNum) ? otherNum : Math.round(otherNum * Math.pow(10, decimalPlaces(otherNum)))) + '\n' +
          '③ 小數位數共 ' + totalDp + ' 位，從右往左數放小數點 → ？\n' +
          '驗算：估算 ' + Math.round(dec) + '×' + Math.round(otherNum) + ' 看答案大概對不對 ✅';
      }
    }
  }

  // Decimal division kinds
  if (/d_div|decimal_div/.test(kind)) {
    const decs = extractDecimals(text);
    const ints = extractIntegers(text);
    if (decs.length >= 1 && ints.length >= 1) {
      return '📐 動手算：\n' +
        '① 被除數 ' + decs[0] + ' 的小數點「抬上去」到商的位置\n' +
        '② 按正常除法步驟做\n' +
        '③ 不夠除就補 0 繼續 → ？\n' +
        '驗算：商 × 除數，看是否等於被除數 ✅';
    }
  }

  // Fraction operations
  if (/simplify/.test(kind)) {
    const fracs = extractFractions(text);
    if (fracs.length >= 1) {
      const f = fracs[0];
      const g = gcd(f.n, f.d);
      return '📐 動手算：\n' +
        '① 找 ' + f.n + ' 和 ' + f.d + ' 的最大公因數\n' +
        '② GCD = ' + g + '\n' +
        '③ 分子分母同除以 ' + g + ' → ？\n' +
        '驗算：結果的分子分母再也找不到共同因數 ✅';
    }
  }

  if (/add_unlike|sub_unlike/.test(kind)) {
    const fracs = extractFractions(text);
    if (fracs.length >= 2) {
      const cm = lcm(fracs[0].d, fracs[1].d);
      const opStr = /sub/.test(kind) ? '減' : '加';
      return '📐 動手算：\n' +
        '① 分母不同（' + fracs[0].d + ' 和 ' + fracs[1].d + '），通分\n' +
        '② LCM = ' + cm + '，兩個分數都變成分母 ' + cm + '\n' +
        '③ 分子' + opStr + ' → 約分到最簡 → ？ ✅';
    }
  }

  // ×10 shift
  if (/x10_shift/.test(kind)) {
    const decs = extractDecimals(text);
    if (decs.length >= 1) {
      return '📐 動手算：\n' +
        '① 找出乘以還是除以 10/100/1000\n' +
        '② 乘→小數點右移，除→小數點左移\n' +
        '③ ' + decs[0] + ' 的小數點移動 → ？\n' +
        '位數數好，不夠的補 0 ✅';
    }
  }

  // Volume
  if (/volume_rect|rect_cm3/.test(kind)) {
    const nums = extractIntegers(text);
    if (nums.length >= 3) {
      const dims = nums.slice(-3);
      return '📐 動手算：\n' +
        '① 長×寬×高 = ' + dims[0] + ' × ' + dims[1] + ' × ' + dims[2] + '\n' +
        '② 先算 ' + dims[0] + '×' + dims[1] + ' = ' + (dims[0] * dims[1]) + '\n' +
        '③ 再 × ' + dims[2] + ' → ？\n' +
        '記得寫 cm³ 或 m³ ✅';
    }
  }

  // Integer ÷ integer → decimal
  if (/int_div_int_to_decimal/.test(kind)) {
    const nums = extractIntegers(text);
    if (nums.length >= 2) {
      return '📐 動手算：\n' +
        '① ' + nums[0] + ' ÷ ' + nums[1] + '，除不盡\n' +
        '② 在 ' + nums[0] + ' 後面補小數點和 0\n' +
        '③ 繼續直式除法 → ？\n' +
        '商的小數點對齊被除數的小數點 ✅';
    }
  }

  return null;
}

/**
 * Determine if a question's L3 is currently "kind-generic"
 * (same for all questions of that kind within this bank).
 */
function buildKindL3Map(bank) {
  const kindL3 = {};
  for (const q of bank) {
    const kind = q.kind || q.subskill || 'unknown';
    const hints = q.hints || [];
    const l3 = hints.length >= 3 ? String(hints[2]) : '';
    if (!kindL3[kind]) kindL3[kind] = { texts: new Set(), count: 0 };
    kindL3[kind].texts.add(l3);
    kindL3[kind].count++;
  }
  return kindL3;
}

/* ════════════════════════════════════════════════════════════════════
   Phase B: Question-Specific CM Generation
   ════════════════════════════════════════════════════════════════════ */

/**
 * Compute a WRONG answer and build a question-specific CM.
 */
function genQuestionSpecificCM(q) {
  const kind = q.kind || '';
  const text = q.question || '';
  const answer = String(q.answer || '');
  const meta = q.meta || {};
  const cms = [];

  // Fraction add/sub: common mistake is adding numerators without LCD
  if (/frac_addsub|add_unlike|sub_unlike|fraction_addsub/.test(kind)) {
    const fracs = extractFractions(text);
    if (fracs.length >= 2 && fracs[0].d !== fracs[1].d) {
      const wrongNumer = /sub/.test(kind) || (meta.op === '-')
        ? fracs[0].n - fracs[1].n
        : fracs[0].n + fracs[1].n;
      const wrongDenom = fracs[0].d + fracs[1].d;
      cms.push('直接分子相' + (/sub/.test(kind) || meta.op === '-' ? '減' : '加') +
        '寫成 ' + Math.abs(wrongNumer) + '/' + wrongDenom +
        '（忘了先通分，分母不能直接相加）。');
    }
    if (fracs.length >= 2) {
      cms.push('通分時倍數算錯，導致分子或分母出錯。');
    }
  }

  // Decimal multiplication
  if (/d_mul|decimal_mul|decimal_times/.test(kind)) {
    const decs = extractDecimals(text);
    if (decs.length >= 1) {
      const dp = decimalPlaces(decs[0]);
      cms.push('忘了放回小數點，直接把整數乘法的結果當成答案。');
      cms.push('小數位數數錯（' + decs[0] + ' 有 ' + dp + ' 位小數），小數點位置放錯。');
    }
  }

  // Decimal division
  if (/d_div|decimal_div/.test(kind)) {
    cms.push('商的小數點沒有對齊被除數的小數點。');
    cms.push('不夠除時忘了在商上補 0。');
  }

  // Simplify
  if (/simplify/.test(kind)) {
    const fracs = extractFractions(text);
    if (fracs.length >= 1) {
      const f = fracs[0];
      const g = gcd(f.n, f.d);
      if (g > 1) {
        // Find a smaller common factor that isn't GCD
        for (let i = 2; i < g; i++) {
          if (f.n % i === 0 && f.d % i === 0) {
            cms.push('只約了 ' + i + ' 而不是最大公因數 ' + g + '，答案 ' +
              (f.n / i) + '/' + (f.d / i) + ' 還可以繼續約。');
            break;
          }
        }
      }
      cms.push('分子分母除以不同的數，比例改變了。');
    }
  }

  // Volume
  if (/volume|rect_cm3|cube_cm3/.test(kind)) {
    const nums = extractIntegers(text).filter(n => n > 0 && n < 1000);
    if (nums.length >= 2) {
      cms.push('只算了 ' + nums[0] + '×' + nums[1] + '（面積），忘了再乘第三個維度。');
      cms.push('單位寫成 cm²（平方）而不是 cm³（立方）。');
    }
  }

  // Percent/discount
  if (/discount|percent/.test(kind)) {
    cms.push('折扣率和實付率搞反了（打 7 折 = 付 70%，不是減 7）。');
    cms.push('百分率忘了 ÷100 就直接乘。');
  }

  // Time
  if (/time_add/.test(kind)) {
    cms.push('分鐘超過 60 但沒有進位到小時（60 進位不是 100 進位）。');
    cms.push('進位後分鐘忘了減 60。');
  }

  // Ratio
  if (/ratio_recipe|proportional_split/.test(kind)) {
    cms.push('忘了先算總份數就直接除。');
    cms.push('每份量算錯導致後面全錯。');
  }

  // Commercial pack kinds
  if (/original/.test(kind)) {
    const fracs = extractFractions(text);
    const ints = extractIntegers(text);
    if (fracs.length && ints.length) {
      cms.push('用已知量 × 分數（應該是 ÷ 分數）來反推原量。');
      cms.push('÷分數忘了改成 ×倒數。');
    }
  }
  if (/part_to_total/.test(kind)) {
    cms.push('部分和全體弄反了（分數的分子和分母對調）。');
    cms.push('忘了約分成最簡分數。');
  }
  if (/remain$/.test(kind)) {
    cms.push('用掉的分數和剩下的分數搞反（剩下 = 1−用掉）。');
    cms.push('忘了把 1 和用掉的分數先做減法。');
  }
  if (/remain_multi/.test(kind)) {
    cms.push('第二次的基準量用了「全部」而不是「第一次剩下的」。');
    cms.push('兩次剩餘的順序搞反了。');
  }
  if (/compare/.test(kind)) {
    cms.push('通分後分子大小比較錯誤。');
    cms.push('忘了通分就直接比較分子。');
  }

  // Unit conversion
  if (/unit_convert/.test(kind)) {
    cms.push('換算倍率記錯（如公里→公尺是 ×1000）。');
    cms.push('乘除方向搞反（大→小要乘、小→大要除）。');
  }

  // Generic fallback if nothing specific generated
  if (cms.length === 0) {
    const nums = extractIntegers(text);
    const decs = extractDecimals(text);
    const fracs = extractFractions(text);
    if (fracs.length >= 1) {
      cms.push('分數運算時分子分母算錯。');
      cms.push('忘了約分或通分。');
    } else if (decs.length >= 1) {
      cms.push('小數點位置放錯。');
      cms.push('計算粗心，數字抄錯。');
    } else if (nums.length >= 2) {
      cms.push('計算粗心，數字看錯或抄錯。');
      cms.push('公式記錯或套錯。');
    } else {
      cms.push('計算粗心。');
      cms.push('單位或標記寫錯。');
    }
  }

  return cms.slice(0, 2); // Max 2 CMs per question
}

/**
 * Check if a question's CM is kind-generic (same as all others of that kind).
 */
function buildKindCMMap(bank) {
  const kindCM = {};
  for (const q of bank) {
    const kind = q.kind || q.subskill || 'unknown';
    const cm = q.common_mistakes ? JSON.stringify(q.common_mistakes) : '';
    if (!kindCM[kind]) kindCM[kind] = { texts: new Set(), count: 0 };
    kindCM[kind].texts.add(cm);
    kindCM[kind].count++;
  }
  return kindCM;
}

/* ════════════════════════════════════════════════════════════════════
   Bank I/O helpers
   ════════════════════════════════════════════════════════════════════ */
function loadBank(dir, gvar, filename) {
  const bankPath = path.join(DOCS, dir, filename);
  if (!fs.existsSync(bankPath)) return null;
  const src = fs.readFileSync(bankPath, 'utf8');
  const sandbox = { window: {} };
  vm.createContext(sandbox);
  try {
    vm.runInContext(src, sandbox, { filename: bankPath, timeout: 10000 });
  } catch (e) {
    console.log('  ⚠ ' + dir + ': parse error: ' + e.message);
    return null;
  }
  const bank = sandbox.window[gvar];
  if (!Array.isArray(bank)) return null;
  return { bank, src, bankPath };
}

function writeBank(bankPath, gvar, bank) {
  const bankStr = JSON.stringify(bank, null, 2);
  const content = 'window.' + gvar + ' = ' + bankStr + ';\n';
  fs.writeFileSync(bankPath, content, 'utf8');

  // Also write to dist
  const distPath = bankPath.replace(DOCS, DIST);
  if (fs.existsSync(path.dirname(distPath))) {
    fs.writeFileSync(distPath, content, 'utf8');
  }
}

function loadJsonBank(dir, filename) {
  const jsonPath = path.join(DOCS, dir, filename);
  if (!fs.existsSync(jsonPath)) return null;
  const src = fs.readFileSync(jsonPath, 'utf8');
  const bank = JSON.parse(src);
  return { bank, jsonPath };
}

function writeJsonBank(jsonPath, bank) {
  const content = JSON.stringify(bank, null, 2) + '\n';
  fs.writeFileSync(jsonPath, content, 'utf8');
  const distPath = jsonPath.replace(DOCS, DIST);
  if (fs.existsSync(path.dirname(distPath))) {
    fs.writeFileSync(distPath, content, 'utf8');
  }
}

/* ════════════════════════════════════════════════════════════════════
   Process a single module
   ════════════════════════════════════════════════════════════════════ */
function processModule(dir, gvar, filename, isJson) {
  let bank, bankPath, jsonPath;

  if (isJson) {
    const result = loadJsonBank(dir, filename);
    if (!result) return null;
    bank = result.bank;
    jsonPath = result.jsonPath;
  } else {
    const result = loadBank(dir, gvar, filename);
    if (!result) return null;
    bank = result.bank;
    bankPath = result.bankPath;
  }

  const kindL3Map = buildKindL3Map(bank);
  const kindCMMap = buildKindCMMap(bank);

  let l3Upgraded = 0, cmUpgraded = 0, cmAdded = 0, leaksFixed = 0;

  for (const q of bank) {
    const kind = q.kind || q.subskill || 'unknown';
    const hints = q.hints || [];
    const answer = String(q.answer || '');

    // ── Phase A: Upgrade L3 from kind-generic to question-specific ──
    if (hints.length >= 3) {
      const kindInfo = kindL3Map[kind];
      const isGeneric = kindInfo && kindInfo.texts.size <= 1 && kindInfo.count > 1;

      if (isGeneric) {
        // Try to generate question-specific L3
        // If a generator produces the SAME text as current L3, try the next one
        let newL3 = genL3FromSteps(q);
        if (!newL3 || newL3 === hints[2]) newL3 = genL3FromMeta(q);
        if (!newL3 || newL3 === hints[2]) newL3 = genL3FromQuestionText(q);

        if (newL3 && newL3 !== hints[2]) {
          // Proactively mask any leaks in the new L3
          let safe = maskAnswer(newL3, answer);
          // If it STILL leaks after masking, don't use it
          if (!validatorLeakCheck(safe, answer)) {
            hints[2] = safe;
            l3Upgraded++;
          }
        }
      }
    }

    // ── Phase B: Upgrade CM from kind-generic to question-specific ──
    const cmInfo = kindCMMap[kind];
    const cmIsGeneric = cmInfo && cmInfo.texts.size <= 1 && cmInfo.count > 1;

    if (!q.common_mistakes || !q.common_mistakes.length) {
      // No CM at all → add
      const newCM = genQuestionSpecificCM(q);
      if (newCM.length) {
        q.common_mistakes = newCM;
        cmAdded++;
      }
    } else if (cmIsGeneric) {
      // CM exists but is generic → upgrade
      const newCM = genQuestionSpecificCM(q);
      if (newCM.length && JSON.stringify(newCM) !== JSON.stringify(q.common_mistakes)) {
        q.common_mistakes = newCM;
        cmUpgraded++;
      }
    }

    // ── Phase C: Final answer-leak guard ──
    // Check ONLY hints[-1] since that's what the validator checks
    if (hints.length > 0) {
      const lastIdx = hints.length - 1;
      if (validatorLeakCheck(hints[lastIdx], answer)) {
        const before = hints[lastIdx];
        hints[lastIdx] = maskAnswer(hints[lastIdx], answer);
        if (hints[lastIdx] !== before) leaksFixed++;
      }
    }
  }

  // Write changes
  if (apply && (l3Upgraded || cmUpgraded || cmAdded || leaksFixed)) {
    if (isJson) {
      writeJsonBank(jsonPath, bank);
    } else {
      writeBank(bankPath, gvar, bank);
    }
  }

  return {
    dir,
    total: bank.length,
    l3Upgraded,
    cmUpgraded,
    cmAdded,
    leaksFixed,
    // For reporting: count how many are still generic
    genericL3: Object.values(kindL3Map).filter(k => k.texts.size <= 1 && k.count > 1).reduce((s, k) => s + k.count, 0),
    genericCM: Object.values(kindCMMap).filter(k => k.texts.size <= 1 && k.count > 1).reduce((s, k) => s + k.count, 0),
  };
}

/* ════════════════════════════════════════════════════════════════════
   Main
   ════════════════════════════════════════════════════════════════════ */

console.log('╔═══════════════════════════════════════════════════════════╗');
console.log('║  AUTO-ITERATE V2: QUESTION-SPECIFIC OPTIMIZER            ║');
console.log('║  Mode: ' + (reportOnly ? 'REPORT ONLY' : (apply ? '✅ APPLY' : '🔍 DRY-RUN')) + '                                         ║');
console.log('╚═══════════════════════════════════════════════════════════╝');
console.log('');

if (reportOnly) {
  console.log('Module'.padEnd(48) + 'Qs'.padStart(6) + ' GenL3'.padStart(7) + ' GenCM'.padStart(7));
  console.log('─'.repeat(70));
} else {
  console.log('Module'.padEnd(48) + 'Qs'.padStart(6) + ' L3↑'.padStart(6) + ' CM↑'.padStart(6) + ' CM+'.padStart(6) + ' Leak'.padStart(6));
  console.log('─'.repeat(78));
}

const totals = { qs: 0, l3: 0, cmUp: 0, cmAdd: 0, leaks: 0, genL3: 0, genCM: 0 };

for (const [dir, gvar, fn] of MODULES) {
  const r = processModule(dir, gvar, fn, false);
  if (!r) continue;
  if (reportOnly) {
    console.log(r.dir.padEnd(48) + String(r.total).padStart(6) + String(r.genericL3).padStart(7) + String(r.genericCM).padStart(7));
  } else {
    console.log(r.dir.padEnd(48) + String(r.total).padStart(6) + String(r.l3Upgraded).padStart(6) + String(r.cmUpgraded).padStart(6) + String(r.cmAdded).padStart(6) + String(r.leaksFixed).padStart(6));
  }
  totals.qs += r.total; totals.l3 += r.l3Upgraded; totals.cmUp += r.cmUpgraded;
  totals.cmAdd += r.cmAdded; totals.leaks += r.leaksFixed;
  totals.genL3 += r.genericL3; totals.genCM += r.genericCM;
}

for (const [dir, fn] of JSON_MODULES) {
  const r = processModule(dir, null, fn, true);
  if (!r) continue;
  if (reportOnly) {
    console.log(r.dir.padEnd(48) + String(r.total).padStart(6) + String(r.genericL3).padStart(7) + String(r.genericCM).padStart(7));
  } else {
    console.log(r.dir.padEnd(48) + String(r.total).padStart(6) + String(r.l3Upgraded).padStart(6) + String(r.cmUpgraded).padStart(6) + String(r.cmAdded).padStart(6) + String(r.leaksFixed).padStart(6));
  }
  totals.qs += r.total; totals.l3 += r.l3Upgraded; totals.cmUp += r.cmUpgraded;
  totals.cmAdd += r.cmAdded; totals.leaks += r.leaksFixed;
  totals.genL3 += r.genericL3; totals.genCM += r.genericCM;
}

console.log('─'.repeat(reportOnly ? 70 : 78));
if (reportOnly) {
  console.log('TOTAL'.padEnd(48) + String(totals.qs).padStart(6) + String(totals.genL3).padStart(7) + String(totals.genCM).padStart(7));
  console.log('');
  console.log('  Generic L3: ' + totals.genL3 + '/' + totals.qs + ' Qs (' + (totals.qs ? (totals.genL3 * 100 / totals.qs).toFixed(1) : 0) + '%)');
  console.log('  Generic CM: ' + totals.genCM + '/' + totals.qs + ' Qs (' + (totals.qs ? (totals.genCM * 100 / totals.qs).toFixed(1) : 0) + '%)');
} else {
  console.log('TOTAL'.padEnd(48) + String(totals.qs).padStart(6) + String(totals.l3).padStart(6) + String(totals.cmUp).padStart(6) + String(totals.cmAdd).padStart(6) + String(totals.leaks).padStart(6));
  console.log('');
  console.log('  L3 upgraded to question-specific: ' + totals.l3);
  console.log('  CM upgraded to question-specific: ' + totals.cmUp);
  console.log('  CM added (was missing):           ' + totals.cmAdd);
  console.log('  Answer leaks fixed:               ' + totals.leaks);
}

if (!apply && !reportOnly) {
  console.log('');
  console.log('👆 Dry-run. To apply: node tools/auto_iterate_v2_question_specific.cjs --apply');
}
if (apply) {
  console.log('');
  console.log('✅ Changes written to docs/ and dist_ai_math_web_pages/docs/');
  console.log('   Next: python tools/validate_all_elementary_banks.py');
}
