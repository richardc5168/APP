(function () {
  'use strict';

  var ERROR_TYPES = [
    'concept_confusion',
    'careless_error',
    'place_value_error',
    'operation_misread',
    'multi_step_breakdown'
  ];

  var COMPARABLE_GROUPS = [
    ['fraction', 'add_like', 'fraction_add', 'kp_fraction_add', 'easy'],
    ['fraction', 'sub_like', 'fraction_sub', 'kp_fraction_sub', 'easy'],
    ['decimal', 'place_value', 'decimal_place_value', 'kp_decimal_place_value', 'medium'],
    ['decimal', 'add_sub', 'decimal_operations', 'kp_decimal_add_sub', 'medium'],
    ['ratio', 'unit_rate', 'ratio_reasoning', 'kp_unit_rate', 'medium'],
    ['measurement', 'unit_convert', 'unit_conversion', 'kp_unit_conversion', 'medium']
  ];

  function createRng(seed) {
    var state = Math.abs(Number(seed) || 1) % 2147483647;
    if (state === 0) state = 1;
    return function next() {
      state = (state * 48271) % 2147483647;
      return (state - 1) / 2147483646;
    };
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function average(items) {
    if (!items.length) return 0;
    var total = 0;
    var index;
    for (index = 0; index < items.length; index += 1) total += items[index];
    return total / items.length;
  }

  function round(value) {
    return Math.round(value * 1000) / 1000;
  }

  function isoFrom(baseMs, offsetMinutes) {
    return new Date(baseMs + offsetMinutes * 60000).toISOString();
  }

  function buildQuestionMeta() {
    var questions = [];
    var index;
    for (index = 0; index < COMPARABLE_GROUPS.length; index += 1) {
      var group = COMPARABLE_GROUPS[index];
      var equivalentGroupId = 'eg_' + String(index + 1).padStart(2, '0');
      questions.push({
        question_id: 'q_pre_' + equivalentGroupId,
        topic: group[0],
        subtopic: group[1],
        skill_tag: group[2],
        knowledge_point: group[3],
        difficulty: group[4],
        pattern_type: 'pre_variant',
        equivalent_group_id: equivalentGroupId
      });
      questions.push({
        question_id: 'q_post_' + equivalentGroupId,
        topic: group[0],
        subtopic: group[1],
        skill_tag: group[2],
        knowledge_point: group[3],
        difficulty: group[4],
        pattern_type: 'post_variant',
        equivalent_group_id: equivalentGroupId
      });
    }
    return questions;
  }

  function performanceBand(studentIndex) {
    var mod = studentIndex % 10;
    if (mod < 2) return 'high';
    if (mod < 7) return 'medium';
    return 'at_risk';
  }

  function outcomeBand(studentIndex) {
    var mod = studentIndex % 3;
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

  function buildAnswerRecord(assessmentId, studentId, classId, questionId, correctness, rng, timestamp) {
    var hintUsed = correctness ? (rng() < 0.2 ? 1 : 0) : 1 + Math.floor(rng() * 3);
    return {
      assessment_id: assessmentId,
      student_id: studentId,
      class_id: classId,
      question_id: questionId,
      answer: correctness ? String(1 + Math.floor(rng() * 9)) : String(10 + Math.floor(rng() * 9)),
      correctness: correctness,
      response_time: 12 + Math.floor(rng() * 90),
      hint_used: hintUsed,
      attempt_count: correctness ? 1 : 1 + Math.floor(rng() * 3),
      error_type: correctness ? null : ERROR_TYPES[Math.floor(rng() * ERROR_TYPES.length)],
      timestamp: timestamp
    };
  }

  function questionMap(questions) {
    var map = {};
    var index;
    for (index = 0; index < questions.length; index += 1) map[questions[index].question_id] = questions[index];
    return map;
  }

  function summarizeComparableAnswers(records, questionsById) {
    var groups = {};
    var index;
    for (index = 0; index < records.length; index += 1) {
      var record = records[index];
      var question = questionsById[record.question_id];
      if (!question) continue;
      var key = question.equivalent_group_id || [question.skill_tag, question.knowledge_point, question.difficulty].join('|');
      if (!groups[key]) {
        groups[key] = {
          equivalent_group_id: question.equivalent_group_id || null,
          skill_tag: question.skill_tag,
          knowledge_point: question.knowledge_point,
          difficulty: question.difficulty,
          question_ids: [],
          correct_values: []
        };
      }
      groups[key].question_ids.push(record.question_id);
      groups[key].correct_values.push(record.correctness ? 1 : 0);
    }
    var keys = Object.keys(groups);
    var summary = {};
    for (index = 0; index < keys.length; index += 1) {
      var group = groups[keys[index]];
      summary[keys[index]] = {
        equivalent_group_id: group.equivalent_group_id,
        skill_tag: group.skill_tag,
        knowledge_point: group.knowledge_point,
        difficulty: group.difficulty,
        accuracy: average(group.correct_values),
        question_count: group.correct_values.length
      };
    }
    return summary;
  }

  function statusFromDelta(delta) {
    if (delta >= 0.12) return 'improved';
    if (delta <= -0.05) return 'regressed';
    return 'plateau';
  }

  function aggregateComparableUnits(units, field) {
    var grouped = {};
    var index;
    for (index = 0; index < units.length; index += 1) {
      var unit = units[index];
      var key = unit[field];
      if (!grouped[key]) grouped[key] = { pre: [], post: [], delta: [] };
      grouped[key].pre.push(unit.pre_accuracy);
      grouped[key].post.push(unit.post_accuracy);
      grouped[key].delta.push(unit.delta);
    }
    var keys = Object.keys(grouped);
    var out = [];
    for (index = 0; index < keys.length; index += 1) {
      var entry = grouped[keys[index]];
      var row = {};
      row[field] = keys[index];
      row.pre_accuracy = round(average(entry.pre));
      row.post_accuracy = round(average(entry.post));
      row.delta = round(average(entry.delta));
      out.push(row);
    }
    out.sort(function (a, b) { return b.delta - a.delta; });
    return out;
  }

  function compareStudentPerformance(student, questions, preAnswers, postAnswers, interventions) {
    var questionsById = questionMap(questions);
    var preSummary = summarizeComparableAnswers(preAnswers, questionsById);
    var postSummary = summarizeComparableAnswers(postAnswers, questionsById);
    var keyMap = {};
    var keys;
    var index;
    for (keys = Object.keys(preSummary), index = 0; index < keys.length; index += 1) keyMap[keys[index]] = true;
    for (keys = Object.keys(postSummary), index = 0; index < keys.length; index += 1) keyMap[keys[index]] = true;

    var comparableUnits = [];
    var reliabilityFlags = [];
    keys = Object.keys(keyMap);
    for (index = 0; index < keys.length; index += 1) {
      var key = keys[index];
      var preUnit = preSummary[key];
      var postUnit = postSummary[key];
      if (!preUnit || !postUnit) {
        reliabilityFlags.push('missing_window:' + key);
        continue;
      }
      comparableUnits.push({
        comparable_key: key,
        equivalent_group_id: postUnit.equivalent_group_id || preUnit.equivalent_group_id,
        skill_tag: postUnit.skill_tag,
        knowledge_point: postUnit.knowledge_point,
        pre_accuracy: preUnit.accuracy,
        post_accuracy: postUnit.accuracy,
        delta: postUnit.accuracy - preUnit.accuracy,
        reliability_flags: []
      });
    }

    var overallPre = average(comparableUnits.map(function (item) { return item.pre_accuracy; }));
    var overallPost = average(comparableUnits.map(function (item) { return item.post_accuracy; }));
    var overallDelta = overallPost - overallPre;
    var status = statusFromDelta(overallDelta);
    var highRisk = overallPost < 0.5 && overallDelta < 0.08;

    return {
      student_id: student.student_id,
      class_id: student.class_id,
      status: status,
      high_risk: highRisk,
      reliability_flags: reliabilityFlags,
      pre_accuracy: round(overallPre),
      post_accuracy: round(overallPost),
      delta: round(overallDelta),
      comparable_units: comparableUnits.map(function (item) {
        return {
          comparable_key: item.comparable_key,
          equivalent_group_id: item.equivalent_group_id,
          skill_tag: item.skill_tag,
          knowledge_point: item.knowledge_point,
          pre_accuracy: round(item.pre_accuracy),
          post_accuracy: round(item.post_accuracy),
          delta: round(item.delta),
          reliability_flags: item.reliability_flags
        };
      }),
      knowledge_point_improvement: aggregateComparableUnits(comparableUnits, 'knowledge_point'),
      skill_tag_improvement: aggregateComparableUnits(comparableUnits, 'skill_tag'),
      intervention_ids: interventions.map(function (item) { return item.intervention_id; }),
      teacher_summary: student.display_name + ' ' + status + ' by ' + Math.round(overallDelta * 100) + ' points.',
      parent_summary: status === 'improved'
        ? student.display_name + ' is showing clear progress after practice.'
        : status === 'regressed'
          ? student.display_name + ' needs another round of support this week.'
          : student.display_name + ' is steady and needs one focused next step.'
    };
  }

  function buildClassImprovementReport(classRoom, students, questions, answerRecords, interventions) {
    var studentComparisons = students.map(function (student) {
      var preAnswers = answerRecords.filter(function (record) {
        return record.student_id === student.student_id && record.assessment_id.indexOf('asm_pre_') === 0;
      });
      var postAnswers = answerRecords.filter(function (record) {
        return record.student_id === student.student_id && record.assessment_id.indexOf('asm_post_') === 0;
      });
      var studentInterventions = interventions.filter(function (item) { return item.student_id === student.student_id; });
      return compareStudentPerformance(student, questions, preAnswers, postAnswers, studentInterventions);
    });
    return {
      class_id: classRoom.class_id,
      teacher_id: classRoom.teacher_id,
      student_count: studentComparisons.length,
      status_counts: {
        improved: studentComparisons.filter(function (item) { return item.status === 'improved'; }).length,
        plateau: studentComparisons.filter(function (item) { return item.status === 'plateau'; }).length,
        regressed: studentComparisons.filter(function (item) { return item.status === 'regressed'; }).length
      },
      high_risk_students: studentComparisons.filter(function (item) { return item.high_risk; }).map(function (item) { return item.student_id; }),
      knowledge_point_improvement: aggregateComparableUnits(studentComparisons.reduce(function (all, item) { return all.concat(item.comparable_units); }, []), 'knowledge_point'),
      skill_tag_improvement: aggregateComparableUnits(studentComparisons.reduce(function (all, item) { return all.concat(item.comparable_units); }, []), 'skill_tag'),
      student_reports: studentComparisons
    };
  }

  function buildProofPack(dataset) {
    var classReports = dataset.classes.map(function (classRoom) {
      var classStudents = dataset.students.filter(function (student) { return student.class_id === classRoom.class_id; });
      return buildClassImprovementReport(classRoom, classStudents, dataset.questions, dataset.answer_records, dataset.intervention_records);
    });

    return {
      admin_summary: {
        total_students: dataset.students.length,
        total_classes: dataset.classes.length,
        improved_students: classReports.reduce(function (sum, item) { return sum + item.status_counts.improved; }, 0),
        plateau_students: classReports.reduce(function (sum, item) { return sum + item.status_counts.plateau; }, 0),
        regressed_students: classReports.reduce(function (sum, item) { return sum + item.status_counts.regressed; }, 0)
      },
      teacher_class_reports: classReports,
      parent_reports: dataset.students.map(function (student) {
        var classReport = classReports.filter(function (report) { return report.class_id === student.class_id; })[0];
        var studentReport = classReport.student_reports.filter(function (report) { return report.student_id === student.student_id; })[0];
        return {
          parent_id: student.parent_id,
          student_id: student.student_id,
          status: studentReport.status,
          parent_summary: studentReport.parent_summary,
          high_risk: studentReport.high_risk
        };
      })
    };
  }

  function generateSchoolFirstMockData(options) {
    options = options || {};
    var seed = options.seed || 20260321;
    var teachers = options.teachers || 2;
    var studentsPerTeacher = options.studentsPerTeacher || 58;
    var rng = createRng(seed);
    var baseTime = Date.parse('2026-03-01T08:00:00Z');
    var questions = buildQuestionMeta();
    var dataset = {
      meta: {
        seed: seed,
        school_id: 'school_demo',
        generated_at: new Date(baseTime).toISOString(),
        teachers: teachers,
        students_per_teacher: studentsPerTeacher,
        total_students: teachers * studentsPerTeacher,
        error_types: ERROR_TYPES.slice()
      },
      admins: [{ admin_id: 'admin_001', role: 'admin', display_name: 'Admin 001' }],
      teachers: [],
      parents: [],
      students: [],
      classes: [],
      questions: questions,
      assessments: [],
      assessment_sessions: [],
      answer_records: [],
      intervention_records: []
    };
    var studentGlobalIndex = 0;
    var teacherIndex;
    for (teacherIndex = 0; teacherIndex < teachers; teacherIndex += 1) {
      var teacherId = 'teacher_' + (teacherIndex + 1);
      var classId = 'class_' + (teacherIndex + 1);
      dataset.teachers.push({ teacher_id: teacherId, role: 'teacher', display_name: 'Teacher ' + (teacherIndex + 1), class_ids: [classId] });
      dataset.classes.push({ class_id: classId, teacher_id: teacherId, school_id: 'school_demo', class_name: 'G5-' + String.fromCharCode(65 + teacherIndex), grade: 'G5' });
      var localIndex;
      for (localIndex = 0; localIndex < studentsPerTeacher; localIndex += 1) {
        studentGlobalIndex += 1;
        var studentId = 'student_' + String(studentGlobalIndex).padStart(3, '0');
        var parentId = 'parent_' + String(studentGlobalIndex).padStart(3, '0');
        var cohort = performanceBand(studentGlobalIndex - 1);
        var outcome = outcomeBand(studentGlobalIndex - 1);
        var baseline = probabilityByBand(cohort);
        var postProbability = clamp(baseline + deltaByOutcome(outcome), 0.05, 0.97);
        dataset.parents.push({ parent_id: parentId, role: 'parent', display_name: 'Parent ' + String(studentGlobalIndex).padStart(3, '0'), student_ids: [studentId] });
        dataset.students.push({ student_id: studentId, display_name: 'Student ' + String(studentGlobalIndex).padStart(3, '0'), class_id: classId, parent_id: parentId, grade: 'G5', cohort_label: cohort });
        dataset.intervention_records.push({
          intervention_id: 'int_' + studentId,
          teacher_id: teacherId,
          class_id: classId,
          student_id: studentId,
          focus_skill_tags: [COMPARABLE_GROUPS[localIndex % COMPARABLE_GROUPS.length][2]],
          focus_knowledge_points: [COMPARABLE_GROUPS[localIndex % COMPARABLE_GROUPS.length][3]],
          outcome_expectation: outcome,
          created_at: isoFrom(baseTime, 300 + studentGlobalIndex)
        });
        var groupIndex;
        for (groupIndex = 0; groupIndex < COMPARABLE_GROUPS.length; groupIndex += 1) {
          var eg = 'eg_' + String(groupIndex + 1).padStart(2, '0');
          dataset.answer_records.push(
            buildAnswerRecord('asm_pre_' + studentId, studentId, classId, 'q_pre_' + eg, rng() < baseline, rng, isoFrom(baseTime, studentGlobalIndex * 10 + groupIndex)),
            buildAnswerRecord('asm_post_' + studentId, studentId, classId, 'q_post_' + eg, rng() < postProbability, rng, isoFrom(baseTime, 600 + studentGlobalIndex * 10 + groupIndex))
          );
        }
      }
    }
    return dataset;
  }

  function buildMockContext(options) {
    var dataset = generateSchoolFirstMockData(options || {});
    var proof = buildProofPack(dataset);
    return { dataset: dataset, proof: proof };
  }

  function getTeacherDashboard(context, teacherId) {
    var dataset = context.dataset;
    var proof = context.proof;
    var teacher = dataset.teachers.filter(function (item) { return item.teacher_id === teacherId; })[0] || dataset.teachers[0];
    var classId = teacher.class_ids[0];
    var classRoom = dataset.classes.filter(function (item) { return item.class_id === classId; })[0];
    var report = proof.teacher_class_reports.filter(function (item) { return item.class_id === classId; })[0];
    var studentRows = dataset.students.filter(function (item) { return item.class_id === classId; }).map(function (student) {
      var studentReport = report.student_reports.filter(function (item) { return item.student_id === student.student_id; })[0];
      return {
        student_id: student.student_id,
        display_name: student.display_name,
        grade: student.grade,
        cohort_label: student.cohort_label,
        status: studentReport.status,
        high_risk: studentReport.high_risk,
        pre_accuracy: studentReport.pre_accuracy,
        post_accuracy: studentReport.post_accuracy,
        delta: studentReport.delta,
        teacher_summary: studentReport.teacher_summary,
        intervention_status: dataset.intervention_records.filter(function (item) { return item.student_id === student.student_id; })[0].outcome_expectation,
        comparable_units: studentReport.comparable_units
      };
    });
    studentRows.sort(function (a, b) {
      if (a.high_risk !== b.high_risk) return a.high_risk ? -1 : 1;
      return a.delta - b.delta;
    });
    return {
      teacher: teacher,
      class: classRoom,
      overview: {
        student_count: report.student_count,
        pre_accuracy: round(average(report.student_reports.map(function (item) { return item.pre_accuracy; }))),
        post_accuracy: round(average(report.student_reports.map(function (item) { return item.post_accuracy; }))),
        improved: report.status_counts.improved,
        plateau: report.status_counts.plateau,
        regressed: report.status_counts.regressed
      },
      students: studentRows,
      skill_summary: report.skill_tag_improvement,
      knowledge_summary: report.knowledge_point_improvement,
      before_after: report,
      high_risk_students: studentRows.filter(function (item) { return item.high_risk; }).slice(0, 12)
    };
  }

  function getParentView(context, parentId) {
    var dataset = context.dataset;
    var proof = context.proof;
    var parent = dataset.parents.filter(function (item) { return item.parent_id === parentId; })[0] || dataset.parents[0];
    var student = dataset.students.filter(function (item) { return item.student_id === parent.student_ids[0]; })[0];
    var classReport = proof.teacher_class_reports.filter(function (item) { return item.class_id === student.class_id; })[0];
    var studentReport = classReport.student_reports.filter(function (item) { return item.student_id === student.student_id; })[0];
    var strongest = studentReport.comparable_units.slice().sort(function (a, b) { return b.post_accuracy - a.post_accuracy; }).slice(0, 2);
    var weakest = studentReport.comparable_units.slice().sort(function (a, b) { return a.post_accuracy - b.post_accuracy; }).slice(0, 3);
    return {
      parent: parent,
      student: student,
      latest_assessment: {
        status: studentReport.status,
        pre_accuracy: studentReport.pre_accuracy,
        post_accuracy: studentReport.post_accuracy,
        delta: studentReport.delta,
        hint_dependency: weakest.filter(function (item) { return item.post_accuracy < 0.6; }).length
      },
      mastered: strongest,
      needs_reinforcement: weakest,
      recommendations: [
        'Focus this week on ' + (weakest[0] ? weakest[0].knowledge_point : 'one target skill') + '.',
        studentReport.high_risk ? 'Ask the teacher for a short intervention check-in.' : 'Keep the home routine short and consistent.',
        studentReport.status === 'improved' ? 'Keep the same practice cadence for one more cycle.' : 'Repeat one comparable practice set before the next post-test.'
      ],
      before_after: studentReport,
      parent_actions: [
        'What happened: ' + studentReport.parent_summary,
        'Why it matters: ' + (weakest[0] ? weakest[0].knowledge_point + ' is still below the target band.' : 'One key concept still needs repetition.'),
        'What to do now: one 10-minute practice block and one teacher follow-up question.'
      ]
    };
  }

  function getAdminDashboard(context) {
    var dataset = context.dataset;
    var proof = context.proof;
    var teacherRows = dataset.teachers.map(function (teacher) {
      var classId = teacher.class_ids[0];
      var classReport = proof.teacher_class_reports.filter(function (item) { return item.class_id === classId; })[0];
      return {
        teacher_id: teacher.teacher_id,
        display_name: teacher.display_name,
        class_count: teacher.class_ids.length,
        improved: classReport.status_counts.improved,
        plateau: classReport.status_counts.plateau,
        regressed: classReport.status_counts.regressed,
        high_risk_students: classReport.high_risk_students.length
      };
    });
    var classRows = proof.teacher_class_reports.map(function (report) {
      return {
        class_id: report.class_id,
        teacher_id: report.teacher_id,
        student_count: report.student_count,
        pre_accuracy: round(average(report.student_reports.map(function (item) { return item.pre_accuracy; }))),
        post_accuracy: round(average(report.student_reports.map(function (item) { return item.post_accuracy; }))),
        delta: round(average(report.student_reports.map(function (item) { return item.delta; }))),
        high_risk_count: report.high_risk_students.length
      };
    });
    var knowledge = aggregateComparableUnits(
      proof.teacher_class_reports.reduce(function (all, report) { return all.concat(report.student_reports.reduce(function (inner, row) { return inner.concat(row.comparable_units); }, [])); }, []),
      'knowledge_point'
    );
    return {
      summary: proof.admin_summary,
      teachers: teacherRows,
      classes: classRows,
      before_after_summary: {
        status_distribution: proof.admin_summary,
        top_improving_knowledge_points: knowledge.slice(0, 4),
        top_struggling_knowledge_points: knowledge.slice().sort(function (a, b) { return a.delta - b.delta; }).slice(0, 4)
      },
      report_coverage: {
        generated_count: classRows.reduce(function (sum, row) { return sum + row.student_count; }, 0),
        missing_count: 0
      }
    };
  }

  window.AIMathSchoolFirstMock = {
    buildMockContext: buildMockContext,
    getTeacherDashboard: getTeacherDashboard,
    getParentView: getParentView,
    getAdminDashboard: getAdminDashboard
  };
})();
