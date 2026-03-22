# School-First Security and Secret Audit

Date: 2026-03-21
Status: Phase 0 audit baseline

## Goal

Identify client-side tokens, PAT-like flows, payment-related secret risks, and sync-secret exposure that conflict with a school-first production model.

## Scope Reviewed

- `docs/shared/report_sync_adapter.js`
- `docs/shared/student_auth.js`
- `docs/parent-report/index.html`
- `docs/shared/payment_provider.js`
- `server.py`
- `SECURITY_MANUAL_ACTIONS.md`

## Findings

| ID | Area | Finding | Risk | Minimum fix |
|---|---|---|---|---|
| SSA-001 | Parent report paid sync | Frontend stores `apiKey` and `studentId` in `sessionStorage` through `AIMathReportSyncAdapter.setCredentials()` | high | replace browser-held API key with backend session or opaque access token scoped to parent-report only |
| SSA-002 | Parent report exchange flow | `POST /v1/app/auth/exchange` returns long-lived `api_key` to browser body | high | move to httpOnly secure session cookie or short-lived scoped token for report-only APIs |
| SSA-003 | Parent report login UI | `docs/parent-report/index.html` still orchestrates login/bootstrap/exchange in browser | medium | keep browser as orchestrator only temporarily; next step is backend session endpoint for school-first views |
| SSA-004 | API base storage | `student_auth.js` stores backend base in localStorage and query param can override it | low | restrict allowed origins or pin environment-specific backend base in production |
| SSA-005 | Payment security posture | payment frontend appears mock-first and does not expose live Stripe secret in bundle, but local state still influences paid UI | medium | require server verification as final authority for school entitlement and paid features |
| SSA-006 | Git history secret | `SECURITY_MANUAL_ACTIONS.md` confirms exposed OpenAI key remains in git history | high | manual revoke plus git history cleanup remains required |
| SSA-007 | Embedded tooling UI | `server.py` serves HTML that writes `rag_api_key` to localStorage for a tool flow | medium | keep isolated from school-first pages and audit whether tool route is production-exposed |
| SSA-008 | Admin token model | `X-Admin-Token` env-based control exists server-side and is not exposed client-side | low | retain server-side only, add audit and rotation procedure |

## Exposed Surface Inventory

### Client-side tokens and credentials

1. `report_sync_adapter.js`
   - session-scoped `apiKey`
   - session-scoped `studentId`

2. `parent-report/index.html`
   - receives backend credentials after login/bootstrap/exchange
   - currently uses them for paid report sync calls

3. `student_auth.js`
   - stores backend base in localStorage
   - supports query-param override for backend target

### Payment and subscription exposure

1. `payment_provider.js`
   - frontend initiates payment-related flows
   - no direct Stripe secret found in reviewed source
   - paid UI state must still be treated as non-authoritative

2. `server.py`
   - server-side subscription verification and webhook are the correct authority path

### Sync-secret exposure

1. parent report sync currently depends on browser-held credential after exchange
2. this is better than URL-passed raw key, but still not ideal for school-first classroom deployment

## Risk Ranking

### High

- browser receives and stores backend `api_key`
- browser can call paid report endpoints directly with that key
- OpenAI key remains in git history

### Medium

- browser orchestrates full paid login/bootstrap/exchange path
- local payment/subscription UI can be tampered with unless server verification remains authoritative
- embedded tool flow writes API key to localStorage

### Low

- backend base origin selection via localStorage/query param
- env-based admin token model if kept server-side only

## Minimum Fix Plan

### Fix 1. Parent report sync

Move from browser-held API key to one of:

1. httpOnly secure session cookie bound to parent-report routes
2. short-lived opaque report session token with minimal scope

Do not widen to full account API access in browser.

### Fix 2. School-first teacher/admin routes

Require dedicated entitlement middleware/service so teacher pages never receive broad account credentials.

### Fix 3. Origin control

Pin allowed API base in production build or server config. Do not allow arbitrary query-param API target on school deployments.

### Fix 4. Manual secret cleanup

Complete the manual steps already documented for the leaked OpenAI key.

## Security Test Cases

1. No school-first production page stores long-lived account API key in localStorage or sessionStorage
2. Parent browser cannot call another child's report route
3. Teacher browser cannot call another class route
4. Admin-only routes reject missing or invalid admin token
5. Export endpoints do not exceed read scope
6. Production frontend bundle contains no PAT or payment secret

## Impacted Files

- `docs/shared/report_sync_adapter.js`
- `docs/shared/student_auth.js`
- `docs/parent-report/index.html`
- `docs/shared/payment_provider.js`
- `server.py`
