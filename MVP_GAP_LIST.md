# MVP Gap List — Monetization Validation MVP

> Last updated: 2026-03-09
> Purpose: Track actionable gaps blocking paid conversion, retention, parent value, and future expansion.

## 1. 阻礙付費轉換的缺口

| # | Gap | Severity | Current State | Fix |
|---|-----|----------|---------------|-----|
| G1 | 3 of 5 A/B tests assigned but **not applied** | P0 | `pain_order`, `star_pack_position`, `free_limit` have no code reading them | Wire tests to actual UI/logic |
| G2 | Landing page CTAs fire no click events | P0 | Only `landing_page_view` tracked; hero/pricing/quest CTAs silent | Add `upgrade_click` / `cta_click` events |
| G3 | No real payment gateway | P1 | `mock_mode: true`; mock trial only | Phase 2: integrate ECPay/LinePay |
| G4 | Subscription in localStorage only | P1 | Can be cleared; no server verification | Phase 2: server-side with Gist or Supabase |
| G5 | `completion_upsell.js` only triggers on empire modules | P2 | Detects `#gBanner` + "結束" text | Extend to standard modules |

## 2. 阻礙留存追蹤的缺口

| # | Gap | Severity | Current State | Fix |
|---|-----|----------|---------------|-----|
| R1 | `return_next_day` / `return_next_week` events not implemented | P0 | Defined in schema but never fired | Implement in analytics.js on page load |
| R2 | `session_complete` event not implemented | P1 | Defined but never fired | Fire on session end / page unload |
| R3 | `question_start` event not implemented | P1 | Defined but never fired | Fire in showQuestion/renderQuestion flows |
| R4 | `retry_start` event not implemented | P2 | Defined but never fired | Fire on re-practice |
| R5 | All analytics in localStorage → data loss risk | P1 | No backend persistence | Phase 2: batch export to Gist/API |
| R6 | No `topic` / `grade` enrichment on events | P2 | Schema requires but most events omit | Add to attempt_telemetry bridge |

## 3. 阻礙家長感知價值的缺口

| # | Gap | Severity | Current State | Fix |
|---|-----|----------|---------------|-----|
| P1 | `weekly_report_view` event unclear if fired | P0 | Defined but not verified in parent-report code | Verify and add if missing |
| P2 | `remedial_recommendation_click` not fired | P1 | Parent report has deep links but no click tracking | Add onclick events to recommendation links |
| P3 | No "比上週進步/退步" trend card | P1 | PARENT_REPORT_V2_SPEC mentions it but not implemented | Add week-over-week comparison |
| P4 | Star pack page has no per-pack progress indicator | P1 | Students can't see completion % | Add progress bars from attempt data |
| P5 | GIST_PAT exposed in client-side JS | P0 | `ghp_U5Cs...` hardcoded in student_auth.js | Move to environment variable or backend proxy |

## 4. 阻礙擴充到更多年級的缺口

| # | Gap | Severity | Current State | Fix |
|---|-----|----------|---------------|-----|
| E1 | Grade detection hardcoded to G5 | P2 | No grade selector; all content assumes G5 | Add grade param to question schema |
| E2 | Module naming not grade-parameterized | P2 | `fraction-g5`, `volume-g5` etc. | Future: `fraction-g{N}` pattern |
| E3 | No question bank import pipeline for new grades | P2 | Each module has hand-built bank.js | Need template→bank generator |

## Priority Matrix

```
P0 (This sprint — immediate revenue/retention impact):
  ├─ G1: Wire 3 unwired A/B tests
  ├─ G2: Landing CTA click tracking
  ├─ R1: Retention events (return_next_day/week)
  ├─ P1: Verify weekly_report_view event
  └─ P5: GIST_PAT security fix

P1 (Next 2 weeks — measurability & value):
  ├─ G3: Real payment gateway prep
  ├─ R2: session_complete event
  ├─ R3: question_start event
  ├─ P2: Recommendation click tracking
  ├─ P3: Week-over-week trend card
  └─ P4: Star pack progress indicators

P2 (Month 2 — polish & expansion):
  ├─ G4: Server-side subscription
  ├─ G5: Extend completion_upsell to standard modules
  ├─ R4: retry_start event
  ├─ R5: Analytics backend persistence
  ├─ R6: topic/grade enrichment
  └─ E1-3: Multi-grade prep
```
