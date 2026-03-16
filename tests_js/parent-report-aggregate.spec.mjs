import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import fs from 'node:fs';
import path from 'node:path';

function loadScripts(files) {
  const sandbox = { window: {}, console, Date, Math, JSON, Number, Array, Object, String, isFinite, isNaN };
  sandbox.globalThis = sandbox.window;
  vm.createContext(sandbox);
  files.forEach((file) => {
    const code = fs.readFileSync(path.resolve(file), 'utf8');
    vm.runInContext(code, sandbox);
  });
  return sandbox.window;
}

const windowObj = loadScripts([
  'docs/shared/report/aggregate.js'
]);

const { AIMathReportAggregate } = windowObj;

test('classifyQuadrant returns A for correct, no hint, first try', () => {
  const evt = { is_correct: true, attempts_count: 1 };
  assert.equal(AIMathReportAggregate.classifyQuadrant(evt), 'A');
});

test('classifyQuadrant returns B for correct with hints', () => {
  const evt = { is_correct: true, attempts_count: 2, hint: { shown_levels: [1] } };
  assert.equal(AIMathReportAggregate.classifyQuadrant(evt), 'B');
});

test('classifyQuadrant returns C for wrong with hints', () => {
  const evt = { is_correct: false, hint: { shown_levels: [1, 2] } };
  assert.equal(AIMathReportAggregate.classifyQuadrant(evt), 'C');
});

test('classifyQuadrant returns D for wrong without hints', () => {
  const evt = { is_correct: false, attempts_count: 1 };
  assert.equal(AIMathReportAggregate.classifyQuadrant(evt), 'D');
});

test('computeStats produces valid quadrant rates', () => {
  const attempts = [
    { is_correct: true, attempts_count: 1, kind: 'frac', ts_start: 1000, ts_end: 2000 },
    { is_correct: true, hint: { shown_levels: [1] }, kind: 'frac', ts_start: 3000, ts_end: 4000 },
    { is_correct: false, hint: { shown_levels: [1, 2] }, kind: 'dec', ts_start: 5000, ts_end: 6000 },
    { is_correct: false, attempts_count: 1, kind: 'dec', ts_start: 7000, ts_end: 8000 },
  ];
  const stats = AIMathReportAggregate.computeStats(attempts);
  assert.equal(stats.quadrants.total, 4);
  assert.equal(stats.quadrants.A, 1);
  assert.equal(stats.quadrants.B, 1);
  assert.equal(stats.quadrants.C, 1);
  assert.equal(stats.quadrants.D, 1);
  assert.equal(stats.quadrants.rateA, 0.25);
});

test('recommend produces tips for low accuracy', () => {
  const attempts = Array.from({length: 20}, () => ({
    is_correct: false, attempts_count: 1, kind: 'frac', ts_start: 1000, ts_end: 2000
  }));
  const stats = AIMathReportAggregate.computeStats(attempts);
  const rec = AIMathReportAggregate.recommend(stats);
  assert.ok(rec.tips.length > 0, 'should have at least one tip');
  assert.ok(rec.tips.some(t => t.includes('正確率')), 'should mention accuracy');
});

test('pickTopWeaknesses selects highest weakness_score', () => {
  const rows = [
    { unit_id: 'u1', kind: 'frac', n: 10, C: 5, D: 2, B: 1, A: 2 },
    { unit_id: 'u2', kind: 'dec', n: 10, C: 1, D: 1, B: 1, A: 7 },
    { unit_id: 'u3', kind: 'avg', n: 10, C: 8, D: 1, B: 1, A: 0 },
  ];
  const top = AIMathReportAggregate.pickTopWeaknesses(rows, 2);
  assert.equal(top.length, 2);
  assert.equal(top[0].kind, 'avg', 'u3/avg should rank first (highest C rate)');
});

test('remedyLabel returns correct severity levels', () => {
  const bad = AIMathReportAggregate.remedyLabel({ n: 10, C: 4, D: 1, B: 1 });
  assert.equal(bad.level, 'bad');
  const warn = AIMathReportAggregate.remedyLabel({ n: 10, C: 1, D: 4, B: 1 });
  assert.equal(warn.level, 'warn');
  const ok = AIMathReportAggregate.remedyLabel({ n: 10, C: 1, D: 1, B: 1 });
  assert.equal(ok.level, 'ok');
});

test('parent-report loads aggregate.js script tag', () => {
  const src = fs.readFileSync(path.resolve('docs/parent-report/index.html'), 'utf8');
  assert.ok(src.includes('aggregate.js'), 'parent-report must load aggregate.js');
});

test('renderQuadrantAnalysis uses AIMathReportAggregate in parent-report', () => {
  const src = fs.readFileSync(path.resolve('docs/parent-report/index.html'), 'utf8');
  assert.ok(src.includes('renderQuadrantAnalysis'), 'parent-report must have renderQuadrantAnalysis');
  assert.ok(src.includes('AIMathReportAggregate.computeStats'), 'must call computeStats from aggregate');
  assert.ok(src.includes('AIMathReportAggregate.recommend'), 'must call recommend for tips');
});
