# School-First RBAC Test Cases

Date: 2026-03-21
Status: Phase 0 baseline

## Goal

These cases define the minimum regression suite for school-first authorization.

The backend is the source of truth. Frontend route guards and hidden buttons do not count as authorization.

## Actors

- `Parent A` linked to `Student A`
- `Parent B` linked to `Student B`
- `Teacher T1` linked to `Class 1`
- `Teacher T2` linked to `Class 2`
- `Admin X` global scope

## Test Matrix

| ID | Scenario | Expected result |
|---|---|---|
| RBAC-001 | Parent A reads Student A report | allow |
| RBAC-002 | Parent A reads Student B report | deny 403 |
| RBAC-003 | Parent A reads Class 1 analytics | deny 403 |
| RBAC-004 | Parent A exports Student A before/after | allow |
| RBAC-005 | Parent A exports Class 1 report | deny 403 |
| RBAC-006 | Teacher T1 reads Class 1 overview | allow |
| RBAC-007 | Teacher T1 reads Class 2 overview | deny 403 |
| RBAC-008 | Teacher T1 reads Student A in Class 1 | allow |
| RBAC-009 | Teacher T1 reads Student B in Class 2 | deny 403 |
| RBAC-010 | Teacher T1 reads school-wide analytics | deny 403 |
| RBAC-011 | Teacher T1 exports Class 1 before/after | allow |
| RBAC-012 | Teacher T1 exports Class 2 before/after | deny 403 |
| RBAC-013 | Admin X reads any class overview | allow |
| RBAC-014 | Admin X reads any student before/after | allow |
| RBAC-015 | Admin X reads global analytics | allow |
| RBAC-016 | Unknown actor without entitlement reads any scoped resource | deny 401 or 403 |

## Before/After Specific Cases

| ID | Scenario | Expected result |
|---|---|---|
| BA-001 | Parent A reads Student A before report | allow |
| BA-002 | Parent A reads Student A after report | allow |
| BA-003 | Parent A reads Student B before/after | deny 403 |
| BA-004 | Teacher T1 reads before/after for student in Class 1 | allow |
| BA-005 | Teacher T1 reads before/after for student outside Class 1 | deny 403 |
| BA-006 | Admin X reads any before/after report | allow |
| BA-007 | Parent sees class-level before/after chart | deny |
| BA-008 | Teacher sees cross-class before/after chart | deny |

## Data Model Cases

| ID | Scenario | Expected result |
|---|---|---|
| DM-001 | Schema stores parent-child link | supported |
| DM-002 | Schema stores teacher-class link | supported |
| DM-003 | Schema stores class membership over time | supported |
| DM-004 | Schema stores pre-test, intervention, post-test lineage | supported |
| DM-005 | Schema stores question metadata with `equivalent_group_id` | supported |
| DM-006 | Schema supports parent, teacher, admin views without duplicated source tables | supported |

## Analytics Correctness Cases

| ID | Scenario | Expected result |
|---|---|---|
| AN-001 | Pre/post questions differ but same `equivalent_group_id` | comparable |
| AN-002 | Same skill and knowledge point but difficulty differs by one band | comparable with reliability note |
| AN-003 | Improvement after intervention | `improved` |
| AN-004 | No change after intervention | `plateau` |
| AN-005 | Worse post-test outcome | `regressed` |
| AN-006 | Low baseline and no improvement | high-risk flagged |
| AN-007 | Knowledge-point aggregation across equivalent groups | correct aggregate |
| AN-008 | Skill-tag aggregation across multiple questions | correct aggregate |

## Security Cases

| ID | Scenario | Expected result |
|---|---|---|
| SEC-001 | No client-side PAT or sync secret in production page source | pass |
| SEC-002 | Parent report sync path uses server-side controlled route | pass |
| SEC-003 | Payment secrets not exposed in frontend bundle | pass |
| SEC-004 | Unauthorized actor cannot read another household or class | deny |
| SEC-005 | Export route does not exceed read scope | pass |
| SEC-006 | Audit log records teacher/admin scoped reads | pass |

## Affected API Surface To Cover

- `POST /v1/app/report_snapshots`
- `POST /v1/app/report_snapshots/latest`
- `POST /v1/app/practice_events`
- `GET /v1/app/parent/children/{student_id}/report`
- `GET /v1/app/teacher/classes/{class_id}/overview`
- `GET /v1/app/teacher/classes/{class_id}/students/{student_id}/report`
- `GET /v1/app/admin/classes/{class_id}/overview`
- future before/after comparison endpoint
- future export endpoints

## Minimum Automated Suite

1. HTTP-level entitlement tests for allow and deny cases
2. Schema tests confirming required entities and lineage fields exist
3. Analytics tests confirming equivalent-group comparison logic
4. Security tests confirming no unauthorized client-side secret path
