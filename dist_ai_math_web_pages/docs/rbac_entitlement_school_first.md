# School-First RBAC Entitlement Spec

Date: 2026-03-21
Status: Draft for MVP implementation
Scope: School-first AI learning diagnosis system where teacher class operations come first, parent child-only reports come second, and admin has global oversight.

## Goal

This document defines the minimum role-based access control and entitlement rules for a school-first version of ai-math-web.

The system focus is:

1. Teacher runs and improves their own class.
2. Parent only sees their own child.
3. Admin can monitor the whole system.
4. Data lineage is explicit enough that before/after impact can be audited.
5. The default rule is deny-by-default, not UI hiding.

## Confirmed Current Framework Reuse

This spec is designed to build on the current repo rather than replace it.

- Existing student/account/report surfaces already exist: `students`, `accounts`, `attempts`, `subscriptions`, `report_snapshots`, `parent_report_registry`.
- Existing deny-by-default backend patterns already exist in `server.py`: API-key auth, subscription checks, ownership checks, admin-token checks, bootstrap/exchange flow.
- Existing parent-report logic already assumes child-specific visibility, not class-wide visibility.
- Existing analytics/event model already distinguishes `role` and stores event-level timestamps.

The MVP should therefore add scoped links and authorization checks around the current data model instead of creating a separate reporting stack.

## Assumptions

1. A student belongs to one active class at a time in MVP.
2. A parent can be linked to one or more children, but only those children.
3. A teacher can be linked to one or more classes, but only those classes.
4. Admin is a platform operator role and can view all schools, all classes, and all students.
5. Before/after reports are report artifacts derived from the same underlying attempt and snapshot data, not a disconnected document system.

## A. Role Matrix

| Resource / View | parent | teacher | admin |
|---|---|---|---|
| Own child profile | Allow | Allow if student is in teacher's class | Allow |
| Own child attempt events | Allow | Allow if student is in teacher's class | Allow |
| Own child parent report | Allow | Allow if student is in teacher's class | Allow |
| Own child before report | Allow | Allow if student is in teacher's class | Allow |
| Own child after report | Allow | Allow if student is in teacher's class | Allow |
| Class roster | Deny | Allow for own class only | Allow |
| Class aggregate analytics | Deny | Allow for own class only | Allow |
| Student-to-student comparison inside same class | Deny by default in MVP | Allow for own class only | Allow |
| Other class roster | Deny | Deny | Allow |
| Other class analytics | Deny | Deny | Allow |
| School-wide analytics | Deny | Deny | Allow |
| Role assignments / entitlement config | Deny | Deny | Allow |
| Raw credentials / PIN / API keys / password hashes | Deny | Deny | Deny in normal UI/API; admin may manage resets but not view stored secrets |

Explicit answers required by product:

- Parent can see class data: No.
- Teacher can see other classes: No.
- Admin can see all data: Yes.

## B. Resource List

### 1. Identity and Roster Resources

| Resource | Description | Primary source |
|---|---|---|
| student_profile | Student name, grade, student_id, active class link | existing `students` + MVP class membership table |
| parent_child_link | Which parent is allowed to see which child | MVP parent-student link table |
| teacher_class_link | Which teacher is allowed to see which class | MVP teacher-class link table |
| class_roster | Class metadata and student membership list | MVP `classes` + class membership table |

### 2. Learning Evidence Resources

| Resource | Description | Primary source |
|---|---|---|
| attempt_event | Per-question attempt, correctness, hint usage, timestamp | existing `attempts` and local/cloud attempt telemetry model |
| practice_event | Parent-report practice loop events | existing `practice_events` / report snapshot append path |
| report_snapshot | Latest structured report payload per student | existing `report_snapshots` |
| parent_report_view | Child-facing or parent-facing rendered report assembled from snapshots and analytics | existing parent-report pipeline |

### 3. Outcome and Comparison Resources

| Resource | Description | Primary source |
|---|---|---|
| before_report | Baseline report before intervention period | MVP report snapshot with `report_phase = before` |
| after_report | Follow-up report after intervention period | MVP report snapshot with `report_phase = after` |
| class_analytics | Aggregated view across one class, no cross-class leakage | derived from student reports and attempt events |
| school_analytics | Global monitoring across all classes and schools | admin-only aggregate layer |

### 4. Governance Resources

| Resource | Description | Primary source |
|---|---|---|
| entitlement_policy | Role-to-resource rules and scope predicates | backend config / code |
| audit_log | Who accessed which scoped resource and when | backend audit trail |

## C. Action List

### Allowed actions by role

| Action | parent | teacher | admin |
|---|---|---|---|
| read | Own child only | Own class only | All scoped data |
| write | Limited child-specific actions only, such as parent notes if enabled later | Class-specific instructional actions only | Global admin actions |
| assign | Deny | Allow within own class only | Allow globally |
| export | Own child report only | Own class exports only | All exports |
| view analytics | Own child only | Own class only | All analytics |

### Action detail

| Resource | read | write | assign | export | view analytics |
|---|---|---|---|---|---|
| student_profile | parent: linked child, teacher: own class, admin: all | admin only for system-level edits in MVP | admin only | parent: child summary only, teacher: own class roster, admin: all | n/a |
| class_roster | teacher own class, admin all | teacher may update instructional state for own class if feature exists, admin all | teacher own class, admin all | teacher own class, admin all | n/a |
| report_snapshot | parent linked child, teacher own class students, admin all | system-generated only in MVP | n/a | parent own child, teacher own class, admin all | yes |
| before_report / after_report | parent linked child, teacher own class students, admin all | system-generated only in MVP | n/a | same as read | yes |
| class_analytics | no parent access | teacher own class only | n/a | teacher own class only | yes |
| school_analytics | deny | deny | allow | admin only | admin only |
| entitlement_policy | deny | deny | allow | admin only | admin only |

## D. Entitlement Rules

### Rule 1. Deny by default

If there is no explicit role-to-resource allow rule and no positive scope match, the request must return `403`.

UI hiding is not authorization.

### Rule 2. Parent scope = linked child only

Parent may read only resources where:

`student_id IN parent_child_links(parent_account_id)`

Parent cannot read:

- class roster
- class ranking
- class aggregate analytics
- any other student's attempts or reports
- teacher-only intervention notes

### Rule 3. Teacher scope = linked class only

Teacher may read only resources where:

- `class_id IN teacher_class_links(teacher_account_id)`
- and the student belongs to that class

Teacher cannot read:

- another teacher's class
- school-wide analytics
- unrelated parent account data
- payment/subscription secrets

### Rule 4. Admin scope = full platform visibility

Admin can view all schools, all classes, all linked students, all reports, all before/after outcomes, and all analytics.

Admin still should not receive raw stored secrets in normal read APIs. Admin operations should be capability-based, such as reset or assign, not secret disclosure.

### Rule 5. Before / after report visibility

Before/after reports are visible as follows:

- parent: only for own child
- teacher: only for students in own class
- admin: for all students/classes

No role should see before/after reports for a student outside their scope.

### Rule 6. Data traceability is mandatory

Every before/after or class-level outcome must be traceable to:

- source attempt events
- source report snapshot ids
- calculation window
- class membership at time of report
- role that accessed the report

Minimum lineage fields for every generated before/after artifact:

- `student_id`
- `class_id`
- `report_phase` (`before` / `after`)
- `window_start`
- `window_end`
- `snapshot_id` or source ids
- `generated_at`

### Rule 7. Aggregates must not leak underlying unauthorized rows

If a parent is not allowed to see class data, then parent must not see even anonymized class charts in MVP.

If a teacher is not allowed to see another class, cross-class comparisons must be excluded unless explicitly admin-only.

### Rule 8. Exports follow the same scope as read

Export never broadens access.

- parent export: own child only
- teacher export: own class only
- admin export: all

### Rule 9. Audit every privileged read

Teacher and admin access to class/student reports should emit an audit log with:

- actor_role
- actor_id
- resource_type
- resource_id
- class_id if applicable
- ts
- access_result (`allow` / `deny`)

## E. Risk Points

### 1. Scope drift between UI and backend

If the frontend filters by class but the backend endpoint still returns broader data, data leakage will occur.

Mitigation: enforce scope in backend query predicates first.

### 2. Parent accidentally seeing class data

This is a product trust break. Even aggregated class charts can reveal peer performance.

Mitigation: no class analytics in parent role for MVP.

### 3. Teacher cross-class leakage

Teachers often belong to one class context at a time in school-first MVP. Allowing other-class access increases privacy and governance risk.

Mitigation: teacher-class link table plus strict class predicate on every teacher analytics endpoint.

### 4. Before/after reports without stable membership snapshot

If a student changes class mid-period and the report does not store class-at-report-time, class improvement data becomes ambiguous.

Mitigation: record `class_id` and time window on every before/after report artifact.

### 5. Export leaks

CSV/PDF export paths often bypass normal UI scope checks.

Mitigation: exports must call the same authorization layer as read APIs.

### 6. Hidden secret leakage through admin tools

Admin may need reset and assignment powers, but should not read raw password hashes, PINs, or API keys through convenience endpoints.

Mitigation: capability APIs instead of raw secret retrieval.

### 7. Cached report reuse after role switch

If a teacher logs out and another user logs in on the same browser, cached class data could remain visible.

Mitigation: clear scoped caches on logout and include role + scope keys in cache namespace.

## F. MVP 最小實作建議

### 1. Do not build a new reporting stack

Reuse the current framework:

- `students`
- `attempts`
- `report_snapshots`
- existing parent-report render pipeline
- existing deny-by-default auth patterns in `server.py`

### 2. Add the smallest new relational links

Add four MVP tables:

1. `classes(id, school_id, class_name, grade, active, created_at)`
2. `class_students(class_id, student_id, active_from, active_to)`
3. `parent_student_links(parent_account_id, student_id, relation_type, active)`
4. `teacher_class_links(teacher_account_id, class_id, active)`

These are enough to express child-only parent scope and class-only teacher scope.

### 3. Add one authorization helper layer

Implement reusable helpers in backend style consistent with current code:

- `_verify_parent_child_scope(conn, parent_account_id, student_id)`
- `_verify_teacher_class_scope(conn, teacher_account_id, class_id)`
- `_resolve_student_class_scope(conn, actor_role, actor_id, student_id)`

Do not scatter ad hoc `SELECT` checks across handlers.

### 4. Model before/after as snapshot phases, not a separate document type

Extend `report_snapshots` or add a sibling table with:

- `student_id`
- `class_id`
- `report_phase`
- `window_start`
- `window_end`
- `payload_json`
- `generated_at`

This keeps lineage and avoids a second reporting system.

### 5. Start with these APIs only

MVP API surface should stay small:

1. `GET /v1/parent/children/{student_id}/report`
2. `GET /v1/teacher/classes/{class_id}/overview`
3. `GET /v1/teacher/classes/{class_id}/students/{student_id}/report`
4. `GET /v1/admin/schools/overview`
5. `GET /v1/admin/classes/{class_id}/overview`

Every endpoint must enforce role + scope in backend.

### 6. Ship reports in this order

1. child report
2. teacher class overview
3. teacher student drill-down
4. before/after comparison
5. admin global overview

This matches the product priority: teacher class operation first, parent extension second, admin monitoring third.

### 7. Verification gate for implementation

Before implementation is considered complete, verify:

1. parent cannot access class overview endpoint
2. teacher cannot access another class id
3. admin can access all classes
4. parent can access only linked child ids
5. teacher can access only students in linked classes
6. before/after reports preserve `class_id`, `window_start`, `window_end`
7. denied requests return explicit `403` with no silent fallback

### 8. Recommended implementation order

1. Land this entitlement spec
2. Add link tables and authorization helpers
3. Add backend tests for parent, teacher, admin scope
4. Expose minimal teacher overview endpoint
5. Add before/after snapshot phase support
6. Add UI only after scope tests are green

## Definition of Done for School-first RBAC MVP

The MVP is done only when:

1. Parent can only see own child.
2. Teacher can only see own class.
3. Admin can see all scoped resources.
4. Before/after reports are scope-checked and traceable.
5. Export follows the same scope as read.
6. Backend tests prove deny-by-default behavior.

## G. Entitlement Service / Middleware Design

The school-first MVP should not scatter scope checks across pages or ad hoc SQL.

Use a single backend entitlement layer with these responsibilities:

1. Build `EntitlementContext`
	- `actor_role`
	- `actor_account_id`
	- `class_ids`
	- `student_ids` only when explicitly linked
	- `subscription_state`

2. Expose reusable predicates
	- `canReadStudent(student_id)`
	- `canReadClass(class_id)`
	- `canReadBeforeAfter(student_id, class_id)`
	- `canExportStudent(student_id)`
	- `canExportClass(class_id)`

3. Enforce at server-side query boundary
	- apply scope before loading rows where possible
	- reject with `403` when scope does not match
	- never rely on frontend route guards as final authority

4. Emit audit trail for teacher/admin scoped reads

Current repo starting point:

- `server.py` already has reusable helpers for:
  - `_verify_parent_child_scope`
  - `_verify_teacher_class_scope`
  - `_verify_student_in_class`
  - `_resolve_student_class_scope`
- The next step is to wrap these helpers behind a small entitlement service so new APIs do not duplicate scope branching.

Recommended MVP structure:

- `entitlement_context_from_request(request)`
- `require_parent_child(ctx, student_id)`
- `require_teacher_class(ctx, class_id)`
- `require_before_after_scope(ctx, student_id, class_id)`
- `require_export_scope(ctx, scope_kind, scope_id)`

## H. Impacted APIs, Pages, and Data Access

### Existing backend APIs already impacted or likely impacted

- `POST /v1/app/report_snapshots`
- `POST /v1/app/report_snapshots/latest`
- `POST /v1/app/practice_events`
- `GET /v1/app/parent/children/{student_id}/report`
- `GET /v1/app/teacher/classes/{class_id}/overview`
- `GET /v1/app/teacher/classes/{class_id}/students/{student_id}/report`
- `GET /v1/app/admin/classes/{class_id}/overview`
- any future export endpoint for parent report, teacher class report, before/after report

### Existing pages likely impacted

- `docs/parent-report/index.html`
- any future teacher dashboard page
- any future admin dashboard page
- `docs/shared/report_sync_adapter.js`
- `docs/shared/student_auth.js`

### Existing data access patterns likely impacted

- direct account ownership checks on `students`
- `report_snapshots` lookup by `account_id + student_id`
- analytics assembled from `attempts` without class scoping
- export flows that currently assume one household scope

### MVP migration rule

Do not rewrite old APIs all at once.

Instead:

1. add new school-first scoped endpoints first
2. add RBAC tests for those endpoints
3. move new teacher/admin UI to those endpoints only
4. retire or wrap older household-only endpoints later when safe
