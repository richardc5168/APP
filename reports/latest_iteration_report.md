# Latest Iteration Report

## Session Summary (Iterations 12–16)

### Iteration 12 (commit `43b4417ba`)
- Expanded TOPIC_LINK_MAP with 4 new entries: commercial-pack1-fraction-sprint, national-bank, midterm, grand-slam
- Fixed commercial-pack1-fraction-sprint falling through to generic fraction link
- +4 regression tests → **42 pass** (net 0 new, replaced prior placeholders)

### Iteration 13 (commit `bb02692bb`)
- Added collapsible section groups to parent report dashboard (17 cards → 7 `<details>` groups)
- Groups: 24h (collapsed), Quick Summary (open), 7-Day Overview (collapsed), Learning Analysis (collapsed), Advanced Analysis (collapsed), Wrong Q & Practice (open), Advice & Export (open)
- Added CSS for `rpt-group` with custom arrow marker, hover effects, count badge
- Pure HTML5, progressive enhancement — **42 pass**

### Iteration 14 (commit `fd7a41b1b`)
- **Critical fix**: WoW identity mismatch — parent-report was querying telemetry with `d.name` (display name "小明") instead of device UUID
- Added `getDeviceUid()` helper using `AIMathCoachLog.getOrCreateUserId()`
- Changed `getPrevWeekAttempts(d.name)` → `getPrevWeekAttempts(getDeviceUid())`
- +1 regression test → **43 pass**

### Iteration 15 (commit `8eb71d19c`)
- Added "📂 展開全部 / 📁 收合全部" expand/collapse-all toggle button
- Button between student info card and first group, toggles all `<details>` open/close
- **43 pass**

### Iteration 16 (commit pending)
- **Security fix**: `esc()` now escapes `"` → `&quot;` and `'` → `&#39;` (prevents HTML attribute injection)
- **UX consistency**: parent copy wrong count changed from 3 → 5 to match dashboard display
- **Stale state fix**: h24Modules element cleared when module list is empty
- +2 regression tests → **45 pass**

### Current Shared Engine Inventory (11 modules)
1. `weakness_engine.js` — `AIMathWeaknessEngine`
2. `recommendation_engine.js` — `AIMathRecommendationEngine` (TOPIC_LINK_MAP: 17 entries)
3. `report_data_builder.js` — `AIMathReportDataBuilder`
4. `practice_from_wrong_engine.js` — `AIMathPracticeFromWrongEngine`
5. `parent_copy_engine.js` — `AIMathParentCopyEngine` (now 5-wrong-item limit)
6. `wow_engine.js` — `AIMathWoWEngine`
7. `radar_engine.js` — `AIMathRadarEngine`
8. `progress_trend_engine.js` — `AIMathProgressTrendEngine`
9. `practice_summary_engine.js` — `AIMathPracticeSummaryEngine`
10. `parent_advice_engine.js` — `AIMathParentAdviceEngine`
11. `aggregate.js` — `AIMathReportAggregate` (not yet connected to parent-report)

### Test Coverage
- **45 regression tests** across 11 test files, all passing
- `validate_all_elementary_banks.py` → 7157 PASS, 0 FAIL
- `verify_all.py` → 4/4 OK (135 files mirrored)

### Remaining Inline Code in parent-report
- h24 KPI section (~20 lines) — view-only, renders pre-computed r.h24
- 7-day KPI grid (~10 lines) — view-only
- wrong list rendering + practice card (~200 lines) — interactive UI/DOM
- hint chart / stuck level (~20 lines) — view-only bar rendering
- All above are **view-layer code** — domain logic extraction is complete

### Residual Risks
1. `aggregate.js` not connected to parent-report (quadrant classification unused)
2. `CONCEPT_MAP` and `TOPIC_LINK_MAP` need updating when new modules are added
3. `esc()` quote escaping only fixed in parent-report — other HTML pages may have same vulnerability
4. Advice text is hardcoded Chinese — future i18n consideration
5. Expand/collapse state not persisted across page reloads

### Next Iteration Priorities
1. Audit `esc()`-equivalent functions in other HTML pages for same quote-escaping vulnerability
2. Connect `aggregate.js` quadrant analysis to parent-report
3. Standardize `getUid()` pattern across all question modules (optional chaining vs explicit check)
4. Consider visual regression tests for layout stability
5. Exam-sprint silent catch blocks — add console.error for localStorage failures
