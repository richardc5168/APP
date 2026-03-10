# Monetization 8H Iteration Plan

> Updated: 2026-03-10
> Goal: use the existing architecture to run focused eight-hour improvement cycles without drifting into a rewrite.

## Core Rule

This repo already has enough surface area to validate monetization. The eight-hour loop should therefore optimize one bottleneck at a time and validate immediately.

Do not use this loop to:

- rebuild pricing from scratch
- redesign the entire site
- add broad new content families
- replace the learning pipeline

Use it to:

- tighten conversion flow
- harden measurement
- improve parent-facing clarity
- improve child-facing explanation quality

## The Four Workstreams

1. subscription and payment loop
2. retention and conversion measurement
3. star-pack merchandising for the four flagship topics
4. parent report plus remediation loop

## Dedicated Sub Test Agent Requirement

The repo already has reviewer automation, but monetization needs a narrower quality agent focused on:

- clear step-by-step solution logic
- wording children can understand
- no answer leakage in hint ladders
- parent report clarity and scannability
- appropriate diagram use where diagrams help, and no diagrams where they distract

This agent should run as a specialized check inside the iteration loop, not as a once-in-a-while manual review.

## One 8H Cycle

### Phase 1

Freeze scope for the cycle.

- choose exactly one target, such as pricing-to-paid dropoff or report-to-practice return rate
- list the files allowed in the cycle
- list the validation commands and success condition

### Phase 2

Inspect current data and reviewer output.

- review current funnel or quality signals
- review `artifacts/reviewer_batch` when explanation quality is in scope
- identify the smallest fixable bottleneck

### Phase 3

Implement one focused change.

Examples:

- normalize CTA source names across landing and pricing
- add missing plan fields to analytics payloads
- improve report CTA wording for top weak skills
- extend a premium upsell into a non-empire module
- tighten hint wording found by the dedicated sub test agent

### Phase 4

Run the local gate.

Use the repo workflow gate when relevant:

```powershell
python tools/validate_all_elementary_banks.py
python scripts/verify_all.py
```

If a pushed Pages change is involved, then also run:

```powershell
node tools/cross_validate_remote.cjs
```

### Phase 5

Record what changed and whether it helped.

- capture affected files
- capture measured before and after signals
- record follow-up work only if it is the next bottleneck

## Recommended 8H Order

### Hour 1

Audit and scope freeze.

Targets:

- confirm exact bottleneck
- confirm no unrelated files will be touched

### Hours 2-3

Subscription and pricing truth.

Targets:

- one naming scheme for plan state and CTA source
- consistent gating entry points

### Hours 4-5

Analytics truth.

Targets:

- normalized event fields
- durable export or ingestion path for core events

### Hours 6-7

Value-loop optimization.

Targets:

- better star-pack positioning
- stronger parent-report to practice loop
- stronger upsell in weaker practice surfaces

### Hour 8

Dedicated sub test agent pass and final validation.

Targets:

- re-check hint ladder safety
- re-check child readability
- re-check parent-report readability
- validate and summarize the delta

## Commit Discipline

Each cycle should produce small, defensible commits such as:

- `feat: normalize subscription analytics fields`
- `feat: strengthen parent report practice return loop`
- `fix: tighten star pack premium CTA wiring`
- `fix: improve hint ladder readability for reviewer gate`

## Success Standard

An eight-hour cycle is successful only if:

1. one monetization bottleneck was clearly chosen
2. one small set of files changed
3. the validation gate still passes
4. the resulting funnel, report loop, or explanation quality became easier to trust
