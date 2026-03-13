#!/usr/bin/env node
/**
 * audit_hint_clarity.cjs — 提示文案品質稽核
 *
 * 掃描 docs/ 下所有 bank.js，檢查：
 *   1) L3 露答案 (answer leak)
 *   2) L1 過長   (> 60 字 by default)
 *   3) L2 無列式引導 (missing formula keyword)
 *
 * 輸出：
 *   artifacts/hint_clarity_audit.json
 *   終端摘要（總掃描題數、違規數、前 20 筆）
 *
 * Exit code: 0 全通過, 1 有違規
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const DOCS_DIR = path.resolve(__dirname, '..', 'docs');
const OUT_DIR = path.resolve(__dirname, '..', 'artifacts');
const OUT_FILE = path.join(OUT_DIR, 'hint_clarity_audit.json');

const L1_MAX_CHARS = 60;
const L2_FORMULA_RE = /列式|算式|先寫成|寫出|化成|通分|擴分|約分|約掉|乘以|除以|加上|減去|乘法|除法|加法|減法|相乘|相加|相減|相除|分子|分母|加總|小數|×|÷|\+|＋|－|−|=|＝|公因數|公倍數|LCM|GCD|左移|右移|位數|換算|比例|倍|立方|平方|算出|大\s*[−\-－]\s*小|整除|試除|對稱軸|因數|質數|合數|比較.*大|比較.*小|最大|最小/;

// ── scanBanks ──────────────────────────────────────────────
function scanBanks() {
  const banks = [];
  const dirs = fs.readdirSync(DOCS_DIR, { withFileTypes: true });
  for (const d of dirs) {
    if (!d.isDirectory()) continue;
    const bankPath = path.join(DOCS_DIR, d.name, 'bank.js');
    if (!fs.existsSync(bankPath)) continue;
    try {
      const src = fs.readFileSync(bankPath, 'utf8');
      // Create a minimal sandbox with window to capture bank assignment
      const sandbox = { window: {} };
      vm.createContext(sandbox);
      vm.runInContext(src, sandbox, { filename: bankPath, timeout: 5000 });
      // Find the bank array (first array property on window)
      let items = null;
      for (const key of Object.keys(sandbox.window)) {
        if (Array.isArray(sandbox.window[key])) {
          items = sandbox.window[key];
          break;
        }
      }
      if (items && items.length) {
        banks.push({ module: d.name, file: bankPath, items });
      }
    } catch (err) {
      console.error(`⚠  Failed to parse ${bankPath}: ${err.message}`);
    }
  }
  return banks;
}

// ── checkLadderPolicy ──────────────────────────────────────
function checkLadderPolicy(banks) {
  const violations = [];

  for (const bank of banks) {
    for (const q of bank.items) {
      const id = q.id || '(no id)';
      const answer = String(q.answer || '');
      const hints = Array.isArray(q.hints) ? q.hints : [];

      // L1 check (index 0): char length
      if (hints[0]) {
        const l1Text = String(hints[0]).replace(/^Hint\s*\d[｜|].+?\n/i, '').trim();
        if (l1Text.length > L1_MAX_CHARS) {
          violations.push({
            rule: 'L1_TOO_LONG',
            module: bank.module,
            question_id: id,
            detail: `L1 長度 ${l1Text.length} 字（上限 ${L1_MAX_CHARS}）`,
            hint_text: l1Text.substring(0, 80) + (l1Text.length > 80 ? '…' : ''),
          });
        }
      }

      // L2 check (index 1): must contain formula keyword
      if (hints[1]) {
        const l2Text = String(hints[1]).replace(/^Hint\s*\d[｜|].+?\n/i, '').trim();
        if (l2Text.length > 0 && !L2_FORMULA_RE.test(l2Text)) {
          violations.push({
            rule: 'L2_NO_FORMULA',
            module: bank.module,
            question_id: id,
            detail: 'L2 缺少列式引導關鍵字',
            hint_text: l2Text.substring(0, 80) + (l2Text.length > 80 ? '…' : ''),
          });
        }
      }

      // L3 check (index 2): must NOT contain the final answer verbatim
      if (hints[2] && answer) {
        const l3Text = String(hints[2]).replace(/^Hint\s*\d[｜|].+?\n/i, '').trim();
        const ansNorm = answer.replace(/\s+/g, '');
        const qText = String(q.question || '');
        if (ansNorm.length >= 1) {
          // Build answer variants
          const variants = [answer.trim()];
          // Fraction → decimal
          const fMatch = answer.match(/^(\d+)\s*[\/／]\s*(\d+)$/);
          if (fMatch) {
            const dec = parseInt(fMatch[1], 10) / parseInt(fMatch[2], 10);
            if (isFinite(dec)) {
              const decStr = String(Math.round(dec * 10000) / 10000);
              // Skip if the decimal already appears in the question text
              // (e.g. "把小數 0.532 寫成最簡分數" — student already sees it)
              if (!qText.includes(decStr)) {
                variants.push(decStr);
              }
            }
          }
          // With unit stripped
          const uMatch = answer.match(/^([\d.\/]+)\s*([^\d.\/]+)$/);
          if (uMatch) variants.push(uMatch[1].trim());

          for (const v of variants) {
            if (!v || v.length < 1) continue;
            const vNorm = v.replace(/\s+/g, '');
            const l3Norm = l3Text.replace(/\s+/g, '');
            // Check: answer appears as a standalone token
            const re = new RegExp('(?:^|[^\\d./])' + escapeRegex(vNorm) + '(?:[^\\d./]|$)');
            if (re.test(l3Norm)) {
              // L3 contains the answer — but skip if it's "自行" or masked
              if (!/自行|先自己算|請.*完成/.test(l3Text.substring(Math.max(0, l3Text.indexOf(v) - 10), l3Text.indexOf(v) + v.length + 10))) {
                violations.push({
                  rule: 'L3_ANSWER_LEAK',
                  module: bank.module,
                  question_id: id,
                  detail: `L3 含答案「${v}」`,
                  hint_text: l3Text.substring(0, 100) + (l3Text.length > 100 ? '…' : ''),
                });
                break; // one violation per question is enough
              }
            }
          }
        }
      }
    }
  }

  return violations;
}

function escapeRegex(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ── reportViolations ───────────────────────────────────────
function reportViolations(banks, violations) {
  const totalQuestions = banks.reduce((s, b) => s + b.items.length, 0);
  const totalBanks = banks.length;

  const summary = {
    scanned_banks: totalBanks,
    scanned_questions: totalQuestions,
    total_violations: violations.length,
    by_rule: {},
    violations: violations,
  };

  for (const v of violations) {
    summary.by_rule[v.rule] = (summary.by_rule[v.rule] || 0) + 1;
  }

  // Write JSON
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT_FILE, JSON.stringify(summary, null, 2), 'utf8');

  // Terminal output
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log('  Hint Clarity Audit');
  console.log('═══════════════════════════════════════════════');
  console.log(`  Banks scanned  : ${totalBanks}`);
  console.log(`  Questions      : ${totalQuestions}`);
  console.log(`  Violations     : ${violations.length}`);
  for (const [rule, cnt] of Object.entries(summary.by_rule)) {
    console.log(`    ${rule}: ${cnt}`);
  }
  console.log('───────────────────────────────────────────────');

  if (violations.length === 0) {
    console.log('  ✅ ALL CLEAR — no hint clarity violations.');
  } else {
    console.log(`  Top ${Math.min(20, violations.length)} violations:`);
    for (const v of violations.slice(0, 20)) {
      console.log(`  [${v.rule}] ${v.module} / ${v.question_id}`);
      console.log(`    ${v.detail}`);
    }
    if (violations.length > 20) {
      console.log(`  ... and ${violations.length - 20} more (see ${OUT_FILE})`);
    }
  }
  console.log('═══════════════════════════════════════════════');
  console.log(`  Output: ${OUT_FILE}`);
  console.log('');

  return summary;
}

// ── Main ───────────────────────────────────────────────────
function main() {
  const banks = scanBanks();
  if (banks.length === 0) {
    console.error('ERROR: No bank.js files found under docs/');
    process.exit(1);
  }
  const violations = checkLadderPolicy(banks);
  reportViolations(banks, violations);
  process.exit(violations.length > 0 ? 1 : 0);
}

main();
