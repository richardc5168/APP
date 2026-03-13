# Manual Sampling Policy

## Purpose

Define how the adaptive sampling system selects generated questions
for human review, balancing thoroughness with efficiency.

## Sampling Rates

| Risk Level | Default Rate | Rationale |
|-----------|-------------|-----------|
| **High** | 100% | Known-vulnerable or complex patterns always need review |
| **Medium** | 20% | Moderate complexity — spot-check sufficient |
| **Low** | 5% | Well-tested patterns — trust automation |

## Override Rules

Sampling rates are overridden in these scenarios:

1. **Topic with baseline failures**: If the previous baseline shows
   failures for a topic, ALL cases of that topic are sampled (100%)
   regardless of individual risk level.

2. **Generator recently changed**: When a generator file is modified
   (detected via `change_history.jsonl`), all cases for that topic
   should be sampled. *(Future enhancement)*

## Deterministic Sampling

Sampling decisions are **deterministic** — the same case always
produces the same sample/skip decision for a given rate. This is
achieved via MD5 hashing of the case ID, ensuring:

- Reproducibility across runs
- No random variance in CI/CD gates
- Consistent review queue

## Review Queue

Sampled cases are written to `logs/manual_review_queue.jsonl`.
Each entry contains:

```json
{
  "case_id": "fraction_word_problem[5]",
  "topic": "fraction_word_problem",
  "risk_score": 45,
  "risk_level": "medium",
  "risk_factors": ["medium_lcd=12", "needs_simplification"],
  "sample_reason": "sampled_at_20%_rate"
}
```

## Report

A summary report is auto-generated at:
`mathgen/reports/manual_sampling_report.md`

It includes:
- Total cases vs sampled count
- Risk distribution (low/medium/high)
- Per-topic breakdown
- High-risk case details
- Theoretical human-time savings

## Integration

The sampling system runs as Step 2c of the full cycle:
```
Step 2a: Run benchmarks
Step 2b: Coverage stats
Step 2c: Risk scoring & adaptive sampling  ← this
Step 3:  Regression check
```

## Files

| File | Purpose |
|------|---------|
| `mathgen/risk_scorer.py` | Dynamic risk scoring engine |
| `mathgen/manual_sampler.py` | Sampling logic + report generation |
| `mathgen/logs/manual_review_queue.jsonl` | Current review queue |
| `mathgen/reports/manual_sampling_report.md` | Latest sampling report |
| `mathgen/docs/risk_validation_policy.md` | Risk factor definitions |
