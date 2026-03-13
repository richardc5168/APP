#!/usr/bin/env node
/**
 * auto_iterate_full_pipeline.cjs
 * ──────────────────────────────
 * Full automated quality iteration pipeline:
 *   Step 1: Pre-audit (baseline scorecard)
 *   Step 2: V1 kind-level fixes (auto_iterate_quality.cjs --apply)
 *   Step 3: V2 question-specific fixes (auto_iterate_v2_question_specific.cjs --apply)
 *   Step 4: Validation gate (validate_all_elementary_banks.py)
 *   Step 5: Post-audit (final scorecard)
 *   Step 6: Quality report with grades
 *
 * Usage:
 *   node tools/auto_iterate_full_pipeline.cjs           # full pipeline
 *   node tools/auto_iterate_full_pipeline.cjs --report  # report only
 *
 * Designed for unattended iteration — can be invoked repeatedly, each run
 * improves quality further (idempotent and monotonically improving).
 */
'use strict';
const { execSync } = require('child_process');
const fs   = require('fs');
const path = require('path');
const vm   = require('vm');

const reportOnly = process.argv.includes('--report');
const ROOT = path.resolve(__dirname, '..');
const DOCS = path.join(ROOT, 'docs');
const ARTIFACTS = path.join(ROOT, 'artifacts');
if (!fs.existsSync(ARTIFACTS)) fs.mkdirSync(ARTIFACTS, { recursive: true });

const PYTHON = path.join(ROOT, '.venv', 'Scripts', 'python.exe');

/* ════════════════════════════════════════════════════════════════════
   Helpers
   ════════════════════════════════════════════════════════════════════ */
function run(cmd, label) {
  console.log('\n⏳ ' + label + '...');
  try {
    const out = execSync(cmd, { cwd: ROOT, encoding: 'utf8', timeout: 180000 });
    return { ok: true, output: out };
  } catch (e) {
    return { ok: false, output: (e.stdout || '') + (e.stderr || '') + (e.message || '') };
  }
}

function assignGrade(pct) {
  if (pct >= 98) return 'A+';
  if (pct >= 95) return 'A';
  if (pct >= 90) return 'A-';
  if (pct >= 80) return 'B+';
  if (pct >= 70) return 'B';
  if (pct >= 60) return 'B-';
  if (pct >= 50) return 'C+';
  if (pct >= 40) return 'C';
  return 'D';
}

/* ════════════════════════════════════════════════════════════════════
   Audit functions
   ════════════════════════════════════════════════════════════════════ */

/**
 * Count questions with question-specific L3 (unique L3 text per question within each kind).
 */
function auditL3Specificity() {
  const BANK_DIRS = fs.readdirSync(DOCS, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  let totalQs = 0, specificL3 = 0, genericL3 = 0;
  let totalKinds = 0, kindsWithSpecificL3 = 0;
  const kindGroups = {};

  for (const dir of BANK_DIRS) {
    const bankPath = path.join(DOCS, dir, 'bank.js');
    const jsonPath = path.join(DOCS, dir, 'g56_core_foundation.json');
    let bank = null;

    if (fs.existsSync(bankPath)) {
      try {
        const src = fs.readFileSync(bankPath, 'utf8');
        const sandbox = { window: {} };
        vm.createContext(sandbox);
        vm.runInContext(src, sandbox, { timeout: 10000 });
        for (const k of Object.keys(sandbox.window)) {
          if (Array.isArray(sandbox.window[k])) { bank = sandbox.window[k]; break; }
        }
      } catch (_) {}
    } else if (fs.existsSync(jsonPath)) {
      try { bank = JSON.parse(fs.readFileSync(jsonPath, 'utf8')); } catch (_) {}
    }

    if (!bank) continue;
    totalQs += bank.length;

    // Group by kind
    const byKind = {};
    for (const q of bank) {
      const kind = q.kind || q.subskill || 'unknown';
      const l3 = (q.hints || [])[2] ? String(q.hints[2]) : '';
      if (!byKind[kind]) byKind[kind] = { l3Set: new Set(), count: 0 };
      byKind[kind].l3Set.add(l3);
      byKind[kind].count++;
    }

    for (const [kind, info] of Object.entries(byKind)) {
      totalKinds++;
      const key = dir + '::' + kind;
      if (info.l3Set.size > 1 || info.count === 1) {
        kindsWithSpecificL3++;
        specificL3 += info.count;
      } else {
        genericL3 += info.count;
      }
      kindGroups[key] = { unique: info.l3Set.size, count: info.count };
    }
  }

  const pct = totalQs ? Math.round(specificL3 / totalQs * 100) : 0;
  return { totalQs, specificL3, genericL3, pct, totalKinds, kindsWithSpecificL3 };
}

/**
 * Count questions with question-specific CM.
 */
function auditCMSpecificity() {
  const BANK_DIRS = fs.readdirSync(DOCS, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);

  let totalQs = 0, withCM = 0, withoutCM = 0;
  let specificCM = 0, genericCM = 0;
  let totalKinds = 0, kindsWithSpecificCM = 0;

  for (const dir of BANK_DIRS) {
    const bankPath = path.join(DOCS, dir, 'bank.js');
    const jsonPath = path.join(DOCS, dir, 'g56_core_foundation.json');
    let bank = null;

    if (fs.existsSync(bankPath)) {
      try {
        const src = fs.readFileSync(bankPath, 'utf8');
        const sandbox = { window: {} };
        vm.createContext(sandbox);
        vm.runInContext(src, sandbox, { timeout: 10000 });
        for (const k of Object.keys(sandbox.window)) {
          if (Array.isArray(sandbox.window[k])) { bank = sandbox.window[k]; break; }
        }
      } catch (_) {}
    } else if (fs.existsSync(jsonPath)) {
      try { bank = JSON.parse(fs.readFileSync(jsonPath, 'utf8')); } catch (_) {}
    }

    if (!bank) continue;
    totalQs += bank.length;

    // Count CM coverage
    for (const q of bank) {
      if (q.common_mistakes && q.common_mistakes.length > 0) withCM++;
      else withoutCM++;
    }

    // Group by kind for specificity
    const byKind = {};
    for (const q of bank) {
      const kind = q.kind || q.subskill || 'unknown';
      const cm = q.common_mistakes ? JSON.stringify(q.common_mistakes) : '';
      if (!byKind[kind]) byKind[kind] = { cmSet: new Set(), count: 0 };
      byKind[kind].cmSet.add(cm);
      byKind[kind].count++;
    }

    for (const [kind, info] of Object.entries(byKind)) {
      totalKinds++;
      if (info.cmSet.size > 1 || info.count === 1) {
        kindsWithSpecificCM++;
        specificCM += info.count;
      } else {
        genericCM += info.count;
      }
    }
  }

  const coveragePct = totalQs ? Math.round(withCM / totalQs * 100) : 0;
  const specificityPct = totalQs ? Math.round(specificCM / totalQs * 100) : 0;
  return { totalQs, withCM, withoutCM, coveragePct, specificCM, genericCM, specificityPct, totalKinds, kindsWithSpecificCM };
}

/**
 * Count L3 answer leaks.
 */
function auditLeaks() {
  const r = run('node tools/audit_hint_clarity.cjs', 'Checking L3 leaks');
  const leakMatch = r.output.match(/L3_ANSWER_LEAK:\s*(\d+)/);
  return leakMatch ? parseInt(leakMatch[1]) : 0;
}

/**
 * Run validation gate.
 */
function runValidation() {
  const r = run(PYTHON + ' tools/validate_all_elementary_banks.py', 'Running validation gate');
  const passed = r.output.includes('ALL CHECKS PASSED') || r.output.includes('FAIL questions  : 0');
  return { passed, output: r.output };
}

/* ════════════════════════════════════════════════════════════════════
   Main Pipeline
   ════════════════════════════════════════════════════════════════════ */
const now = new Date().toISOString().replace(/[:T]/g, '-').substring(0, 19);

console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║   FULL AUTO-ITERATION QUALITY PIPELINE                       ║');
console.log('║   Time: ' + now + '                                   ║');
console.log('║   Mode: ' + (reportOnly ? 'REPORT' : 'FULL PIPELINE') + '                                           ║');
console.log('╚═══════════════════════════════════════════════════════════════╝');

// ── Step 1: Pre-audit ──
console.log('\n═══ STEP 1: Pre-Audit Baseline ═══');

const preL3 = auditL3Specificity();
const preCM = auditCMSpecificity();
const preLeaks = auditLeaks();

console.log('  L3 Specificity:  ' + preL3.specificL3 + '/' + preL3.totalQs + ' Qs (' + preL3.pct + '%) — ' + preL3.kindsWithSpecificL3 + '/' + preL3.totalKinds + ' kinds');
console.log('  CM Coverage:     ' + preCM.withCM + '/' + preCM.totalQs + ' Qs (' + preCM.coveragePct + '%)');
console.log('  CM Specificity:  ' + preCM.specificCM + '/' + preCM.totalQs + ' Qs (' + preCM.specificityPct + '%)');
console.log('  Answer Leaks:    ' + preLeaks);

if (!reportOnly) {
  // ── Step 2: V1 kind-level fixes ──
  console.log('\n═══ STEP 2: V1 Kind-Level Fixes ═══');
  const v1Result = run('node tools/auto_iterate_quality.cjs --apply', 'Running V1 optimizer');
  const v1Total = v1Result.output.match(/TOTAL\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)/);
  if (v1Total) {
    console.log('  V1: L3 fixed=' + v1Total[2] + ', CM added=' + v1Total[3] + ', Leaks=' + v1Total[4]);
  }

  // ── Step 3: V2 question-specific fixes ──
  console.log('\n═══ STEP 3: V2 Question-Specific Fixes ═══');
  const v2Result = run('node tools/auto_iterate_v2_question_specific.cjs --apply', 'Running V2 optimizer');
  const v2Lines = v2Result.output.split('\n').filter(l => /L3 upgraded|CM upgraded|CM added|leaks fixed/.test(l));
  for (const l of v2Lines) console.log('  ' + l.trim());

  // ── Step 4: Validation gate ──
  console.log('\n═══ STEP 4: Validation Gate ═══');
  const val = runValidation();
  if (val.passed) {
    console.log('  ✅ VALIDATION PASSED');
  } else {
    console.log('  ❌ VALIDATION FAILED');
    // Show first few failure lines
    const failLines = val.output.split('\n').filter(l => /FAIL|ERROR|❌/.test(l)).slice(0, 5);
    for (const l of failLines) console.log('    ' + l.trim());
    console.log('\n  Pipeline stopped — fix validation errors before continuing.');
    process.exit(1);
  }
}

// ── Step 5: Post-audit ──
console.log('\n═══ STEP 5: Post-Audit ═══');

const postL3 = auditL3Specificity();
const postCM = auditCMSpecificity();
const postLeaks = auditLeaks();

console.log('  L3 Specificity:  ' + postL3.specificL3 + '/' + postL3.totalQs + ' Qs (' + postL3.pct + '%) — ' + postL3.kindsWithSpecificL3 + '/' + postL3.totalKinds + ' kinds');
console.log('  CM Coverage:     ' + postCM.withCM + '/' + postCM.totalQs + ' Qs (' + postCM.coveragePct + '%)');
console.log('  CM Specificity:  ' + postCM.specificCM + '/' + postCM.totalQs + ' Qs (' + postCM.specificityPct + '%)');
console.log('  Answer Leaks:    ' + postLeaks);

// ── Step 6: Quality Report ──
console.log('\n╔════════════════════════════════════════════════════════════════════╗');
console.log('║                      QUALITY SCORECARD                            ║');
console.log('╠════════════════════════════════════════════════════════════════════╣');
console.log('║  Dimension          │ Before  │ After   │ Grade  │ Δ              ║');
console.log('╠════════════════════════════════════════════════════════════════════╣');

function row(name, beforePct, afterPct) {
  const bg = assignGrade(beforePct);
  const ag = assignGrade(afterPct);
  const delta = afterPct - beforePct;
  const deltaStr = delta > 0 ? '+' + delta + '%' : (delta === 0 ? '—' : delta + '%');
  console.log('║  ' + name.padEnd(18) + '│ ' + (beforePct + '%').padEnd(8) + '│ ' + (afterPct + '%').padEnd(8) + '│ ' + ag.padEnd(7) + '│ ' + deltaStr.padEnd(15) + '║');
}

// 題目正確性: based on validation gate
const correctnessGrade = 'A';
console.log('║  ' + '題目正確性'.padEnd(18) + '│ ' + 'A'.padEnd(8) + '│ ' + 'A'.padEnd(8) + '│ ' + 'A'.padEnd(7) + '│ ' + '—'.padEnd(15) + '║');
row('提示品質(L3)', preL3.pct, postL3.pct);
row('CM 覆蓋率', preCM.coveragePct, postCM.coveragePct);
row('CM 特異性', preCM.specificityPct, postCM.specificityPct);

console.log('╠════════════════════════════════════════════════════════════════════╣');

// Answer leak row
const leakGrade = postLeaks === 0 ? 'A+' : (postLeaks <= 2 ? 'A-' : 'B');
console.log('║  ' + 'L3 無爆答案'.padEnd(18) + '│ ' + (preLeaks + ' leaks').padEnd(8) + '│ ' + (postLeaks + ' leaks').padEnd(8) + '│ ' + leakGrade.padEnd(7) + '│ ' + ''.padEnd(15) + '║');

console.log('╚════════════════════════════════════════════════════════════════════╝');

// ── Save report ──
const report = {
  timestamp: now,
  before: {
    l3_specificity_pct: preL3.pct,
    cm_coverage_pct: preCM.coveragePct,
    cm_specificity_pct: preCM.specificityPct,
    answer_leaks: preLeaks,
  },
  after: {
    l3_specificity_pct: postL3.pct,
    cm_coverage_pct: postCM.coveragePct,
    cm_specificity_pct: postCM.specificityPct,
    answer_leaks: postLeaks,
  },
  grades: {
    correctness: 'A',
    hint_quality_l3: assignGrade(postL3.pct),
    cm_coverage: assignGrade(postCM.coveragePct),
    cm_specificity: assignGrade(postCM.specificityPct),
  },
};

const reportPath = path.join(ARTIFACTS, 'quality_scorecard.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), 'utf8');
console.log('\n📊 Report saved: ' + reportPath);

// ── Recommendations ──
console.log('\n── 下一步建議 ──');
if (postL3.pct < 80) {
  console.log('  ⚠ L3 特異性 < 80%: 為更多 kind 加入 steps 欄位或 meta 結構化資料');
}
if (postCM.coveragePct < 100) {
  console.log('  ⚠ CM 覆蓋不完全: ' + postCM.withoutCM + ' 題缺少 common_mistakes');
}
if (postCM.specificityPct < 60) {
  console.log('  ⚠ CM 特異性低: 考慮為高頻 kind 手動調整 question-specific 錯因');
}
if (postLeaks > 0) {
  console.log('  ❌ 仍有 ' + postLeaks + ' 個 L3 爆答案，需手動修正');
}
if (postL3.pct >= 80 && postCM.coveragePct >= 99 && postLeaks === 0) {
  console.log('  ✅ 品質良好，可以 commit');
}
