(function(){
  'use strict';

  var DAY_MS = 86400000;

  /**
   * computeWeeklyTrend - Build 4-week accuracy trend from raw event entries.
   * @param {Array<{ts:*, ok:*}>} entries - raw teacher log entries
   * @param {number} [nowMs] - current timestamp (default: Date.now())
   * @returns {Array<{label:string, total:number, correct:number, rate:number}>}
   */
  function computeWeeklyTrend(entries, nowMs){
    var allEntries = Array.isArray(entries) ? entries : [];
    var now = Number(nowMs) || Date.now();
    var weeks = [];

    for (var w = 3; w >= 0; w--){
      var weekEnd = new Date(now);
      weekEnd.setDate(weekEnd.getDate() - w * 7);
      var weekStart = new Date(weekEnd);
      weekStart.setDate(weekStart.getDate() - 6);
      var wTotal = 0, wCorrect = 0;
      allEntries.forEach(function(e){
        if (!e || !e.ts) return;
        var d = new Date(e.ts);
        if (d >= weekStart && d <= weekEnd){
          wTotal++;
          if (e.ok) wCorrect++;
        }
      });
      var label = (weekStart.getMonth() + 1) + '/' + weekStart.getDate() + '~' +
                  (weekEnd.getMonth() + 1) + '/' + weekEnd.getDate();
      weeks.push({ label: label, total: wTotal, correct: wCorrect, rate: wTotal ? Math.round(wCorrect / wTotal * 100) : 0 });
    }

    return weeks;
  }

  /**
   * hasAnyData - Check if any week has data.
   * @param {Array<{total:number}>} weeks
   * @returns {boolean}
   */
  function hasAnyData(weeks){
    return Array.isArray(weeks) && weeks.some(function(w){ return w && w.total > 0; });
  }

  window.AIMathProgressTrendEngine = {
    computeWeeklyTrend: computeWeeklyTrend,
    hasAnyData: hasAnyData
  };
})();
