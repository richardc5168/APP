# School-First Data Model

Date: 2026-03-21
Status: Phase 0 baseline

## Goal

Define the smallest data model that can support:

- parent child-only views
- teacher class-only views
- admin global views
- pre-test -> intervention -> post-test evidence chain
- individual and class before/after reporting

## Truth Source Principle

All reports must trace back to event-level data, not only summary rows.

Current truth-source direction:

1. event rows (`answer_submitted`, `assessment_completed`, `intervention_created`)
2. derived analytics outputs
3. report snapshots for fast rendering and export

## Core Entities

### Identity and Scope

```text
AdminUser
TeacherProfile
ParentProfile
StudentProfile
ClassRoom
EntitlementContext
```

### Assessment and Learning Evidence

```text
Assessment
AssessmentSession
QuestionMeta
AnswerRecord
InterventionRecord
ParentReportSnapshot
TeacherClassReportSnapshot
BeforeAfterReportSnapshot
```

## Required Type Contracts

### Role

```text
Role = 'parent' | 'teacher' | 'admin'
```

### QuestionMeta

Must include:

- `question_id`
- `topic`
- `subtopic`
- `skill_tag`
- `knowledge_point`
- `difficulty`
- `pattern_type`
- `equivalent_group_id`

### AnswerRecord

Must include:

- `assessment_id`
- `student_id`
- `class_id`
- `answer`
- `correctness`
- `response_time`
- `hint_used`
- `attempt_count`
- `error_type`
- `timestamp`

## Relational Model

### Existing repo tables already useful

- `accounts`
- `students`
- `attempts`
- `report_snapshots`
- `subscriptions`

### Existing school-first additions already implemented

- `classes`
- `class_students`
- `parent_student_links`
- `teacher_class_links`

### Required logical additions for full MVP

These can start as view-model artifacts or new tables later depending on risk:

- `assessments`
- `assessment_sessions`
- `question_meta`
- `intervention_records`
- `before_after_report_snapshots`
- `audit_access_events`

## Minimal Table Sketch

```text
accounts
  id
  name
  api_key

students
  id
  account_id
  display_name
  grade

classes
  id
  school_id
  class_name
  grade

class_students
  id
  class_id
  student_id
  active_from
  active_to

parent_student_links
  id
  parent_account_id
  student_id
  relation_type
  active

teacher_class_links
  id
  teacher_account_id
  class_id
  active

attempts
  id
  account_id
  student_id
  topic
  difficulty
  question
  correct_answer
  user_answer
  is_correct
  time_spent_sec
  error_tag
  error_detail
  hint_level_used
  meta_json
  ts

report_snapshots
  id
  account_id
  student_id
  class_id
  report_phase
  window_start
  window_end
  report_payload_json
  source
  created_at
  updated_at
```

## Mapping To School-First Views

### Parent View

- student profile
- own child answer records
- own child interventions
- own child before/after summary
- parent-readable recommendations

### Teacher View

- class roster
- class pre-test summary
- class intervention log
- class post-test summary
- class before/after summary
- student drill-down for same class only

### Admin View

- school-level aggregate
- teacher/class roster overview
- report generation coverage
- cross-class before/after summary

## Report Snapshot Strategy

Snapshots are cache/render artifacts, not source truth.

Use them for:

- fast parent page rendering
- export payloads
- teacher dashboard summary cards
- admin status overview

Do not use snapshots as the only source for analytics. They must reference event windows and comparables.

## Migration Strategy

### Phase 1

- keep current `report_snapshots`
- add mock-only `Assessment`, `QuestionMeta`, and `InterventionRecord` shape in code
- use school-first mock generator to validate view requirements

### Phase 2+

- add durable `question_meta` and `assessment_sessions`
- normalize attempt metadata so equivalent-group analytics does not depend on parsing free-form text
- add access-audit records for teacher/admin reads

## Affected Files

- `server.py`
- `tests/test_report_snapshot_endpoints.py`
- future school-first mock and analytics modules
- parent/teacher/admin dashboard pages
