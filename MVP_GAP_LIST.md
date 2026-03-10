# MVP Gap List

> Updated: 2026-03-10
> Purpose: track the remaining gaps that block trustworthy monetization validation, not cosmetic completeness.

## P0

| ID | Gap | Why it matters | Current evidence | Recommended next step |
|---|---|---|---|---|
| P0-1 | No provider-backed web payment flow | Without real payment and webhook-style reconciliation, paid conversion data is not trustworthy | `docs/shared/subscription.js` still drives a mock-first status transition | Wire one real provider path and reconcile plan state on server |
| P0-2 | Parent-report cloud sync security risk | Client-visible secret patterns undermine trust and production readiness | Existing docs and implementation history still flag GIST_PAT exposure concern | Move secret use behind backend proxy or service endpoint |
| P0-3 | Public web subscription not fully server-backed | Local plan state is easy to reset or desync | Front-end plan state exists; `server.py` already has subscriptions table and auth hooks | Connect pricing and purchase completion to server-backed subscription records |
| P0-4 | No dedicated sub test agent for explanation quality | Monetization fails if hints are confusing, answer-leaky, or parent reports are hard to read | Generic reviewer automation exists, but no narrower agent loop for child readability and parent clarity | Add a focused reviewer agent around hint ladder, solution logic, wording, parent report clarity, and diagram checks |

## P1

| ID | Gap | Why it matters | Current evidence | Recommended next step |
|---|---|---|---|---|
| P1-1 | Analytics durability is still local-first | Cohort and funnel truth degrades when data is browser-local only | `docs/shared/analytics.js` stores locally and drives KPI page | Add batch export or server write path for core events |
| P1-2 | Event enrichment is not yet fully normalized across surfaces | Topic, module, plan, and CTA analysis becomes noisy | Analytics and attempt telemetry exist, but older docs still note enrichment inconsistency | Standardize `topic`, `grade`, `module_id`, `plan_type`, `plan_status`, `cta_source` |
| P1-3 | Completion upsell coverage is uneven | Some modules convert better because they have stronger end-state upsell than others | `docs/shared/completion_upsell.js` is strongest on empire-style experiences | Reuse the upsell pattern across standard practice surfaces |
| P1-4 | Parent report to practice return loop can be tighter | Retention improves when parents can act directly from the report | `docs/parent-report/index.html` and learning pipeline already support recommendation surfaces | Strengthen direct links into star packs and weak-skill practice modules |
| P1-5 | KPI page is useful but still pilot-grade | Internal visibility exists, but not yet durable for production decision-making | `docs/kpi/index.html` depends on local event pool | Add export, server aggregation, or snapshot sync |

## P2

| ID | Gap | Why it matters | Current evidence | Recommended next step |
|---|---|---|---|---|
| P2-1 | Retry-specific telemetry is incomplete | Useful for mastery loops, but not required for first paid validation | No dedicated retry event flow is consistently documented | Add when retry UX is standardized |
| P2-2 | Pack outcome summaries can be more explicit | Better merchandising and parent communication | Star-pack exists, but per-pack outcome summaries can go deeper | Add completion card and “what improved” summary |
| P2-3 | Grade expansion is not parameterized | Important later, but not before G5-G6 loop is proven | Current surfaces are strongly G5-centered | Generalize only after the paid loop stabilizes |
| P2-4 | Recommendation engine is still mostly deterministic rules | Good enough for MVP, but not differentiated long-term | `learning/remediation.py` is rule-driven | Keep rules for MVP; improve after data durability work |

## Recommended Order

1. `P0-1` real payment path
2. `P0-2` parent-report sync hardening
3. `P0-3` server-backed subscription state
4. `P0-4` dedicated sub test agent for quality
5. `P1-1` durable analytics export or ingestion
6. `P1-2` event field normalization
7. `P1-3` and `P1-4` conversion and retention optimization

## Definition Of “Closed”

A gap is only closed when:

1. the code path exists in the repo
2. its main event or state transition is measurable
3. the change survives the current validation workflow
4. the change improves the actual monetization loop rather than just the docs
