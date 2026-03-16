/*  parent_advice_engine.js  –  AIMathParentAdviceEngine
 *  Generates structured parent advice from report summary data.
 *  Browser IIFE – exposes window.AIMathParentAdviceEngine
 */
(function(){
  'use strict';

  /**
   * Build advice lines based on report summary, stuck level, and weaknesses.
   *
   * @param {object} opts
   * @param {number} opts.total       – total questions answered
   * @param {number} opts.accuracy    – accuracy percentage (0-100)
   * @param {number} opts.stuckLevel  – hint stuck level (0-3+)
   * @param {Array}  opts.weaknesses  – array of { t: topic } objects
   * @param {number} opts.avgMs       – average answer time in ms
   * @returns {Array<string>} ordered advice lines
   */
  function buildAdvice(opts) {
    var o = opts || {};
    var total = Number(o.total) || 0;
    var accuracy = Number(o.accuracy) || 0;
    var stuckLv = Number(o.stuckLevel) || 0;
    var weak = Array.isArray(o.weaknesses) ? o.weaknesses : [];
    var avgMs = Number(o.avgMs) || 0;

    var advices = [];

    // Volume check
    if (total < 5) {
      advices.push('目前作答數較少，建議每天至少做 5~10 題練習。');
    }

    // Accuracy-based
    if (accuracy < 60) {
      advices.push('正確率偏低，建議先做基礎題加強觀念，不要急著做進階題。');
    } else if (accuracy < 80) {
      advices.push('正確率還有進步空間，建議錯題先印出來重做一次，觀念才會穩固。');
    } else {
      advices.push('正確率不錯！可以嘗試更多進階活用題挑戰。');
    }

    // Stuck level
    if (stuckLv >= 3) {
      advices.push('孩子常需要完整步驟提示才能解題，建議把錯題的「完整步驟」抄一遍再做同型 2 題。');
    } else if (stuckLv >= 2) {
      advices.push('孩子常卡在列式階段，建議練習「把題意翻成算式」的步驟。');
    }

    // Weakness topics
    if (weak.length) {
      var topics = weak.map(function(w) { return w && w.t ? w.t : ''; }).filter(Boolean);
      if (topics.length) {
        advices.push('弱點主題：' + topics.join('、') + '。建議針對這些主題多練 5~10 題。');
      }
    }

    // Time check
    if (avgMs > 120000) {
      advices.push('平均耗時偏長，可能需要加強基本運算速度。');
    }

    return advices;
  }

  /**
   * Determine banner tone class based on advices.
   * @param {Array<string>} advices
   * @param {number} accuracy
   * @returns {string} CSS class: 'ok' | 'warn' | 'bad'
   */
  function adviceTone(advices, accuracy) {
    if (!advices || !advices.length) return 'muted';
    var acc = Number(accuracy) || 0;
    if (acc >= 80) return 'ok';
    if (acc >= 60) return 'warn';
    return 'bad';
  }

  window.AIMathParentAdviceEngine = {
    buildAdvice: buildAdvice,
    adviceTone: adviceTone
  };
})();
