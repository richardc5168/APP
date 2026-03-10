# Roadmap 12 Weeks

> Updated: 2026-03-10
> Principle: do not rebuild the product. Harden the existing loop until conversion and retention numbers are believable.

## Current Baseline

Already present in the repo today:

- landing, pricing, star-pack, parent-report, KPI surfaces
- front-end subscription state and gating
- local-first analytics and A/B testing
- learning analytics, remediation, and report assembly
- backend auth and subscription extension points
- reviewer automation for iterative quality work

That means the next 12 weeks are not “build MVP from zero”. They are “turn the existing MVP into a trustworthy validation machine”.

## Weeks 1-2

Focus: payment and subscription truth

- connect one real payment provider path from pricing to backend reconciliation
- map purchase completion into server-backed subscription state
- keep front-end state only as cache or UX convenience, not source of truth
- define failure and expiry behavior clearly

Success criteria:

- one real purchase path can move a user from free to paid
- paid state survives browser reset
- pricing, report gating, and pack gating reflect the same plan truth

## Weeks 3-4

Focus: analytics durability and normalized event shape

- export or persist core monetization events beyond browser-only storage
- standardize event fields across landing, pricing, report, packs, and practice
- verify funnel steps from landing to pricing to trial or checkout to paid
- add internal snapshots or exports that make KPI review reproducible

Success criteria:

- the same user journey produces consistent records across sessions
- topic, module, plan, and CTA source are queryable
- KPI review no longer depends on a single browser session

## Weeks 5-8

Focus: strengthen the paid value loop

- tighten star-pack merchandising around fractions, decimals, percentages, and life applications
- tighten parent-report to practice click-through
- extend upsell patterns beyond empire modules
- keep parent report centered on “weakest concepts, what to do next, did it improve”

Success criteria:

- parent report directly sends traffic into targeted practice
- star-pack pages present a clearer reason to pay
- premium differences are obvious without feeling arbitrary

## Weeks 9-12

Focus: safer scale and reviewer-driven optimization

- add the dedicated sub test agent for child-readable explanation quality and parent-report clarity
- run repeated reviewer batches against hints, solution logic, diagrams, and report copy
- expand A/B iteration only after payment and analytics truth are stable
- use data to simplify or remove weak CTA positions

Success criteria:

- explanation quality is guarded by automation, not ad hoc review
- parent-facing copy is measured and revised systematically
- A/B changes are evaluated on durable data, not browser-local noise

## Priority Summary

1. payment truth
2. subscription truth
3. analytics truth
4. pack and report conversion loop
5. dedicated sub test agent and reviewer optimization

## What Not To Do In This Window

- do not rebuild all content packs
- do not redesign the whole site visual system
- do not generalize to more grades before G5-G6 monetization is measured cleanly
- do not treat local-only KPI signals as final business truth
