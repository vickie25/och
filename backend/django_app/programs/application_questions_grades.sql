-- =============================================================================
-- Application / Interview Questions & Grades (run manually in PostgreSQL)
-- Question bank, candidate sessions, cohort question sets, passing thresholds
-- =============================================================================

-- Question bank (MCQ, scenario, behavioral; used for application and interview)
CREATE TABLE IF NOT EXISTS application_question_bank (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(20) NOT NULL CHECK (type IN ('mcq', 'scenario', 'behavioral')),
  difficulty VARCHAR(20) NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
  topic VARCHAR(255) NULL,
  question_text TEXT NOT NULL,
  options JSONB NULL,
  correct_answer TEXT NULL,
  scoring_weight DECIMAL(5, 2) NOT NULL DEFAULT 1.0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_bank_type ON application_question_bank(type);
CREATE INDEX IF NOT EXISTS idx_question_bank_topic ON application_question_bank(topic);

-- Cohort application question set (which questions, time limit, opens/closes)
CREATE TABLE IF NOT EXISTS cohort_application_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
  question_ids JSONB NOT NULL DEFAULT '[]',
  time_limit_minutes INTEGER NOT NULL DEFAULT 60,
  opens_at TIMESTAMPTZ NULL,
  closes_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(cohort_id)
);

CREATE INDEX IF NOT EXISTS idx_cohort_app_questions_cohort ON cohort_application_questions(cohort_id);

-- Cohort interview question set (for mentor-led interview)
CREATE TABLE IF NOT EXISTS cohort_interview_questions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
  question_ids JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(cohort_id)
);

CREATE INDEX IF NOT EXISTS idx_cohort_int_questions_cohort ON cohort_interview_questions(cohort_id);

-- Candidate session (one per user per application test)
CREATE TABLE IF NOT EXISTS application_candidate_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
  session_type VARCHAR(20) NOT NULL CHECK (session_type IN ('application', 'interview')),
  start_time TIMESTAMPTZ NULL,
  end_time TIMESTAMPTZ NULL,
  total_score DECIMAL(10, 2) NULL,
  flagged_behavior TEXT NULL,
  ai_feedback JSONB NULL,
  answers_snapshot JSONB NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidate_sessions_user ON application_candidate_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_candidate_sessions_cohort ON application_candidate_sessions(cohort_id);
CREATE INDEX IF NOT EXISTS idx_candidate_sessions_type ON application_candidate_sessions(session_type);

-- Passing grade thresholds per cohort (application test and interview)
CREATE TABLE IF NOT EXISTS cohort_grade_thresholds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
  application_passing_score DECIMAL(10, 2) NULL,
  interview_passing_score DECIMAL(10, 2) NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(cohort_id)
);

CREATE INDEX IF NOT EXISTS idx_cohort_grade_thresholds_cohort ON cohort_grade_thresholds(cohort_id);

COMMENT ON TABLE application_question_bank IS 'Questions for application tests and interviews (MCQ, scenario, behavioral)';
COMMENT ON TABLE cohort_application_questions IS 'Application test config per cohort: questions, time limit, open/close dates';
COMMENT ON TABLE cohort_interview_questions IS 'Interview questions per cohort (mentor fills grades per question)';
COMMENT ON TABLE application_candidate_sessions IS 'One row per user per application/interview test; stores score, answers, AI feedback';
COMMENT ON TABLE cohort_grade_thresholds IS 'Passing thresholds per cohort for application and interview stages';
