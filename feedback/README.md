# Parent Report Learning Signals

This directory feeds phase-2 nightly optimization.

Primary input file:
- `parent_report_signals.jsonl`

Each line should contain one report aggregate event, for example:

```json
{
  "topic": "購物折扣",
  "top_misconceptions": ["把折扣金額當成交價", "折數轉小數錯誤"],
  "recommended_next_practice": ["折扣", "小數乘法"],
  "hint_usage_rate": {"h1": 0.72, "h2": 0.58, "h3": 0.21, "h4": 0.08}
}
```

Nightly scripts:
- `tools/derive_report_signal_candidates.cjs`
- `tools/apply_report_signal_autotune.cjs`
