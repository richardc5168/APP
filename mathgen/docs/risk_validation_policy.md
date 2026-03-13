# Risk Validation Policy

## Purpose

Define how generated math questions are classified by risk level
and what validation gates apply to each level.

## Dynamic Risk Scoring

Every generated question receives a **risk score** (0–100) based on:

| Factor | Weight | Applies To |
|--------|--------|-----------|
| Topic base complexity | 5–15 | All |
| Large LCD (> 20) | +20 | Fraction |
| Medium LCD (11–20) | +10 | Fraction |
| Improper fraction | +10 | Fraction |
| Result = 0 | +15 | Fraction, Decimal |
| Needs simplification | +5 | Fraction |
| Deep decimals (≥ 2 places) | +15 | Decimal |
| Multiply operation | +10 | Decimal |
| Sub-1 operand in multiply | +10 | Decimal |
| Carry across tens | +10 | Decimal |
| Multiply-by-one leak risk | +20 | Decimal |
| Non-exact division | +15 | Average |
| Wording count mismatch | +15 | Average |
| Wide value range (> 500) | +10 | Average |
| Reverse direction (division) | +10 | Unit conversion |
| Decimal input | +10 | Unit conversion |
| Non-integer result | +10 | Unit conversion |
| Area conversion (10000×) | +10 | Unit conversion |
| Value=1 forward leak risk | +25 | Unit conversion |

## Risk Level Classification

| Score Range | Level | Description |
|-------------|-------|-------------|
| 0–29 | **Low** | Simple, well-tested patterns |
| 30–59 | **Medium** | Moderate complexity, some edge cases |
| 60+ | **High** | Complex or known-vulnerable patterns |

## Validation Gates by Level

| Gate | Low | Medium | High |
|------|-----|--------|------|
| Schema validation | ✅ | ✅ | ✅ |
| Hint ladder check | ✅ | ✅ | ✅ |
| Answer correctness | ✅ | ✅ | ✅ |
| Hint leak scan | ✅ | ✅ | ✅ |
| Adaptive sampling for review | 5% | 20% | 100% |

## Implementation

- Scorer: `mathgen/risk_scorer.py`
- Integration: `mathgen/scripts/run_full_cycle.py` (Step 2c)
- Reports: `mathgen/reports/manual_sampling_report.md`
