# Mutation Testing Report

## Summary

| Metric | Value |
|--------|-------|
| Total mutations | 120 |
| Killed (detected) | 57 |
| Survived (undetected) | 63 |
| Mutation score | 47.5% |

## Per-Topic Results

| Topic | Killed | Survived | Total | Score |
|-------|--------|----------|-------|-------|
| average_word_problem | 17 | 8 | 25 | 68.0% |
| decimal_word_problem | 14 | 11 | 25 | 56.0% |
| fraction_word_problem | 12 | 28 | 40 | 30.0% |
| unit_conversion | 14 | 16 | 30 | 46.7% |

## Surviving Mutations (Weaknesses)

These mutations were NOT detected — potential blind spots:

| Case | Mutation | Notes |
|------|----------|-------|
| fraction_word_problem[0] | a_den_plus1 | survived |
| fraction_word_problem[0] | b_den_minus1 | survived |
| fraction_word_problem[0] | b_den_plus1 | survived |
| fraction_word_problem[0] | swap_ab | survived |
| fraction_word_problem[0] | large_denoms | survived |
| fraction_word_problem[0] | template_shift | survived |
| fraction_word_problem[1] | a_den_plus1 | survived |
| fraction_word_problem[1] | b_den_minus1 | survived |
| fraction_word_problem[1] | b_den_plus1 | survived |
| fraction_word_problem[1] | equal_fractions | survived |
| fraction_word_problem[1] | swap_ab | survived |
| fraction_word_problem[1] | large_denoms | survived |
| fraction_word_problem[1] | template_shift | survived |
| fraction_word_problem[2] | a_den_plus1 | survived |
| fraction_word_problem[2] | b_den_minus1 | survived |
| fraction_word_problem[2] | b_den_plus1 | survived |
| fraction_word_problem[2] | swap_ab | survived |
| fraction_word_problem[2] | large_denoms | survived |
| fraction_word_problem[2] | template_shift | survived |
| fraction_word_problem[3] | a_den_plus1 | survived |
| ... | +43 more | |

## Gold Bank Promotion Candidates

Cases with high mutation kill rates (robust validations):

| Case | Kill Rate | Tested | Killed |
|------|-----------|--------|--------|
| average_word_problem[4] | 100% | 5 | 5 |
