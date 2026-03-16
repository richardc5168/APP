import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function loadEngine() {
  const code = readFileSync(
    path.resolve(__dirname, '..', 'docs', 'shared', 'report', 'progress_trend_engine.js'),
    'utf-8'
  );
  const ctx = { window: {} };
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return ctx.window.AIMathProgressTrendEngine;
}

describe('AIMathProgressTrendEngine', () => {
  const engine = loadEngine();

  it('computeWeeklyTrend returns 4 weeks', () => {
    const weeks = engine.computeWeeklyTrend([]);
    assert.equal(weeks.length, 4);
    weeks.forEach(w => {
      assert.equal(w.total, 0);
      assert.equal(w.correct, 0);
      assert.equal(w.rate, 0);
      assert.ok(w.label.includes('/'));
    });
  });

  it('correctly buckets entries into weeks', () => {
    const now = new Date('2025-07-15T12:00:00Z');
    const entries = [
      { ts: '2025-07-14T10:00:00Z', ok: true },
      { ts: '2025-07-14T11:00:00Z', ok: false },
      { ts: '2025-07-07T10:00:00Z', ok: true },
      { ts: '2025-07-07T11:00:00Z', ok: true },
      { ts: '2025-07-07T12:00:00Z', ok: true },
    ];
    const weeks = engine.computeWeeklyTrend(entries, now.getTime());
    // week 3 (most recent, ending ~Jul 15) should have the 2 entries from Jul 14
    const lastWeek = weeks[3];
    assert.equal(lastWeek.total, 2);
    assert.equal(lastWeek.correct, 1);
    assert.equal(lastWeek.rate, 50);
    // week 2 (ending ~Jul 8) should have the 3 entries from Jul 7
    const prevWeek = weeks[2];
    assert.equal(prevWeek.total, 3);
    assert.equal(prevWeek.correct, 3);
    assert.equal(prevWeek.rate, 100);
  });

  it('hasAnyData returns false for empty weeks', () => {
    const weeks = engine.computeWeeklyTrend([]);
    assert.equal(engine.hasAnyData(weeks), false);
  });

  it('hasAnyData returns true when at least one week has data', () => {
    const now = new Date('2025-07-15T12:00:00Z');
    const entries = [{ ts: '2025-07-14T10:00:00Z', ok: true }];
    const weeks = engine.computeWeeklyTrend(entries, now.getTime());
    assert.equal(engine.hasAnyData(weeks), true);
  });

  it('ignores entries with missing ts', () => {
    const now = new Date('2025-07-15T12:00:00Z');
    const entries = [
      { ok: true },
      { ts: null, ok: true },
      { ts: '2025-07-14T10:00:00Z', ok: true },
    ];
    const weeks = engine.computeWeeklyTrend(entries, now.getTime());
    const totalAll = weeks.reduce((s, w) => s + w.total, 0);
    assert.equal(totalAll, 1);
  });
});
