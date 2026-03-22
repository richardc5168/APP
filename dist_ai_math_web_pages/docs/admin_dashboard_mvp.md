# Admin Dashboard MVP

Date: 2026-03-21
Status: Mock-data-first design

## Goal

Give system owner or school admin a top-level view across teachers, classes, reports, and before/after outcomes.

## Scope Rules

- admin can read all classes, students, and reports
- admin should not receive raw secrets in normal UI

## Required Panels

1. Global student overview
   - total students
   - active classes
   - assessment completion coverage

2. Teacher/class overview
   - class count per teacher
   - class completion and risk status

3. Pre/post summary by class
   - pre-test average
   - post-test average
   - improvement delta

4. Parent report coverage
   - generated count
   - missing count

5. Global before/after summary
   - improved / plateau / regressed distribution
   - top improving and top struggling knowledge points

6. Teacher usage and class health
   - intervention counts
   - classes needing attention

## Mock-First API Shape

```json
{
  "summary": {},
  "teachers": [],
  "classes": [],
  "before_after_summary": {},
  "report_coverage": {}
}
```

## Acceptance Criteria

1. works fully on mock data
2. can filter by teacher and class
3. does not expose secrets or reset credentials in same surface

## Affected Files

- future admin dashboard page
- school-first mock data module
- school-first analytics engine
