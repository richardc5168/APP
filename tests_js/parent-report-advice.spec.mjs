import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function loadEngine() {
  const code = readFileSync(
    path.resolve(__dirname, '..', 'docs', 'shared', 'report', 'parent_advice_engine.js'),
    'utf-8'
  );
  const ctx = { window: {} };
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  return ctx.window.AIMathParentAdviceEngine;
}

describe('AIMathParentAdviceEngine', () => {
  const engine = loadEngine();

  it('low total triggers volume advice', () => {
    const advices = engine.buildAdvice({ total: 3, accuracy: 90, stuckLevel: 0, weaknesses: [], avgMs: 30000 });
    assert.ok(advices.some(a => a.includes('作答數較少')));
  });

  it('low accuracy triggers basic advice', () => {
    const advices = engine.buildAdvice({ total: 20, accuracy: 45, stuckLevel: 0, weaknesses: [], avgMs: 30000 });
    assert.ok(advices.some(a => a.includes('正確率偏低')));
    assert.ok(!advices.some(a => a.includes('正確率不錯')));
  });

  it('medium accuracy triggers improvement advice', () => {
    const advices = engine.buildAdvice({ total: 20, accuracy: 70, stuckLevel: 0, weaknesses: [], avgMs: 30000 });
    assert.ok(advices.some(a => a.includes('進步空間')));
  });

  it('high accuracy triggers positive advice', () => {
    const advices = engine.buildAdvice({ total: 20, accuracy: 90, stuckLevel: 0, weaknesses: [], avgMs: 30000 });
    assert.ok(advices.some(a => a.includes('正確率不錯')));
  });

  it('stuck level 3 triggers step-hint advice', () => {
    const advices = engine.buildAdvice({ total: 20, accuracy: 50, stuckLevel: 3, weaknesses: [], avgMs: 30000 });
    assert.ok(advices.some(a => a.includes('完整步驟')));
  });

  it('stuck level 2 triggers formulation advice', () => {
    const advices = engine.buildAdvice({ total: 20, accuracy: 50, stuckLevel: 2, weaknesses: [], avgMs: 30000 });
    assert.ok(advices.some(a => a.includes('列式')));
    // Should NOT include stuck level 3 advice
    assert.ok(!advices.some(a => a.includes('完整步驟')));
  });

  it('weaknesses included in advice', () => {
    const advices = engine.buildAdvice({
      total: 20, accuracy: 70, stuckLevel: 0,
      weaknesses: [{ t: '分數加法' }, { t: '小數乘法' }],
      avgMs: 30000
    });
    assert.ok(advices.some(a => a.includes('分數加法') && a.includes('小數乘法')));
  });

  it('slow time triggers speed advice', () => {
    const advices = engine.buildAdvice({ total: 20, accuracy: 70, stuckLevel: 0, weaknesses: [], avgMs: 150000 });
    assert.ok(advices.some(a => a.includes('耗時偏長')));
  });

  it('adviceTone returns ok/warn/bad based on accuracy', () => {
    assert.equal(engine.adviceTone(['a'], 90), 'ok');
    assert.equal(engine.adviceTone(['a'], 70), 'warn');
    assert.equal(engine.adviceTone(['a'], 40), 'bad');
    assert.equal(engine.adviceTone([], 90), 'muted');
  });
});
