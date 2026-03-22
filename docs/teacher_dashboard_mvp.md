# Teacher Dashboard MVP

Date: 2026-03-21
Status: Mock-data-first design

## Goal

Give one teacher a class-operating cockpit for about 58 students without exposing any other class.

## Scope Rules

- teacher sees own class only
- no cross-class comparison in MVP
- all charts and drill-downs derive from class-scoped mock or backend data

## Required Panels

1. Class overview
   - class name
   - grade
   - student count
   - pre-test completion
   - post-test completion

2. Student list
   - 58 students
   - status badges: high performer, medium, at-risk
   - latest intervention status

3. High-risk ranking
   - lowest post-test mastery
   - not-improved after intervention
   - high hint dependency

4. Skill and knowledge performance
   - by `skill_tag`
   - by `knowledge_point`

5. Pre-test summary
   - top weaknesses
   - completion coverage

6. Intervention recommendation panel
   - suggested regrouping
   - suggested reteach focus
   - suggested remedial pack

7. Post-test summary
   - post-test mastery distribution
   - improved vs plateau vs regressed counts

8. Before/after chart
   - class-level improvement by skill and knowledge point
   - reliability notes when comparability is weak

9. Student drill-down
   - one student at a time
   - pre/post comparison
   - error types
   - recommended next action

## Mock-First API Shape

```json
{
  "class": {"id": "class_t1", "class_name": "G5 A", "teacher_id": "teacher_1"},
  "overview": {},
  "students": [],
  "skill_summary": [],
  "knowledge_summary": [],
  "before_after": {},
  "high_risk_students": []
}
```

## Acceptance Criteria

1. loads with mock data only
2. teacher cannot navigate to another class dataset
3. drill-down remains within same class
4. before/after uses equivalent-group comparison, not exact same question requirement

## Affected Files

- future teacher dashboard page
- school-first mock data module
- school-first analytics engine
