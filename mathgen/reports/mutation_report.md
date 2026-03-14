# Mutation Testing Report

## Summary

| Metric | Value |
|--------|-------|
| Total mutations | 120 |
| Killed (detected) | 50 |
| Survived (undetected) | 70 |
| Mutation score | 41.7% |

## Per-Topic Results

| Topic | Killed | Survived | Total | Score |
|-------|--------|----------|-------|-------|
| average_word_problem | 18 | 7 | 25 | 72.0% |
| decimal_word_problem | 14 | 11 | 25 | 56.0% |
| fraction_word_problem | 4 | 36 | 40 | 10.0% |
| unit_conversion | 14 | 16 | 30 | 46.7% |

## Surviving Mutations (Weaknesses)

These mutations were NOT detected — potential blind spots:

| Case | Mutation | Notes |
|------|----------|-------|
| fraction_word_problem[0] | a_den_minus1 | survived |
| fraction_word_problem[0] | a_den_plus1 | survived |
| fraction_word_problem[0] | b_den_minus1 | survived |
| fraction_word_problem[0] | b_den_plus1 | survived |
| fraction_word_problem[0] | swap_ab | survived |
| fraction_word_problem[0] | large_denoms | survived |
| fraction_word_problem[0] | template_shift | survived |
| fraction_word_problem[1] | a_den_minus1 | survived |
| fraction_word_problem[1] | a_den_plus1 | survived |
| fraction_word_problem[1] | b_den_minus1 | survived |
| fraction_word_problem[1] | b_den_plus1 | survived |
| fraction_word_problem[1] | equal_fractions | survived |
| fraction_word_problem[1] | swap_ab | survived |
| fraction_word_problem[1] | large_denoms | survived |
| fraction_word_problem[1] | template_shift | survived |
| fraction_word_problem[2] | a_den_minus1 | survived |
| fraction_word_problem[2] | a_den_plus1 | survived |
| fraction_word_problem[2] | b_den_minus1 | survived |
| fraction_word_problem[2] | b_den_plus1 | survived |
| fraction_word_problem[2] | swap_ab | survived |
| ... | +50 more | |

## Gold Bank Promotion Candidates

Cases with high mutation kill rates (robust validations):

| Case | Kill Rate | Tested | Killed |
|------|-----------|--------|--------|
| average_word_problem[4] | 100% | 5 | 5 |
| average_word_problem[0] | 80% | 5 | 4 |
