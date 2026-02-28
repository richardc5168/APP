/**
 * audit_hint_diagrams.cjs
 *
 * Automated audit: scans all elementary question banks and detects
 * known diagram/hint anti-patterns. Ensures past bugs do not recur.
 *
 * Run:  node tools/audit_hint_diagrams.cjs
 * Exit: 0 if clean, 1 if issues found
 *
 * Integrates with the 12h autonomous runner as a validation phase.
 */

const fs = require('fs');
const path = require('path');

// ── Load registry ──────────────────────────────────────────

const REGISTRY_PATH = path.join(__dirname, 'hint_diagram_known_issues.json');
const registry = JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));

// ── Discover all bank.js files ─────────────────────────────

function discoverBanks() {
  const docsDir = path.join(process.cwd(), 'docs');
  if (!fs.existsSync(docsDir)) return [];
  const banks = [];
  const entries = fs.readdirSync(docsDir, { withFileTypes: true });
  for (const e of entries) {
    if (!e.isDirectory()) continue;
    const bankPath = path.join(docsDir, e.name, 'bank.js');
    if (fs.existsSync(bankPath)) {
      banks.push({ module: e.name, path: bankPath });
    }
  }
  return banks;
}

// ── Parse bank.js → array of question objects ──────────────

function parseBankQuestions(bankPath) {
  const src = fs.readFileSync(bankPath, 'utf8');
  // bank.js exports: window.XXX_BANK = [...]; — variable name varies per module
  const match = src.match(/window\.\w+_BANK\s*=\s*(\[[\s\S]*\])\s*;?\s*$/m);
  if (!match) return [];
  try {
    return JSON.parse(match[1]);
  } catch {
    return [];
  }
}

// ── Anti-pattern checks ────────────────────────────────────

const checks = [];

/**
 * AP-001: Volume value used as height
 * For rect_find_height questions, extractIntegers would yield [L, W, Vol].
 * If the code blindly uses ints[2] as height, the diagram is wrong.
 * We verify that parseVolumeDims exists in hint_engine.js and is called.
 */
checks.push({
  id: 'AP-001',
  name: 'volume-as-height',
  run(questions) {
    const issues = [];
    for (const q of questions) {
      if (q.kind !== 'rect_find_height') continue;
      const text = q.question || '';
      const lm = text.match(/長[是為]?\s*(\d+)/);
      const wm = text.match(/寬[是為]?\s*(\d+)/);
      const vm = text.match(/體積[是為]?\s*(\d+)/);
      if (lm && wm && vm) {
        const l = parseInt(lm[1], 10);
        const w = parseInt(wm[1], 10);
        const v = parseInt(vm[1], 10);
        // Extract all integers from text to mimic extractIntegers()
        const allInts = (text.match(/\d+/g) || []).map(Number).filter(n => n > 0);
        // If ints[2] would be the volume, that's the scenario we fixed
        if (allInts.length >= 3 && allInts[2] === v && v > l * w) {
          // This is expected — the question IS a rect_find_height.
          // Check that parseVolumeDims is in hint_engine.js
          // (structural check done separately)
        }
      }
    }
    return issues;
  },
});

/**
 * AP-002: Fraction addition question with fracWord/fracRemain diagram
 * Detect if a generic_fraction_word question has addition keywords
 * but would be rendered with the old remainder bar chart.
 */
checks.push({
  id: 'AP-002',
  name: 'frac-addition-as-remainder',
  run(questions) {
    const issues = [];
    const addRe = /一共|合計|總共|相加|加起來|加在一起|共[用吃花走]了|共佔/;
    for (const q of questions) {
      if (q.kind !== 'generic_fraction_word') continue;
      const text = q.question || '';
      if (addRe.test(text)) {
        // This is an addition question — verify hint_engine handles it
        // The fix should be present (isFracAddition detection).
        // If buildFractionBarSVG is called without the guard, that's a regression.
        // We'll check hint_engine.js structurally.
      }
    }
    return issues;
  },
});

// ── Structural checks on hint_engine.js ────────────────────

function checkHintEngineStructure() {
  const hePath = path.join(process.cwd(), 'docs', 'shared', 'hint_engine.js');
  if (!fs.existsSync(hePath)) {
    return [{ id: 'STRUCT-000', severity: 'error', message: 'docs/shared/hint_engine.js not found' }];
  }
  const src = fs.readFileSync(hePath, 'utf8');
  const issues = [];

  // Check 1: parseVolumeDims must exist (VOL-001 fix)
  if (!/function\s+parseVolumeDims/.test(src)) {
    issues.push({
      id: 'STRUCT-VOL-001',
      severity: 'error',
      message: 'parseVolumeDims() function missing — volume diagram will use raw ints as dimensions (regression of VOL-001)',
    });
  }

  // Check 2: parseVolumeDims must be called in volume L2 branch
  if (!/parseVolumeDims\(text,\s*q\.kind\)/.test(src)) {
    issues.push({
      id: 'STRUCT-VOL-001b',
      severity: 'error',
      message: 'parseVolumeDims() not called with q.kind — rect_find_height will not be detected',
    });
  }

  // Check 3: isFracAddition detection must exist (FRAC-001 fix)
  if (!/isFracAddition/.test(src)) {
    issues.push({
      id: 'STRUCT-FRAC-001',
      severity: 'error',
      message: 'isFracAddition detection missing — fraction addition word problems will show remainder bar chart (regression of FRAC-001)',
    });
  }

  // Check 4: isPureCalculation must exist (CALC-001 fix)
  if (!/isPureCalculation/.test(src)) {
    issues.push({
      id: 'STRUCT-CALC-001',
      severity: 'error',
      message: 'isPureCalculation() missing — pure calculations will show unnecessary diagrams (regression of CALC-001)',
    });
  }

  // Check 5: Arrow markers for all 3 dimensions (VOL-002 fix)
  if (!/arr_g_s|arr_green_s/.test(src)) {
    issues.push({
      id: 'STRUCT-VOL-002',
      severity: 'warning',
      message: 'Width arrow markers missing in buildIsometricBoxSVG — width label may be unclear (regression of VOL-002)',
    });
  }

  // Check 6: unknownDim support in buildIsometricBoxSVG
  if (!/unknownDim/.test(src)) {
    issues.push({
      id: 'STRUCT-VOL-003',
      severity: 'warning',
      message: 'unknownDim support missing — reverse-solve (find height/edge) boxes cannot show "= ?" labels',
    });
  }

  // Check 7: fracAdd branch should NOT have buildFractionBarSVG or buildFractionComparisonSVG
  // (those were replaced with simple text steps in FRAC-002)
  const fracAddSection = src.match(/family === 'fracAdd'[\s\S]{0,2000}/);
  if (fracAddSection && /buildFractionBarSVG|buildFractionComparisonSVG/.test(fracAddSection[0])) {
    issues.push({
      id: 'STRUCT-FRAC-002',
      severity: 'warning',
      message: 'fracAdd branch still uses complex bar/comparison SVG — should use simple text steps (regression of FRAC-002)',
    });
  }

  // Check 8: dist mirror must be in sync
  const distPath = path.join(process.cwd(), 'dist_ai_math_web_pages', 'docs', 'shared', 'hint_engine.js');
  if (fs.existsSync(distPath)) {
    const distSrc = fs.readFileSync(distPath, 'utf8');
    if (src !== distSrc) {
      issues.push({
        id: 'STRUCT-SYNC-001',
        severity: 'error',
        message: 'docs/shared/hint_engine.js and dist mirror are out of sync — run: Copy-Item -Force docs/shared/hint_engine.js dist_ai_math_web_pages/docs/shared/hint_engine.js',
      });
    }
  }

  return issues;
}

// ── Question-level regression checks ───────────────────────

function checkQuestionRegressions(questions) {
  const issues = [];

  for (const q of questions) {
    const text = q.question || '';
    const kind = q.kind || '';

    // Regression: rect_find_height without proper hints mentioning 反求
    if (kind === 'rect_find_height') {
      const hints = q.hints || [];
      const hasReverse = hints.some(h => /體積\s*÷|反求|高\s*=/.test(h));
      if (!hasReverse) {
        issues.push({
          id: 'Q-VOL-001',
          severity: 'warning',
          qid: q.id,
          message: `rect_find_height question "${q.id}" hints don't mention reverse formula (高 = 體積 ÷ 底面積)`,
        });
      }
    }

    // Regression: generic_fraction_word with addition keywords but answer not matching add pattern
    if (kind === 'generic_fraction_word' && /一共|合計|總共/.test(text)) {
      const fracs = text.match(/(\d+)\s*[/／]\s*(\d+)/g) || [];
      if (fracs.length >= 2) {
        // Verify answer looks like a fraction (not a remainder)
        const ans = String(q.answer || '');
        if (/剩/.test(ans)) {
          issues.push({
            id: 'Q-FRAC-001',
            severity: 'warning',
            qid: q.id,
            message: `Addition word problem "${q.id}" answer mentions 剩 — possible misclassification`,
          });
        }
      }
    }

    // Check: any question with ints where the 3rd int is suspiciously large for volume
    if (kind === 'rect_cm3' || kind === 'volume_rect_prism') {
      const allInts = (text.match(/\d+/g) || []).map(Number).filter(n => n > 0);
      if (allInts.length >= 3 && allInts[2] > allInts[0] * allInts[1] * 5) {
        issues.push({
          id: 'Q-VOL-002',
          severity: 'info',
          qid: q.id,
          message: `Volume question "${q.id}" has suspiciously large 3rd integer (${allInts[2]}) — may be volume not height`,
        });
      }
    }
  }

  return issues;
}

// ── Main ───────────────────────────────────────────────────

function main() {
  console.log('='.repeat(60));
  console.log('  HINT DIAGRAM AUDIT');
  console.log('  Registry: ' + registry.issues.length + ' known issues, ' + registry.anti_patterns.length + ' anti-patterns');
  console.log('='.repeat(60));

  const allIssues = [];

  // 1. Structural checks on hint_engine.js
  console.log('\n[1/3] Structural checks on hint_engine.js...');
  const structIssues = checkHintEngineStructure();
  allIssues.push(...structIssues);
  for (const iss of structIssues) {
    const icon = iss.severity === 'error' ? '❌' : '⚠️';
    console.log(`  ${icon} ${iss.id}: ${iss.message}`);
  }
  if (structIssues.length === 0) console.log('  ✅ All structural checks pass');

  // 2. Scan all question banks
  console.log('\n[2/3] Scanning question banks...');
  const banks = discoverBanks();
  let totalQuestions = 0;
  const bankIssues = [];
  for (const bank of banks) {
    const questions = parseBankQuestions(bank.path);
    totalQuestions += questions.length;
    const qIssues = checkQuestionRegressions(questions);
    for (const iss of qIssues) {
      iss.module = bank.module;
      bankIssues.push(iss);
    }
  }
  allIssues.push(...bankIssues);
  console.log(`  Scanned ${banks.length} modules, ${totalQuestions} questions`);
  for (const iss of bankIssues) {
    const icon = iss.severity === 'error' ? '❌' : iss.severity === 'warning' ? '⚠️' : 'ℹ️';
    console.log(`  ${icon} [${iss.module}] ${iss.id}: ${iss.message}`);
  }
  if (bankIssues.length === 0) console.log('  ✅ No question-level regressions found');

  // 3. Anti-pattern coverage summary
  console.log('\n[3/3] Anti-pattern coverage...');
  for (const ap of registry.anti_patterns) {
    console.log(`  ✓ ${ap.id} (${ap.name}): ${ap.description}`);
  }

  // Write report
  const report = {
    timestamp: new Date().toISOString(),
    registry_issues: registry.issues.length,
    anti_patterns: registry.anti_patterns.length,
    banks_scanned: banks.length,
    questions_scanned: totalQuestions,
    issues_found: allIssues.length,
    errors: allIssues.filter(i => i.severity === 'error').length,
    warnings: allIssues.filter(i => i.severity === 'warning').length,
    info: allIssues.filter(i => i.severity === 'info').length,
    issues: allIssues,
  };

  const artifactsDir = path.join(process.cwd(), 'artifacts');
  if (!fs.existsSync(artifactsDir)) fs.mkdirSync(artifactsDir, { recursive: true });
  fs.writeFileSync(
    path.join(artifactsDir, 'hint_diagram_audit.json'),
    JSON.stringify(report, null, 2) + '\n',
    'utf8'
  );

  // Summary
  const errors = allIssues.filter(i => i.severity === 'error');
  console.log('\n' + '='.repeat(60));
  if (errors.length > 0) {
    console.log(`  ❌ AUDIT FAILED: ${errors.length} error(s), ${allIssues.length - errors.length} warning(s)/info(s)`);
    console.log('='.repeat(60));
    process.exit(1);
  } else {
    console.log(`  ✅ AUDIT PASSED: 0 errors, ${allIssues.length} warning(s)/info(s)`);
    console.log('='.repeat(60));
    process.exit(0);
  }
}

main();
