# Model Sandbox Policy

## Purpose

Define the strict guardrails for using language models to improve
question wording in the mathgen system. The sandbox ensures LLMs
can only modify cosmetic wording — never mathematical content.

## Allowed Operations

The model sandbox permits ONLY:

1. **Problem text rewriting** — improve clarity, grammar, or naturalness
2. **Name changes** — swap character names (小明→小華)
3. **Scenario changes** — swap context (餅乾→蘋果) if numbers stay same
4. **Grammar fixes** — correct Chinese grammar or punctuation

## Forbidden Operations

The model sandbox BLOCKS any change to:

| Field | Protected | Reason |
|-------|-----------|--------|
| `correct_answer` | ✅ | Mathematical correctness |
| `unit` | ✅ | Answer completeness |
| `parameters` | ✅ | Reproducibility |
| `steps` | ✅ | Solution integrity |
| `hint_ladder` | ✅ | Pedagogical design |
| Numbers in text | ✅ | Answer derivation |

## Safety Invariants

Six invariant checks run after every rewrite attempt:

1. **answer_preserved** — correct_answer unchanged
2. **unit_preserved** — unit unchanged
3. **parameters_preserved** — parameters dict unchanged
4. **steps_preserved** — steps list unchanged
5. **hints_preserved** — hint_ladder unchanged
6. **no_new_numbers** — no new numbers in problem_text

If ANY check fails, the rewrite is rejected and logged.

## Operating Modes

| Mode | Effect |
|------|--------|
| `dry_run=True` (default) | Shows proposed changes without applying |
| `dry_run=False` | Applies changes only if all safety checks pass |

## Logging

All sandbox attempts are logged to:
`mathgen/logs/model_sandbox_log.jsonl`

Each entry records:
- Original and proposed text
- Whether text changed
- All safety check results
- Whether change was applied

## Integration

```python
from mathgen.model_sandbox import ModelSandbox

# Create with a rewriter function
sandbox = ModelSandbox(
    rewriter=my_llm_rewrite_function,
    dry_run=True,  # default: show but don't apply
)

result = sandbox.polish_wording(question_dict)
if result['all_safe']:
    print(f"Safe to apply: {result['proposed_text']}")
```

## Files

| File | Purpose |
|------|---------|
| `mathgen/model_sandbox.py` | Sandbox implementation |
| `mathgen/logs/model_sandbox_log.jsonl` | Audit trail |
| `mathgen/docs/model_sandbox_policy.md` | This policy |
