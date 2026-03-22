# School-First Proof Pack

Date: 2026-03-21
Status: Phase 0 and Phase 1 scaffold target

## Goal

Demonstrate the complete school-first story using mock data before wiring full backend data.

## Demo Story

1. Admin creates school with 2 teachers and 2 classes
2. Each teacher owns 58 students
3. Each student has one linked parent
4. Each student completes pre-test
5. Teacher receives intervention suggestions
6. Teacher applies intervention records
7. Each student completes post-test with different but equivalent questions
8. System generates:
   - parent report
   - teacher class report
   - individual before/after report
   - class before/after report
   - admin summary

## Required Mock Outputs

- `admin_summary`
- `teacher_class_reports[]`
- `parent_reports[]`
- `before_after_reports[]`

## Evidence Checklist

### Entitlement

- parent can only open own child proof
- teacher can only open own class proof
- admin can open all proofs

### Data model

- every answer references `question_id`
- every comparable question carries `equivalent_group_id`
- every before/after output lists reliability flags

### Analytics

- at least one improved student
- at least one plateau student
- at least one regressed student
- class summary by `skill_tag`
- class summary by `knowledge_point`

### Security

- no client-side PAT used in proof flow
- no export exceeds read scope

## Demo Dataset Shape

Use deterministic seed so the same proof can be regenerated.

Recommended output file:

- `artifacts/school_first_mock_data_sample.json`

## Validation Steps

1. generate mock data from seed
2. run school-first mock-data tests
3. run school-first analytics tests
4. confirm docs/dist mirror still matches

## Phase Status

- Phase 0: design docs present
- Phase 1: mock generator and analytics scaffold required
- Phase 2: UI proof pages pending
- Phase 3: real event integration pending
