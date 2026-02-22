const fs = require('fs');
const path = require('path');

function readJson(p, fallback = null) {
  if (!fs.existsSync(p)) return fallback;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

const cwd = process.cwd();
const baselinePath = path.join(cwd, 'golden', 'improvement_baseline.json');
const hintPath = path.join(cwd, 'artifacts', 'hint_judge.json');
const scorecardPath = path.join(cwd, 'artifacts', 'scorecard.json');
const outPath = path.join(cwd, 'artifacts', 'improvement_check.json');

const modeArgIndex = process.argv.indexOf('--mode');
const mode = modeArgIndex >= 0 ? process.argv[modeArgIndex + 1] : 'enforce';

const hint = readJson(hintPath, { summary: { avg_score: 0, min_score: 0, count: 0 } });
const scorecard = readJson(scorecardPath, { golden: { correct_rate: 0 }, e2e: { flaky_rate: 1 } });
const baseline = readJson(baselinePath, {
  best_hint_avg: 0,
  best_hint_min: 0,
  best_golden_rate: 0,
  max_e2e_flaky_rate: 0.02,
  last_updated: null,
});

const current = {
  hint_avg: Number(hint.summary?.avg_score || 0),
  hint_min: Number(hint.summary?.min_score || 0),
  golden_rate: Number(scorecard.golden?.correct_rate || 0),
  e2e_flaky_rate: Number(scorecard.e2e?.flaky_rate ?? 1),
};

const nonRegression =
  current.hint_avg >= Number(baseline.best_hint_avg || 0) &&
  current.hint_min >= Number(baseline.best_hint_min || 0) &&
  current.golden_rate >= Number(baseline.best_golden_rate || 0) &&
  current.e2e_flaky_rate <= Number(baseline.max_e2e_flaky_rate || 0.02);

const improved =
  current.hint_avg > Number(baseline.best_hint_avg || 0) ||
  current.hint_min > Number(baseline.best_hint_min || 0) ||
  current.golden_rate > Number(baseline.best_golden_rate || 0);

const nextBaseline = {
  best_hint_avg: Math.max(Number(baseline.best_hint_avg || 0), current.hint_avg),
  best_hint_min: Math.max(Number(baseline.best_hint_min || 0), current.hint_min),
  best_golden_rate: Math.max(Number(baseline.best_golden_rate || 0), current.golden_rate),
  max_e2e_flaky_rate: Number(baseline.max_e2e_flaky_rate || 0.02),
  last_updated: new Date().toISOString(),
};

const report = {
  mode,
  non_regression: nonRegression,
  improved,
  baseline,
  current,
};

fs.mkdirSync(path.join(cwd, 'artifacts'), { recursive: true });
fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf8');

if (nonRegression) {
  fs.writeFileSync(baselinePath, JSON.stringify(nextBaseline, null, 2) + '\n', 'utf8');
}

if (mode === 'require-improvement' && !improved) {
  console.error('no measurable improvement over baseline');
  process.exit(1);
}

if (mode === 'enforce' && !nonRegression) {
  console.error('non-regression check failed');
  process.exit(1);
}

console.log(JSON.stringify({ nonRegression, improved }, null, 2));
