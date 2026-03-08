/**
 * AIMathAnalytics — 最小可用的產品事件追蹤
 *
 * 儲存 key: aimath_analytics_v1
 * 所有事件記錄到 localStorage，可匯出 JSON。
 * 未來可替換為正式 analytics backend。
 */
(function(){
  'use strict';
  var KEY = 'aimath_analytics_v1';
  var MAX_EVENTS = 10000;
  var SESSION_KEY = 'aimath_session_id';

  function getSessionId(){
    var sid = sessionStorage.getItem(SESSION_KEY);
    if (!sid){
      sid = 's_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 6);
      sessionStorage.setItem(SESSION_KEY, sid);
    }
    return sid;
  }

  function getUserId(){
    if (window.AIMathStudentAuth && window.AIMathStudentAuth.isLoggedIn()){
      var s = window.AIMathStudentAuth.getCurrentStudent();
      return s ? s.name : 'anonymous';
    }
    return 'anonymous';
  }

  function getRole(){
    // 從當前頁面推斷角色
    if (location.pathname.indexOf('parent-report') >= 0) return 'parent';
    if (location.pathname.indexOf('coach') >= 0) return 'coach';
    return 'student';
  }

  function loadEvents(){
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return [];
      return JSON.parse(raw);
    } catch(e){ return []; }
  }

  function saveEvents(events){
    // 保留最新 MAX_EVENTS 筆
    if (events.length > MAX_EVENTS){
      events = events.slice(events.length - MAX_EVENTS);
    }
    try { localStorage.setItem(KEY, JSON.stringify(events)); } catch(e){}
  }

  /**
   * 記錄事件
   * @param {string} name - 事件名稱
   * @param {object} data - 附加資料
   */
  function track(name, data){
    var events = loadEvents();
    var event = {
      event: name,
      ts: Date.now(),
      user_id: getUserId(),
      role: getRole(),
      session_id: getSessionId(),
      page: location.pathname,
      data: data || {}
    };
    events.push(event);
    saveEvents(events);
  }

  /**
   * 查詢事件
   * @param {object} opts - { event, user_id, sinceMs, limit }
   */
  function query(opts){
    opts = opts || {};
    var events = loadEvents();
    if (opts.event){
      events = events.filter(function(e){ return e.event === opts.event; });
    }
    if (opts.user_id){
      events = events.filter(function(e){ return e.user_id === opts.user_id; });
    }
    if (opts.sinceMs){
      var cutoff = Date.now() - opts.sinceMs;
      events = events.filter(function(e){ return e.ts >= cutoff; });
    }
    if (opts.limit){
      events = events.slice(-opts.limit);
    }
    return events;
  }

  /**
   * 計算 KPI
   */
  function computeKPIs(){
    var all = loadEvents();
    var now = Date.now();
    var d7 = now - 7 * 86400000;
    var d30 = now - 30 * 86400000;
    var recent7 = all.filter(function(e){ return e.ts >= d7; });
    var recent30 = all.filter(function(e){ return e.ts >= d30; });

    function countEvent(list, name){
      return list.filter(function(e){ return e.event === name; }).length;
    }

    function uniqueUsers(list){
      var set = {};
      list.forEach(function(e){ if(e.user_id) set[e.user_id]=1; });
      return Object.keys(set).length;
    }

    return {
      total_events: all.length,
      events_7d: recent7.length,
      events_30d: recent30.length,
      unique_users_7d: uniqueUsers(recent7),
      unique_users_30d: uniqueUsers(recent30),
      trial_starts: countEvent(all, 'trial_start'),
      checkout_starts: countEvent(all, 'checkout_start'),
      checkout_success: countEvent(all, 'checkout_success'),
      pricing_views: countEvent(all, 'pricing_view'),
      upgrade_clicks: countEvent(all, 'upgrade_click'),
      question_submits_7d: countEvent(recent7, 'question_submit'),
      question_correct_7d: countEvent(recent7, 'question_correct'),
      hint_opens_7d: countEvent(recent7, 'hint_open'),
      report_views_7d: countEvent(recent7, 'weekly_report_view'),
      landing_views_7d: countEvent(recent7, 'landing_page_view')
    };
  }

  /**
   * 匯出全部事件 JSON
   */
  function exportJSON(){
    return JSON.stringify(loadEvents(), null, 2);
  }

  function clearAll(){
    try { localStorage.removeItem(KEY); } catch(e){}
  }

  window.AIMathAnalytics = {
    track: track,
    query: query,
    computeKPIs: computeKPIs,
    exportJSON: exportJSON,
    clearAll: clearAll,
    getSessionId: getSessionId
  };
})();
