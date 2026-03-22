function difficultyRank(value) {
  if (value === 'easy') return 1;
  if (value === 'medium') return 2;
  if (value === 'hard') return 3;
  return 0;
}

function average(items) {
  if (!items.length) return 0;
  return items.reduce((total, item) => total + item, 0) / items.length;
}

function questionMap(questions) {
  return new Map((questions || []).map((question) => [question.question_id, question]));
}

function summarizeComparableAnswers(records, questionsById) {
  const groups = new Map();
  for (const record of records || []) {
    const question = questionsById.get(record.question_id);
    if (!question) continue;
    const key = question.equivalent_group_id || `${question.skill_tag}|${question.knowledge_point}|${question.difficulty}`;
    if (!groups.has(key)) {
      groups.set(key, {
        equivalent_group_id: question.equivalent_group_id || null,
        skill_tag: question.skill_tag,
        knowledge_point: question.knowledge_point,
        difficulty: question.difficulty,
        question_ids: [],
        correct_values: []
      });
    }
    const entry = groups.get(key);
    entry.question_ids.push(record.question_id);
    entry.correct_values.push(record.correctness ? 1 : 0);
  }

  const summary = new Map();
  for (const [key, entry] of groups.entries()) {
    summary.set(key, {
      ...entry,
      accuracy: average(entry.correct_values),
      question_count: entry.correct_values.length
    });
  }
  return summary;
}

function statusFromDelta(delta) {
  if (delta >= 0.12) return 'improved';
  if (delta <= -0.05) return 'regressed';
  return 'plateau';
}

export function compareStudentPerformance({ student, questions, preAnswers, postAnswers, interventions = [] }) {
  const questionsById = questionMap(questions);
  const preSummary = summarizeComparableAnswers(preAnswers, questionsById);
  const postSummary = summarizeComparableAnswers(postAnswers, questionsById);
  const comparableKeys = Array.from(new Set([...preSummary.keys(), ...postSummary.keys()]));
  const comparableUnits = [];
  const reliabilityFlags = [];

  for (const key of comparableKeys) {
    const preUnit = preSummary.get(key);
    const postUnit = postSummary.get(key);
    if (!preUnit || !postUnit) {
      reliabilityFlags.push(`missing_window:${key}`);
      continue;
    }
    const difficultyGap = Math.abs(difficultyRank(preUnit.difficulty) - difficultyRank(postUnit.difficulty));
    if (difficultyGap > 1) reliabilityFlags.push(`difficulty_gap:${key}`);
    comparableUnits.push({
      comparable_key: key,
      equivalent_group_id: postUnit.equivalent_group_id || preUnit.equivalent_group_id,
      skill_tag: postUnit.skill_tag,
      knowledge_point: postUnit.knowledge_point,
      pre_accuracy: preUnit.accuracy,
      post_accuracy: postUnit.accuracy,
      delta: postUnit.accuracy - preUnit.accuracy,
      reliability_flags: difficultyGap > 1 ? ['difficulty_gap'] : []
    });
  }

  const overallPre = average(comparableUnits.map((item) => item.pre_accuracy));
  const overallPost = average(comparableUnits.map((item) => item.post_accuracy));
  const overallDelta = overallPost - overallPre;
  const status = statusFromDelta(overallDelta);
  const highRisk = overallPost < 0.5 && overallDelta < 0.08;
  const interventionIds = new Set(interventions.map((item) => item.intervention_id));

  const knowledgePointImprovement = aggregateComparableUnits(comparableUnits, 'knowledge_point');
  const skillImprovement = aggregateComparableUnits(comparableUnits, 'skill_tag');

  return {
    student_id: student.student_id,
    class_id: student.class_id,
    status,
    high_risk: highRisk,
    reliability_flags: Array.from(new Set(reliabilityFlags)),
    pre_accuracy: round(overallPre),
    post_accuracy: round(overallPost),
    delta: round(overallDelta),
    comparable_units: comparableUnits.map((item) => ({ ...item, delta: round(item.delta) })),
    knowledge_point_improvement: knowledgePointImprovement,
    skill_tag_improvement: skillImprovement,
    intervention_ids: Array.from(interventionIds),
    teacher_summary: buildTeacherSummary(student, status, overallDelta, highRisk),
    parent_summary: buildParentSummary(student, status, overallDelta, highRisk)
  };
}

function round(value) {
  return Math.round(value * 1000) / 1000;
}

export function aggregateComparableUnits(units, field) {
  const grouped = new Map();
  for (const unit of units || []) {
    const key = unit[field];
    if (!grouped.has(key)) {
      grouped.set(key, { key, pre: [], post: [], delta: [] });
    }
    const entry = grouped.get(key);
    entry.pre.push(unit.pre_accuracy);
    entry.post.push(unit.post_accuracy);
    entry.delta.push(unit.delta);
  }
  return Array.from(grouped.values()).map((entry) => ({
    [field]: entry.key,
    pre_accuracy: round(average(entry.pre)),
    post_accuracy: round(average(entry.post)),
    delta: round(average(entry.delta))
  }));
}

function buildTeacherSummary(student, status, delta, highRisk) {
  const label = status === 'improved' ? 'improved' : status === 'regressed' ? 'regressed' : 'stayed flat';
  const risk = highRisk ? ' Needs intervention follow-up.' : '';
  return `${student.display_name} ${label} by ${Math.round(delta * 100)} points.${risk}`;
}

function buildParentSummary(student, status, delta, highRisk) {
  if (status === 'improved') return `${student.display_name} is showing clear progress after practice.`;
  if (status === 'regressed') return `${student.display_name} needs another round of support this week.`;
  if (highRisk) return `${student.display_name} needs extra support and teacher follow-up.`;
  return `${student.display_name} is steady and needs one focused next step.`;
}

export function buildClassImprovementReport({ classRoom, students, questions, answerRecords, interventions }) {
  const studentComparisons = students.map((student) => {
    const preAnswers = answerRecords.filter((record) => record.student_id === student.student_id && record.assessment_id.startsWith('asm_pre_'));
    const postAnswers = answerRecords.filter((record) => record.student_id === student.student_id && record.assessment_id.startsWith('asm_post_'));
    const studentInterventions = interventions.filter((item) => item.student_id === student.student_id);
    return compareStudentPerformance({ student, questions, preAnswers, postAnswers, interventions: studentInterventions });
  });

  const knowledgePointImprovement = aggregateComparableUnits(
    studentComparisons.flatMap((comparison) => comparison.comparable_units),
    'knowledge_point'
  );
  const skillTagImprovement = aggregateComparableUnits(
    studentComparisons.flatMap((comparison) => comparison.comparable_units),
    'skill_tag'
  );
  const statusCounts = {
    improved: studentComparisons.filter((item) => item.status === 'improved').length,
    plateau: studentComparisons.filter((item) => item.status === 'plateau').length,
    regressed: studentComparisons.filter((item) => item.status === 'regressed').length
  };

  return {
    class_id: classRoom.class_id,
    teacher_id: classRoom.teacher_id,
    student_count: studentComparisons.length,
    status_counts: statusCounts,
    high_risk_students: studentComparisons.filter((item) => item.high_risk).map((item) => item.student_id),
    knowledge_point_improvement: knowledgePointImprovement,
    skill_tag_improvement: skillTagImprovement,
    student_reports: studentComparisons
  };
}

export function buildProofPack(dataset) {
  const classReports = dataset.classes.map((classRoom) => {
    const classStudents = dataset.students.filter((student) => student.class_id === classRoom.class_id);
    return buildClassImprovementReport({
      classRoom,
      students: classStudents,
      questions: dataset.questions,
      answerRecords: dataset.answer_records,
      interventions: dataset.intervention_records
    });
  });

  const parentReports = dataset.students.map((student) => {
    const classReport = classReports.find((report) => report.class_id === student.class_id);
    const studentReport = classReport.student_reports.find((report) => report.student_id === student.student_id);
    return {
      parent_id: student.parent_id,
      student_id: student.student_id,
      status: studentReport.status,
      parent_summary: studentReport.parent_summary,
      high_risk: studentReport.high_risk
    };
  });

  const beforeAfterReports = classReports.flatMap((classReport) => {
    const studentLevel = classReport.student_reports.map((report) => ({
      report_scope: 'student',
      class_id: classReport.class_id,
      student_id: report.student_id,
      status: report.status,
      reliability_flags: report.reliability_flags
    }));
    return [
      {
        report_scope: 'class',
        class_id: classReport.class_id,
        status_counts: classReport.status_counts,
        reliability_flags: []
      },
      ...studentLevel
    ];
  });

  const adminSummary = {
    total_students: dataset.students.length,
    total_classes: dataset.classes.length,
    improved_students: classReports.reduce((total, report) => total + report.status_counts.improved, 0),
    plateau_students: classReports.reduce((total, report) => total + report.status_counts.plateau, 0),
    regressed_students: classReports.reduce((total, report) => total + report.status_counts.regressed, 0)
  };

  return {
    admin_summary: adminSummary,
    teacher_class_reports: classReports,
    parent_reports: parentReports,
    before_after_reports: beforeAfterReports
  };
}
