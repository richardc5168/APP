# Parent View MVP

Date: 2026-03-21
Status: Mock-data-first design

## Goal

Show one parent only their own child's learning status in family-readable language.

## Scope Rules

- parent sees one linked child at a time
- no class data
- no peer comparison
- no teacher-only operational data

## Required Sections

1. This session summary
   - latest assessment result
   - completion status
   - confidence and hint use

2. Already mastered
   - strongest `skill_tag`
   - strongest `knowledge_point`

3. Needs reinforcement
   - weakest `knowledge_point`
   - most common error types

4. Remedial recommendation
   - one next step now
   - one home support suggestion
   - one teacher follow-up note if available

5. Before/after trend
   - improved / plateau / regressed
   - short explanation of why
   - reliability warning if comparison is weak

6. Parent action packaging
   - what happened
   - why it matters
   - what parent can do this week

## Mock-First API Shape

```json
{
  "student": {"id": "student_001", "display_name": "Student 001"},
  "latest_assessment": {},
  "mastered": [],
  "needs_reinforcement": [],
  "recommendations": [],
  "before_after": {},
  "parent_actions": []
}
```

## UX Rules

1. language must be parent-readable, not teacher jargon
2. no raw SQL-ish IDs in UI
3. one clear next action above the fold

## Affected Files

- `docs/parent-report/index.html`
- school-first mock data module
- school-first analytics engine
