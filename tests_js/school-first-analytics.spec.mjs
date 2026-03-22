import test from 'node:test';
import assert from 'node:assert/strict';

import { aggregateComparableUnits, buildClassImprovementReport, compareStudentPerformance } from '../school_first/analytics.js';

const questions = [
  {
    question_id: 'q_pre_1',
    topic: 'fraction',
    subtopic: 'add_like',
    skill_tag: 'fraction_add',
    knowledge_point: 'kp_fraction_add',
    difficulty: 'easy',
    pattern_type: 'pre_variant',
    equivalent_group_id: 'eg_01'
  },
  {
    question_id: 'q_post_1',
    topic: 'fraction',
    subtopic: 'add_like',
    skill_tag: 'fraction_add',
    knowledge_point: 'kp_fraction_add',
    difficulty: 'easy',
    pattern_type: 'post_variant',
    equivalent_group_id: 'eg_01'
  }
];

test('analytics compare different questions with the same equivalent group', () => {
  const report = compareStudentPerformance({
    student: { student_id: 'student_001', class_id: 'class_1', display_name: 'Student 001' },
    questions,
    preAnswers: [{ assessment_id: 'asm_pre_1', student_id: 'student_001', class_id: 'class_1', question_id: 'q_pre_1', answer: '10', correctness: false, response_time: 30, hint_used: 2, attempt_count: 2, error_type: 'concept_confusion', timestamp: '2026-03-01T00:00:00Z' }],
    postAnswers: [{ assessment_id: 'asm_post_1', student_id: 'student_001', class_id: 'class_1', question_id: 'q_post_1', answer: '1', correctness: true, response_time: 20, hint_used: 0, attempt_count: 1, error_type: null, timestamp: '2026-03-08T00:00:00Z' }],
    interventions: [{ intervention_id: 'int_1' }]
  });

  assert.equal(report.comparable_units.length, 1);
  assert.equal(report.comparable_units[0].equivalent_group_id, 'eg_01');
  assert.equal(report.status, 'improved');
});

test('analytics classifies plateau and regression correctly', () => {
  const plateau = compareStudentPerformance({
    student: { student_id: 'student_002', class_id: 'class_1', display_name: 'Student 002' },
    questions,
    preAnswers: [{ assessment_id: 'asm_pre_2', student_id: 'student_002', class_id: 'class_1', question_id: 'q_pre_1', answer: '1', correctness: true, response_time: 20, hint_used: 0, attempt_count: 1, error_type: null, timestamp: '2026-03-01T00:00:00Z' }],
    postAnswers: [{ assessment_id: 'asm_post_2', student_id: 'student_002', class_id: 'class_1', question_id: 'q_post_1', answer: '1', correctness: true, response_time: 20, hint_used: 0, attempt_count: 1, error_type: null, timestamp: '2026-03-08T00:00:00Z' }]
  });
  const regression = compareStudentPerformance({
    student: { student_id: 'student_003', class_id: 'class_1', display_name: 'Student 003' },
    questions,
    preAnswers: [{ assessment_id: 'asm_pre_3', student_id: 'student_003', class_id: 'class_1', question_id: 'q_pre_1', answer: '1', correctness: true, response_time: 20, hint_used: 0, attempt_count: 1, error_type: null, timestamp: '2026-03-01T00:00:00Z' }],
    postAnswers: [{ assessment_id: 'asm_post_3', student_id: 'student_003', class_id: 'class_1', question_id: 'q_post_1', answer: '10', correctness: false, response_time: 35, hint_used: 2, attempt_count: 2, error_type: 'careless_error', timestamp: '2026-03-08T00:00:00Z' }]
  });

  assert.equal(plateau.status, 'plateau');
  assert.equal(regression.status, 'regressed');
});

test('analytics flags high risk and aggregates knowledge and skill improvement', () => {
  const units = [
    { knowledge_point: 'kp_fraction_add', skill_tag: 'fraction_add', pre_accuracy: 0.2, post_accuracy: 0.2, delta: 0 },
    { knowledge_point: 'kp_fraction_add', skill_tag: 'fraction_add', pre_accuracy: 0.1, post_accuracy: 0.2, delta: 0.1 }
  ];

  const aggregate = aggregateComparableUnits(units, 'knowledge_point');
  assert.equal(aggregate.length, 1);
  assert.equal(aggregate[0].knowledge_point, 'kp_fraction_add');
  assert.equal(aggregate[0].post_accuracy, 0.2);
});

test('class report identifies high-risk not-improved students', () => {
  const classRoom = { class_id: 'class_1', teacher_id: 'teacher_1' };
  const students = [
    { student_id: 'student_010', class_id: 'class_1', display_name: 'Student 010' },
    { student_id: 'student_011', class_id: 'class_1', display_name: 'Student 011' }
  ];
  const answerRecords = [
    { assessment_id: 'asm_pre_student_010', student_id: 'student_010', class_id: 'class_1', question_id: 'q_pre_1', answer: '10', correctness: false, response_time: 25, hint_used: 2, attempt_count: 2, error_type: 'concept_confusion', timestamp: '2026-03-01T00:00:00Z' },
    { assessment_id: 'asm_post_student_010', student_id: 'student_010', class_id: 'class_1', question_id: 'q_post_1', answer: '10', correctness: false, response_time: 30, hint_used: 2, attempt_count: 2, error_type: 'concept_confusion', timestamp: '2026-03-08T00:00:00Z' },
    { assessment_id: 'asm_pre_student_011', student_id: 'student_011', class_id: 'class_1', question_id: 'q_pre_1', answer: '10', correctness: false, response_time: 25, hint_used: 2, attempt_count: 2, error_type: 'concept_confusion', timestamp: '2026-03-01T00:00:00Z' },
    { assessment_id: 'asm_post_student_011', student_id: 'student_011', class_id: 'class_1', question_id: 'q_post_1', answer: '1', correctness: true, response_time: 18, hint_used: 0, attempt_count: 1, error_type: null, timestamp: '2026-03-08T00:00:00Z' }
  ];
  const report = buildClassImprovementReport({
    classRoom,
    students,
    questions,
    answerRecords,
    interventions: []
  });

  assert.ok(report.high_risk_students.includes('student_010'));
  assert.equal(report.status_counts.improved, 1);
});
