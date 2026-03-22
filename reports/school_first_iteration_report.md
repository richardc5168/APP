# School-First Iteration Report

Date: 2026-03-21
Iteration: 64
Scope: Phase 0 contract plus implementation slice for scoped sessions, before/after APIs, and mock shells

## Executive Summary

This iteration converts the school-first direction from a single RBAC concept note into a repo-level implementation contract.

It adds the missing baseline documents for:

- RBAC test matrix
- school-first data model
- school-first event model
- security and secret audit
- teacher, parent, and admin MVP definitions
- proof-pack definition

The goal is to make the next implementation steps deterministic: mock data first, schema second, UI third, real integration last.

## Goal

Establish school-first design truth before expanding implementation.

## Out Of Scope

- payment feature expansion
- visual polish work
- broad refactor of legacy parent-report flow
- full teacher/admin UI implementation in this iteration

## Affected Files

- `docs/rbac_entitlement_school_first.md`
- `docs/rbac_test_cases.md`
- `docs/data_model_school_first.md`
- `docs/event_model_school_first.md`
- `docs/security_secret_audit.md`
- `docs/teacher_dashboard_mvp.md`
- `docs/parent_view_mvp.md`
- `docs/admin_dashboard_mvp.md`
- `docs/school_first_proof_pack.md`
- `dist_ai_math_web_pages/docs/(mirrors of the above)`

## Root Cause Summary

The repo had a good parent-report foundation and a newly added school-first backend scope layer, but still lacked a shared implementation contract for event truth, analytics comparability, security cleanup order, and mock-data-first UI development.

Without those artifacts, teacher-first features would likely drift into page-by-page improvisation.

## New Logic

1. School-first work is now anchored on explicit docs rather than only chat context.
2. RBAC is defined together with test cases, not as a prose-only policy.
3. Learning events are separated from the existing business funnel analytics schema.
4. Secret exposure review is documented with minimum fixes rather than deferred vaguely.
5. Teacher, parent, and admin MVPs are mock-data-first by design.

## Validation Plan

1. keep docs and dist mirrors identical
2. add runnable mock-data generator next
3. add analytics tests for equivalent-group comparison next
4. only after that build UI on top of mock data

## Validation Result

Pending implementation-stage validation in this iteration.

Document quality was derived from current repo code, tests, and security flows already inspected in Phase 0.

## Residual Risks

1. Parent report still depends on browser-held backend credentials after exchange.
2. Existing analytics schema is still business-oriented and could be misused unless the new event model is kept separate.
3. Older endpoints outside the new school-first surface remain household-centric.

## Next Step

Connect the teacher shell to the live teacher class overview and before/after endpoints, then narrow the remaining transient login grant so the browser no longer needs a raw API key even in memory during bootstrap.

---

## Iteration 64

Date: 2026-03-21
Scope: Before/after scope API, session-token narrowing, and teacher/parent/admin mock shells

### Executive Summary

This iteration converts the school-first contract into the first integrated implementation slice.

It narrows the browser-held paid-report credential from a raw API key to a scoped session token, adds dedicated before/after comparison endpoints for parent, teacher, and admin scope, fixes snapshot lineage storage so `before` and `after` do not overwrite each other, and lands mock-data-driven teacher, parent, and admin dashboard shells.

The result is a verifiable school-first path that is safer than the prior parent-report paid flow and ready for the next step of wiring teacher UI to live scoped APIs.

### Goal

Complete the approved school-first implementation slice without breaking the current parent-report pipeline.

### Out Of Scope

- real teacher/admin API wiring in the new shell pages
- full event-grain normalization for school-first analytics
- deployment and remote cross-validation
- a new login UI or full auth-system redesign

### Affected Files

- `server.py`
- `tests/test_report_snapshot_endpoints.py`
- `docs/shared/report_sync_adapter.js`
- `docs/parent-report/index.html`
- `docs/shared/school_first/mock_runtime.js`
- `docs/school-first-teacher/index.html`
- `docs/school-first-parent/index.html`
- `docs/school-first-admin/index.html`
- `dist_ai_math_web_pages/docs/(mirrors of the above)`
- `tests_js/parent-report-cloud-sync-security.spec.mjs`
- `tests_js/school-first-mock-data.spec.mjs`
- `tests_js/school-first-analytics.spec.mjs`

### Root Cause Summary

The repo already had school-first scope docs, backend foundation tables, and a mock-data analytics scaffold, but three gaps blocked a safe end-to-end slice:

1. The paid browser flow still stored a broad `api_key` in session state.
2. School-first snapshots carried lineage fields, but there was no dedicated before/after API surface for scoped comparison.
3. Snapshot storage keyed only on `(account_id, student_id)`, so an `after` write could overwrite `before` and destroy comparison lineage.

### New Logic

1. `POST /v1/app/auth/exchange` now returns a scoped `session_token` instead of a raw `api_key` for frontend storage.
2. Paid report endpoints now resolve auth through shared helpers and accept `X-Session-Token`.
3. Snapshot upsert semantics are phase-aware, so `before`, `after`, and `current` rows remain separate.
4. Parent, teacher, and admin now have dedicated before/after endpoints with scope enforcement.
5. School-first browser shells now exist for teacher, parent, and admin roles and consume deterministic mock runtime data.

### Validation Plan

1. Run targeted backend scope and snapshot tests.
2. Run JS security and school-first scaffold tests.
3. Run repo gates to confirm no docs/dist drift and no elementary-bank regression.

### Validation Result

Passed.

- `python -m pytest tests/test_report_snapshot_endpoints.py -q`
- `node --test tests_js/parent-report-cloud-sync-security.spec.mjs tests_js/school-first-mock-data.spec.mjs tests_js/school-first-analytics.spec.mjs`
- `python tools/validate_all_elementary_banks.py`
- `python scripts/verify_all.py`

The backend tests initially exposed a lineage bug where `before` was overwritten by `after`; this was fixed by including `report_phase` in the snapshot upsert identity and then re-running the tests to green.

### Residual Risks

1. Paid login still receives a raw `api_key` transiently in memory before bootstrap exchange; it is no longer stored in browser session state, but the handoff can be narrowed further.
2. Before/after comparisons are still snapshot-derived rather than event-grain normalized.
3. The three new school-first shells are mock-first and not yet wired to live scoped APIs.
4. Remote cross-validation has not been run because the change is not yet deployed.

### Next Step

Wire the teacher shell to the live teacher class overview and before/after endpoints, then replace the remaining transient login `api_key` handoff with a narrower login-grant token if the APP/browser boundary still needs hardening.

---

## Iteration 65

Date: 2026-03-21
Scope: Live teacher shell integration on existing scoped teacher APIs

### Executive Summary

This iteration turns the teacher shell from a mock-only proof surface into a bounded live integration.

The page can now authenticate a teacher account, call the existing scoped teacher endpoints for class overview and before/after reporting, and load teacher-student drill-down data through the dedicated teacher student before/after endpoint.

The change stays intentionally narrow: the raw teacher `api_key` is kept in memory only, mock mode remains the default and fallback, and no new backend auth model was introduced in the same pass.

### Goal

Connect the teacher shell to live scoped APIs without broadening authorization or destabilizing the parent-report paid flow.

### Out Of Scope

- teacher-specific browser grant redesign
- teacher class discovery endpoint
- live integration for parent and admin shells
- deployment and remote cross-validation

### Affected Files

- `docs/school-first-teacher/index.html`
- `dist_ai_math_web_pages/docs/school-first-teacher/index.html`
- `tests/test_report_snapshot_endpoints.py`
- `tests_js/school-first-teacher-live.spec.mjs`

### Root Cause Summary

The repo already had the correct backend surface for teacher scope, but the teacher shell still rendered only mock data. That left the UI contract and backend contract disconnected even though the safest minimum live surface already existed.

### New Logic

1. The teacher shell now supports a live connect flow using teacher username, password, backend base, and class id.
2. Live mode calls the existing teacher overview, teacher class before/after, and teacher student before/after endpoints.
3. The page keeps the raw login `api_key` in memory only and never stores it durably.
4. Mock mode remains the default render and immediate fallback if live auth or endpoint reads fail.

### Validation Plan

1. Run teacher/backend scope regressions.
2. Run school-first and source-level JS regressions.
3. Run repo gates to confirm docs/dist sync and no unrelated regression.

### Validation Result

Passed.

- `python -m pytest tests/test_report_snapshot_endpoints.py -q`
- `node --test tests_js/school-first-teacher-live.spec.mjs tests_js/school-first-mock-data.spec.mjs tests_js/school-first-analytics.spec.mjs tests_js/parent-report-cloud-sync-security.spec.mjs`
- `python tools/validate_all_elementary_banks.py`
- `python scripts/verify_all.py`
- `node tools/cross_validate_remote.cjs`

### Residual Risks

1. The teacher shell still holds a raw `api_key` transiently in memory after login because there is no narrower teacher session grant yet.
2. The live path still requires manual class id entry because linked-class discovery is not yet exposed.
3. Parent and admin shells are still mock-first by design.
4. Remote cross-validation has not been run because the changes are not deployed.

### Next Step

Add a narrower teacher session-grant and class-discovery path so the live teacher shell can authenticate and discover linked classes without holding a raw `api_key` in page memory or requiring manual class id entry.

---

## Iteration 66

Date: 2026-03-21
Scope: Teacher session grant and linked class discovery

### Executive Summary

This iteration removes the two temporary teacher-live integration compromises left by Iteration 65.

The teacher shell no longer keeps a raw `api_key` in page memory after live login, and it no longer depends on manual class id entry. Instead, the backend now issues a teacher-scoped browser session and exposes linked-class discovery, while the existing scoped teacher endpoints accept the narrower session token.

The change stays additive and narrow: mock mode remains intact, teacher authorization still resolves through the same class-link predicates, and the generic parent-report paid flow is not widened.

### Goal

Replace teacher-page raw API-key retention and manual class-id entry with a narrower teacher browser grant plus linked-class discovery.

### Out Of Scope

- parent live-shell integration
- admin live-shell integration
- generic auth-system redesign beyond the teacher browser path
- deployment and remote cross-validation

### Affected Files

- `server.py`
- `docs/school-first-teacher/index.html`
- `dist_ai_math_web_pages/docs/school-first-teacher/index.html`
- `tests/test_report_snapshot_endpoints.py`
- `tests_js/school-first-teacher-live.spec.mjs`
- `tests_js/parent-report-cloud-sync-security.spec.mjs`

### Root Cause Summary

Iteration 65 intentionally used the smallest live-teacher slice by wiring the teacher shell to existing scoped APIs with the raw login `api_key` kept only in page memory and a manual `class_id` field.

That was acceptable as a bounded first integration, but it still left two avoidable weaknesses:

1. the browser-held teacher page kept a broader credential than the page actually needed
2. the UI forced the operator to guess or manually type a linked class id even though class linkage already existed in backend tables

### New Logic

1. Added shared `_authenticate_app_user(...)` so login-rate-limit, lockout, subscription, and account loading logic are reused consistently.
2. Added `POST /v1/app/auth/teacher-session` to issue a scoped teacher browser session and return linked classes.
3. Added `GET /v1/app/teacher/classes` so the teacher shell can refresh linked-class discovery from the backend.
4. Updated teacher scoped overview and before/after endpoints to accept `X-Session-Token` through a teacher-portal auth resolver.
5. Reworked the teacher shell live mode to store `sessionToken`, populate a class selector from linked classes, switch classes without manual id entry, and keep mock fallback behavior.

### Validation Plan

1. Run targeted backend teacher/report regressions.
2. Run focused JS school-first and security regressions.
3. Run repository gates to confirm no bank, mirror, or smoke regression.

### Validation Result

Passed.

- `python -m pytest tests/test_report_snapshot_endpoints.py -q`
- `node --test tests_js/school-first-teacher-live.spec.mjs tests_js/school-first-mock-data.spec.mjs tests_js/school-first-analytics.spec.mjs tests_js/parent-report-cloud-sync-security.spec.mjs`
- `python tools/validate_all_elementary_banks.py`
- `python scripts/verify_all.py`

### Residual Risks

1. Parent and admin school-first shells are still mock-first by design and have not adopted live scoped sessions.
2. The generic login response still contains `api_key` for older bounded flows; only the teacher shell now avoids retaining it after connect.
3. The current remote cross-validation baseline passed, but that validator covers the published docs/bank surface and does not by itself prove every undeployed school-first teacher-shell change is live remotely.

### Next Step

Only when parent or admin live-shell work is ready, reuse the same scoped-browser-session pattern rather than widening raw credential handling again.
