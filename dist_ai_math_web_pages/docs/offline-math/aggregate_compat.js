/*
  AIMathReportAggregate (compat)
  - Same API surface used by offline-math.
  - Avoids optional chaining and object spread which can blank-screen on older browsers.
*/

(function(){
  'use strict';

  function toInt(x, d){
    var n = Number(x);
    return Number.isFinite(n) ? Math.trunc(n) : (d || 0);
  }

  function safeArray(x){
    return Array.isArray(x) ? x : [];
  }

  function classifyQuadrant(evt){
    var isCorrect = !!(evt && evt.is_correct);
    var shownLevels = (evt && evt.hint && Array.isArray(evt.hint.shown_levels)) ? evt.hint.shown_levels : [];
    var shownSolution = !!(evt && evt.steps && evt.steps.shown_solution);
    var attemptsCount = Math.max(1, toInt(evt && evt.attempts_count, 1));

    var hasHint = shownLevels.length > 0 || shownSolution;

    // A: 無提示且一次就對
    if (isCorrect && !hasHint && attemptsCount === 1) return 'A';
    // B: 看提示後答對
    if (isCorrect && hasHint) return 'B';
    // C: 看提示仍答錯
    if (!isCorrect && hasHint) return 'C';
    // D: 無提示仍答錯
    return 'D';
  }

  function hintDepthKey(evt){
    var shownLevels = (evt && evt.hint && Array.isArray(evt.hint.shown_levels)) ? evt.hint.shown_levels : [];
    var shownSolution = !!(evt && evt.steps && evt.steps.shown_solution);
    if (shownSolution) return 'solution';

    var maxLv = 0;
    for (var i=0;i<shownLevels.length;i++){
      var v = Number(shownLevels[i]) || 0;
      if (v > maxLv) maxLv = v;
    }
    if (maxLv >= 3) return 'L3';
    if (maxLv >= 2) return 'L2';
    if (maxLv >= 1) return 'L1';
    return 'none';
  }

  function emptyGroupStats(unitId, kind){
    return {
      unit_id: String(unitId || ''),
      kind: String(kind || 'unknown'),
      n: 0,
      correct: 0,
      independent_correct: 0,
      hint_correct: 0,
      hint_wrong: 0,
      nohint_wrong: 0,
      A: 0,
      B: 0,
      C: 0,
      D: 0,
      hint_level_hist: { none: 0, L1: 0, L2: 0, L3: 0, solution: 0 },
      first_try_correct: 0,
      avg_time_ms: 0
    };
  }

  function emptyTopicStats(kind){
    return {
      kind: String(kind || 'unknown'),
      n: 0,
      correct: 0,
      independent_correct: 0,
      hint_correct: 0,
      hint_wrong: 0,
      nohint_wrong: 0,
      hint_level_hist: { none: 0, L1: 0, L2: 0, L3: 0, solution: 0 },
      first_try_correct: 0,
      avg_time_ms: 0
    };
  }

  function aggregateByUnitKind(attempts){
    var items = safeArray(attempts);
    var byKey = {};

    for (var i=0;i<items.length;i++){
      var evt = items[i];
      var unitId = String((evt && evt.unit_id) || '');
      var kind = String((evt && evt.kind) || 'unknown');
      var key = unitId + '::' + kind;
      var st = byKey[key];
      if (!st){
        st = byKey[key] = emptyGroupStats(unitId, kind);
      }

      var q = classifyQuadrant(evt);
      var dkey = hintDepthKey(evt);

      var duration = Math.max(0, toInt(evt && evt.ts_end, 0) - toInt(evt && evt.ts_start, 0));
      var isCorrect = !!(evt && evt.is_correct);
      var attemptsCount = Math.max(1, toInt(evt && evt.attempts_count, 1));

      st.n += 1;
      if (isCorrect) st.correct += 1;
      if (q === 'A') st.independent_correct += 1;
      if (q === 'B') st.hint_correct += 1;
      if (q === 'C') st.hint_wrong += 1;
      if (q === 'D') st.nohint_wrong += 1;
      st[q] = (st[q] || 0) + 1;
      st.hint_level_hist[dkey] = (st.hint_level_hist[dkey] || 0) + 1;
      if (isCorrect && attemptsCount === 1) st.first_try_correct += 1;
      st.avg_time_ms += duration;
    }

    var list = Object.values(byKey);
    for (var j=0;j<list.length;j++){
      if (list[j].n) list[j].avg_time_ms = Math.round(list[j].avg_time_ms / list[j].n);
    }

    list.sort(function(a,b){
      return (b.n - a.n) || String(a.unit_id).localeCompare(String(b.unit_id)) || String(a.kind).localeCompare(String(b.kind));
    });

    return list;
  }

  function weaknessScore(row){
    var n = Math.max(0, toInt(row && row.n, 0));
    if (!n) return 0;
    var cRate = (toInt(row && row.C, 0) / n);
    var dRate = (toInt(row && row.D, 0) / n);
    var bRate = (toInt(row && row.B, 0) / n);
    var base = 2.0 * cRate + 1.2 * dRate + 0.4 * bRate;
    var w = Math.log(1 + n);
    return base * w;
  }

  function pickTopWeaknesses(unitKindRows, topN){
    var rows = safeArray(unitKindRows);
    var n = Math.max(1, toInt(topN, 3));
    var scored = [];

    for (var i=0;i<rows.length;i++){
      var r = rows[i];
      var copy = Object.assign({}, r);
      copy.weakness_score = weaknessScore(r);
      if ((copy.n || 0) > 0) scored.push(copy);
    }

    scored.sort(function(a,b){
      return (b.weakness_score - a.weakness_score) || ((b.n || 0) - (a.n || 0));
    });

    return scored.slice(0, n);
  }

  function remedyLabel(row){
    var n = Math.max(0, toInt(row && row.n, 0));
    if (!n) return { level: 'warn', title: '資料不足' };
    var cRate = (toInt(row && row.C, 0) / n);
    var dRate = (toInt(row && row.D, 0) / n);
    if (cRate >= 0.30) return { level: 'bad', title: '優先補救：看提示仍常錯' };
    if (dRate >= 0.30) return { level: 'warn', title: '需補強：不看提示就容易錯' };
    return { level: 'ok', title: '可加強：穩定度再提升' };
  }

  function aggregate(attempts){
    var items = safeArray(attempts);

    var overall = emptyTopicStats('overall');
    var byKind = {};

    for (var i=0;i<items.length;i++){
      var evt = items[i];
      var kind = String((evt && evt.kind) || 'unknown');
      var st = byKind[kind];
      if (!st){
        st = byKind[kind] = emptyTopicStats(kind);
      }

      var q = classifyQuadrant(evt);
      var dkey = hintDepthKey(evt);

      var duration = Math.max(0, toInt(evt && evt.ts_end, 0) - toInt(evt && evt.ts_start, 0));
      var isCorrect = !!(evt && evt.is_correct);
      var attemptsCount = Math.max(1, toInt(evt && evt.attempts_count, 1));

      function bump(target){
        target.n += 1;
        if (isCorrect) target.correct += 1;
        if (q === 'A') target.independent_correct += 1;
        if (q === 'B') target.hint_correct += 1;
        if (q === 'C') target.hint_wrong += 1;
        if (q === 'D') target.nohint_wrong += 1;
        target.hint_level_hist[dkey] = (target.hint_level_hist[dkey] || 0) + 1;
        if (isCorrect && attemptsCount === 1) target.first_try_correct += 1;
        target.avg_time_ms += duration;
      }

      bump(st);
      bump(overall);
    }

    function finalize(st){
      if (!st.n) return st;
      st.avg_time_ms = Math.round(st.avg_time_ms / st.n);
      return st;
    }

    finalize(overall);
    Object.values(byKind).forEach(finalize);

    var kindList = Object.values(byKind).sort(function(a,b){ return b.n - a.n; });

    var kpi = {
      total: overall.n,
      accuracy: overall.n ? (overall.correct / overall.n) : 0,
      independent_rate: overall.n ? (overall.independent_correct / overall.n) : 0,
      hint_dependency: overall.n ? ((overall.hint_correct + overall.hint_wrong) / overall.n) : 0,
      avg_time_ms: overall.avg_time_ms
    };

    return {
      overall: overall,
      kpi: kpi,
      by_kind: kindList
    };
  }

  window.AIMathReportAggregate = {
    toInt: toInt,
    classifyQuadrant: classifyQuadrant,
    hintDepthKey: hintDepthKey,
    aggregate: aggregate,
    aggregateByUnitKind: aggregateByUnitKind,
    pickTopWeaknesses: pickTopWeaknesses,
    remedyLabel: remedyLabel
  };
})();
