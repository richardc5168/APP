import test from 'node:test';
import assert from 'node:assert/strict';

import { buildProofPack } from '../school_first/analytics.js';
import { generateSchoolFirstMockData } from '../school_first/mock_data.js';

test('school-first mock data creates the required roster shape', () => {
  const dataset = generateSchoolFirstMockData({ seed: 20260321 });

  assert.equal(dataset.admins.length, 1);
  assert.equal(dataset.teachers.length, 2);
  assert.equal(dataset.classes.length, 2);
  assert.equal(dataset.students.length, 116);
  assert.equal(dataset.parents.length, 116);
  assert.equal(dataset.assessments.length, 232);
  assert.equal(dataset.intervention_records.length, 116);
});

test('school-first mock data uses different pre and post questions in the same equivalent group', () => {
  const dataset = generateSchoolFirstMockData({ seed: 20260321 });
  const firstStudent = dataset.students[0];
  const pre = dataset.answer_records.find((record) => record.student_id === firstStudent.student_id && record.assessment_id.startsWith('asm_pre_'));
  const post = dataset.answer_records.find((record) => record.student_id === firstStudent.student_id && record.assessment_id.startsWith('asm_post_'));
  const questions = new Map(dataset.questions.map((question) => [question.question_id, question]));

  assert.notEqual(pre.question_id, post.question_id);
  assert.equal(questions.get(pre.question_id).equivalent_group_id, questions.get(post.question_id).equivalent_group_id);
});

test('school-first proof pack covers admin, teacher, parent, and before-after outputs', () => {
  const dataset = generateSchoolFirstMockData({ seed: 20260321 });
  const proof = buildProofPack(dataset);

  assert.equal(proof.teacher_class_reports.length, 2);
  assert.equal(proof.parent_reports.length, 116);
  assert.ok(proof.before_after_reports.length > 116);
  assert.equal(proof.admin_summary.total_students, 116);
});
