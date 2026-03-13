# Mutation Testing Report

## Summary

| Metric | Value |
|--------|-------|
| Total mutations | 72 |
| Killed (detected) | 6 |
| Survived (undetected) | 66 |
| Mutation score | 8.3% |

## Per-Topic Results

| Topic | Killed | Survived | Total | Score |
|-------|--------|----------|-------|-------|
| average_word_problem | 0 | 15 | 15 | 0.0% |
| decimal_word_problem | 3 | 12 | 15 | 20.0% |
| fraction_word_problem | 0 | 24 | 24 | 0.0% |
| unit_conversion | 3 | 15 | 18 | 16.7% |

## Surviving Mutations (Weaknesses)

These mutations were NOT detected — potential blind spots:

| Case | Mutation | Notes |
|------|----------|-------|
| fraction_word_problem[0] | a_den_minus1 | survived |
| fraction_word_problem[0] | a_den_plus1 | survived |
| fraction_word_problem[0] | b_den_minus1 | survived |
| fraction_word_problem[0] | b_den_plus1 | survived |
| fraction_word_problem[0] | equal_fractions | survived |
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
| ... | +46 more | |
