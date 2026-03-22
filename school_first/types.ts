export type Role = 'parent' | 'teacher' | 'admin';

export interface AdminProfile {
  admin_id: string;
  role: 'admin';
  display_name: string;
}

export interface TeacherProfile {
  teacher_id: string;
  role: 'teacher';
  display_name: string;
  class_ids: string[];
}

export interface ParentProfile {
  parent_id: string;
  role: 'parent';
  display_name: string;
  student_ids: string[];
}

export interface StudentProfile {
  student_id: string;
  display_name: string;
  class_id: string;
  parent_id: string;
  grade: string;
  cohort_label: 'high' | 'medium' | 'at_risk';
}

export interface ClassRoom {
  class_id: string;
  teacher_id: string;
  school_id: string;
  class_name: string;
  grade: string;
}

export interface QuestionMeta {
  question_id: string;
  topic: string;
  subtopic: string;
  skill_tag: string;
  knowledge_point: string;
  difficulty: 'easy' | 'medium' | 'hard';
  pattern_type: string;
  equivalent_group_id: string;
}

export interface Assessment {
  assessment_id: string;
  class_id: string;
  student_id: string;
  assessment_kind: 'pre_test' | 'post_test';
  assigned_at: string;
}

export interface AssessmentSession {
  session_id: string;
  assessment_id: string;
  student_id: string;
  started_at: string;
  completed_at: string;
}

export interface AnswerRecord {
  assessment_id: string;
  student_id: string;
  class_id: string;
  question_id: string;
  answer: string;
  correctness: boolean;
  response_time: number;
  hint_used: number;
  attempt_count: number;
  error_type: string | null;
  timestamp: string;
}

export interface InterventionRecord {
  intervention_id: string;
  teacher_id: string;
  class_id: string;
  student_id: string;
  focus_skill_tags: string[];
  focus_knowledge_points: string[];
  outcome_expectation: 'improved' | 'plateau' | 'regressed';
  created_at: string;
}

export interface ParentReportSnapshot {
  report_id: string;
  student_id: string;
  class_id: string;
  generated_at: string;
  report_phase: 'before' | 'after';
}

export interface TeacherClassReportSnapshot {
  report_id: string;
  class_id: string;
  generated_at: string;
}

export interface BeforeAfterReportSnapshot {
  report_id: string;
  report_scope: 'student' | 'class';
  student_id?: string;
  class_id: string;
  generated_at: string;
  reliability_flags: string[];
}

export interface EntitlementContext {
  actor_role: Role;
  actor_id: string;
  class_ids: string[];
  student_ids: string[];
}
