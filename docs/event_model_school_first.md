# School-First Event Model

Date: 2026-03-21
Status: Phase 0 baseline

## Goal

Define the event truth-source model needed for school-first analytics.

This model is separate from the current business funnel analytics schema. It tracks learning evidence, not pricing conversion.

## Required Events

- `assessment_assigned`
- `assessment_started`
- `answer_submitted`
- `assessment_completed`
- `intervention_created`
- `parent_report_generated`
- `before_after_report_generated`

## Event Envelope

Every school-first event should use this minimum shape:

```json
{
  "event_type": "answer_submitted",
  "event_id": "evt_000001",
  "timestamp": "2026-03-21T10:00:00Z",
  "actor_role": "student",
  "actor_id": "student_001",
  "school_id": "school_demo",
  "class_id": "class_t1",
  "student_id": "student_001",
  "assessment_id": "asm_pre_001",
  "session_id": "sess_001",
  "payload": {}
}
```

## Event Payload Contracts

### assessment_assigned

Required payload:

- `assessment_id`
- `assessment_kind` (`pre_test` | `post_test` | `practice`)
- `assigned_by_role`
- `assigned_by_id`
- `question_ids`
- `target_skill_tags`
- `target_knowledge_points`

### assessment_started

Required payload:

- `assessment_id`
- `session_id`
- `started_at`

### answer_submitted

Required payload:

- `question_id`
- `equivalent_group_id`
- `skill_tag`
- `knowledge_point`
- `difficulty`
- `answer`
- `correctness`
- `response_time`
- `hint_used`
- `attempt_count`
- `error_type`

### assessment_completed

Required payload:

- `assessment_id`
- `session_id`
- `question_count`
- `correct_count`
- `accuracy`
- `completed_at`

### intervention_created

Required payload:

- `intervention_id`
- `intervention_type`
- `target_skill_tags`
- `target_knowledge_points`
- `reason`
- `assigned_by_role`
- `assigned_by_id`
- `student_ids`

### parent_report_generated

Required payload:

- `report_id`
- `student_id`
- `report_window_start`
- `report_window_end`
- `source_snapshot_ids`

### before_after_report_generated

Required payload:

- `report_id`
- `report_scope` (`student` | `class`)
- `student_id` or `class_id`
- `pre_assessment_ids`
- `post_assessment_ids`
- `intervention_ids`
- `comparison_keys`
- `reliability_flags`

## Data Flow

### Individual flow

1. `assessment_assigned` for pre-test
2. `assessment_started`
3. multiple `answer_submitted`
4. `assessment_completed`
5. `intervention_created`
6. `assessment_assigned` for post-test
7. `assessment_started`
8. multiple `answer_submitted`
9. `assessment_completed`
10. `before_after_report_generated`
11. `parent_report_generated`

### Class flow

1. teacher assigns pre-test to class
2. students complete sessions
3. teacher creates intervention plan
4. teacher assigns post-test
5. students complete post-test
6. class before/after report generated

## Comparison Logic

Pre/post comparisons may use different questions only when:

- same `skill_tag`
- same `knowledge_point`
- same or similar `difficulty`
- same `equivalent_group_id`

### Reliability flags

Mark result as lower-confidence when:

- missing pre or post evidence
- `equivalent_group_id` missing
- difficulty drift greater than one band
- too few comparable questions
- intervention window overlaps incomplete data

## Relation To Existing Repo Analytics

Current `ANALYTICS_SCHEMA.md` is for business funnel and UI telemetry.

It should not be treated as school-first learning truth source.

The school-first event model should eventually feed:

- teacher dashboard analytics
- parent report evidence
- before/after report generation
- admin school-wide monitoring

## Affected Files

- `server.py`
- future school-first event ingestion/service modules
- future analytics engine
- parent/teacher/admin report snapshot builders
