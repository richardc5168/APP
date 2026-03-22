const ERROR_TYPES = [
  'concept_confusion',
  'careless_error',
  'place_value_error',
  'operation_misread',
  'multi_step_breakdown'
];

const COMPARABLE_GROUPS = [
  ['fraction', 'add_like', 'fraction_add', 'kp_fraction_add', 'easy'],
  ['fraction', 'sub_like', 'fraction_sub', 'kp_fraction_sub', 'easy'],
  ['decimal', 'place_value', 'decimal_place_value', 'kp_decimal_place_value', 'medium'],
  ['decimal', 'add_sub', 'decimal_operations', 'kp_decimal_add_sub', 'medium'],
  ['ratio', 'unit_rate', 'ratio_reasoning', 'kp_unit_rate', 'medium'],
  ['measurement', 'unit_convert', 'unit_conversion', 'kp_unit_conversion', 'medium'],
  ['geometry', 'area_rect', 'area_reasoning', 'kp_area_rectangles', 'medium'],
  ['word_problem', 'two_step', 'multi_step_reasoning', 'kp_two_step_reasoning', 'hard']
];

function createRng(seed) {
  let state = Math.abs(Number(seed) || 1) % 2147483647;
  if (state === 0) state = 1;
  return function next() {
    state = (state * 48271) % 2147483647;
    return (state - 1) / 2147483646;
  };
}

function pickOne(items, rng) {
  return items[Math.floor(rng() * items.length)];
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function isoFrom(baseMs, offsetMinutes) {
  return new Date(baseMs + offsetMinutes * 60000).toISOString();
}

function buildQuestionMeta() {
  const questions = [];
  for (let index = 0; index < COMPARABLE_GROUPS.length; index += 1) {
    const [topic, subtopic, skillTag, knowledgePoint, difficulty] = COMPARABLE_GROUPS[index];
    const equivalentGroupId = `eg_${String(index + 1).padStart(2, '0')}`;
    questions.push({
      question_id: `q_pre_${equivalentGroupId}`,
      topic,
      subtopic,
      skill_tag: skillTag,
      knowledge_point: knowledgePoint,
      difficulty,
      pattern_type: 'pre_variant',
      equivalent_group_id: equivalentGroupId
    });
    questions.push({
      question_id: `q_post_${equivalentGroupId}`,
      topic,
      subtopic,
      skill_tag: skillTag,
      knowledge_point: knowledgePoint,
      difficulty,
      pattern_type: 'post_variant',
      equivalent_group_id: equivalentGroupId
    });
  }
  return questions;
}

function performanceBand(studentIndex) {
  const mod = studentIndex % 10;
  if (mod < 2) return 'high';
  if (mod < 7) return 'medium';
  return 'at_risk';
}

function outcomeBand(studentIndex) {
  const mod = studentIndex % 3;
  if (mod === 0) return 'improved';
  if (mod === 1) return 'plateau';
  return 'regressed';
}

function probabilityByBand(band) {
  if (band === 'high') return 0.82;
  if (band === 'medium') return 0.58;
  return 0.32;
}

function deltaByOutcome(outcome) {
  if (outcome === 'improved') return 0.22;
  if (outcome === 'plateau') return 0.03;
  return -0.08;
}

function answerText(correctness, rng) {
  return correctness ? String(1 + Math.floor(rng() * 9)) : String(10 + Math.floor(rng() * 9));
}

function buildAnswerRecord({
  assessmentId,
  studentId,
  classId,
  questionId,
  correctness,
  rng,
  timestamp
}) {
  const hintUsed = correctness ? (rng() < 0.2 ? 1 : 0) : 1 + Math.floor(rng() * 3);
  return {
    assessment_id: assessmentId,
    student_id: studentId,
    class_id: classId,
    question_id: questionId,
    answer: answerText(correctness, rng),
    correctness,
    response_time: 12 + Math.floor(rng() * 90),
    hint_used: hintUsed,
    attempt_count: correctness ? 1 : 1 + Math.floor(rng() * 3),
    error_type: correctness ? null : pickOne(ERROR_TYPES, rng),
    timestamp
  };
}

export function generateSchoolFirstMockData(options = {}) {
  const seed = options.seed || 20260321;
  const teachers = options.teachers || 2;
  const studentsPerTeacher = options.studentsPerTeacher || 58;
  const rng = createRng(seed);
  const baseTime = Date.parse('2026-03-01T08:00:00Z');
  const schoolId = 'school_demo';
  const questions = buildQuestionMeta();
  const questionMap = new Map(questions.map((question) => [question.question_id, question]));

  const admins = [{ admin_id: 'admin_001', role: 'admin', display_name: 'Admin 001' }];
  const teacherProfiles = [];
  const parentProfiles = [];
  const studentProfiles = [];
  const classes = [];
  const assessments = [];
  const sessions = [];
  const answerRecords = [];
  const interventionRecords = [];

  let studentGlobalIndex = 0;

  for (let teacherIndex = 0; teacherIndex < teachers; teacherIndex += 1) {
    const teacherId = `teacher_${teacherIndex + 1}`;
    const classId = `class_${teacherIndex + 1}`;
    teacherProfiles.push({
      teacher_id: teacherId,
      role: 'teacher',
      display_name: `Teacher ${teacherIndex + 1}`,
      class_ids: [classId]
    });
    classes.push({
      class_id: classId,
      teacher_id: teacherId,
      school_id: schoolId,
      class_name: `G5-${String.fromCharCode(65 + teacherIndex)}`,
      grade: 'G5'
    });

    for (let localIndex = 0; localIndex < studentsPerTeacher; localIndex += 1) {
      studentGlobalIndex += 1;
      const studentId = `student_${String(studentGlobalIndex).padStart(3, '0')}`;
      const parentId = `parent_${String(studentGlobalIndex).padStart(3, '0')}`;
      const cohort = performanceBand(studentGlobalIndex - 1);
      const outcome = outcomeBand(studentGlobalIndex - 1);
      const baseline = probabilityByBand(cohort);
      const postProbability = clamp(baseline + deltaByOutcome(outcome), 0.05, 0.97);
      const preAssessmentId = `asm_pre_${studentId}`;
      const postAssessmentId = `asm_post_${studentId}`;
      const preSessionId = `sess_pre_${studentId}`;
      const postSessionId = `sess_post_${studentId}`;
      const focusGroups = COMPARABLE_GROUPS.slice(0, 6);

      parentProfiles.push({
        parent_id: parentId,
        role: 'parent',
        display_name: `Parent ${String(studentGlobalIndex).padStart(3, '0')}`,
        student_ids: [studentId]
      });
      studentProfiles.push({
        student_id: studentId,
        display_name: `Student ${String(studentGlobalIndex).padStart(3, '0')}`,
        class_id: classId,
        parent_id: parentId,
        grade: 'G5',
        cohort_label: cohort
      });

      assessments.push(
        {
          assessment_id: preAssessmentId,
          class_id: classId,
          student_id: studentId,
          assessment_kind: 'pre_test',
          assigned_at: isoFrom(baseTime, studentGlobalIndex)
        },
        {
          assessment_id: postAssessmentId,
          class_id: classId,
          student_id: studentId,
          assessment_kind: 'post_test',
          assigned_at: isoFrom(baseTime, 600 + studentGlobalIndex)
        }
      );
      sessions.push(
        {
          session_id: preSessionId,
          assessment_id: preAssessmentId,
          student_id: studentId,
          started_at: isoFrom(baseTime, studentGlobalIndex + 5),
          completed_at: isoFrom(baseTime, studentGlobalIndex + 20)
        },
        {
          session_id: postSessionId,
          assessment_id: postAssessmentId,
          student_id: studentId,
          started_at: isoFrom(baseTime, 650 + studentGlobalIndex),
          completed_at: isoFrom(baseTime, 670 + studentGlobalIndex)
        }
      );

      focusGroups.forEach((group, groupIndex) => {
        const equivalentGroupId = `eg_${String(groupIndex + 1).padStart(2, '0')}`;
        const preQuestionId = `q_pre_${equivalentGroupId}`;
        const postQuestionId = `q_post_${equivalentGroupId}`;
        const preCorrect = rng() < baseline;
        const postCorrect = rng() < postProbability;
        answerRecords.push(
          buildAnswerRecord({
            assessmentId: preAssessmentId,
            studentId,
            classId,
            questionId: preQuestionId,
            correctness: preCorrect,
            rng,
            timestamp: isoFrom(baseTime, studentGlobalIndex * 10 + groupIndex)
          }),
          buildAnswerRecord({
            assessmentId: postAssessmentId,
            studentId,
            classId,
            questionId: postQuestionId,
            correctness: postCorrect,
            rng,
            timestamp: isoFrom(baseTime, 700 + studentGlobalIndex * 10 + groupIndex)
          })
        );
      });

      const firstWrongGroup = answerRecords
        .filter((record) => record.student_id === studentId && record.assessment_id === preAssessmentId && !record.correctness)
        .map((record) => questionMap.get(record.question_id))
        .filter(Boolean)[0] || questionMap.get('q_pre_eg_01');

      interventionRecords.push({
        intervention_id: `int_${studentId}`,
        teacher_id: teacherId,
        class_id: classId,
        student_id: studentId,
        focus_skill_tags: [firstWrongGroup.skill_tag],
        focus_knowledge_points: [firstWrongGroup.knowledge_point],
        outcome_expectation: outcome,
        created_at: isoFrom(baseTime, 400 + studentGlobalIndex)
      });
    }
  }

  return {
    meta: {
      seed,
      school_id: schoolId,
      generated_at: new Date(baseTime).toISOString(),
      teachers,
      students_per_teacher: studentsPerTeacher,
      total_students: studentProfiles.length,
      error_types: ERROR_TYPES.slice()
    },
    admins,
    teachers: teacherProfiles,
    parents: parentProfiles,
    students: studentProfiles,
    classes,
    questions,
    assessments,
    assessment_sessions: sessions,
    answer_records: answerRecords,
    intervention_records: interventionRecords
  };
}

export { ERROR_TYPES };
