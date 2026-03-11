-- Cohort Learning Tables Migration
-- Run this SQL to create all cohort-related tables

-- 1. Cohort Day Materials
CREATE TABLE IF NOT EXISTS cohort_day_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
    day_number INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    material_type VARCHAR(20) NOT NULL CHECK (material_type IN ('video', 'article', 'slides', 'lab', 'reading', 'exercise')),
    content_url TEXT,
    content_text TEXT,
    "order" INTEGER DEFAULT 0,
    estimated_minutes INTEGER DEFAULT 30,
    is_required BOOLEAN DEFAULT TRUE,
    unlock_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cohort_id, day_number, "order")
);

CREATE INDEX idx_cohort_day_materials_cohort ON cohort_day_materials(cohort_id);
CREATE INDEX idx_cohort_day_materials_day ON cohort_day_materials(day_number);

-- 2. Cohort Material Progress
CREATE TABLE IF NOT EXISTS cohort_material_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    material_id UUID NOT NULL REFERENCES cohort_day_materials(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'completed')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    time_spent_minutes INTEGER DEFAULT 0,
    notes TEXT,
    UNIQUE(enrollment_id, material_id)
);

CREATE INDEX idx_material_progress_enrollment ON cohort_material_progress(enrollment_id);
CREATE INDEX idx_material_progress_status ON cohort_material_progress(status);

-- 3. Cohort Exams
CREATE TABLE IF NOT EXISTS cohort_exams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    exam_type VARCHAR(20) NOT NULL CHECK (exam_type IN ('quiz', 'midterm', 'final', 'practical')),
    description TEXT,
    day_number INTEGER NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    total_points INTEGER DEFAULT 100,
    passing_score INTEGER DEFAULT 70,
    questions JSONB DEFAULT '[]'::jsonb,
    scheduled_date TIMESTAMP WITH TIME ZONE NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cohort_exams_cohort ON cohort_exams(cohort_id);
CREATE INDEX idx_cohort_exams_scheduled ON cohort_exams(scheduled_date);

-- 4. Cohort Exam Submissions
CREATE TABLE IF NOT EXISTS cohort_exam_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_id UUID NOT NULL REFERENCES cohort_exams(id) ON DELETE CASCADE,
    enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
    answers JSONB DEFAULT '{}'::jsonb,
    score DECIMAL(5, 2),
    status VARCHAR(20) DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'submitted', 'graded')),
    started_at TIMESTAMP WITH TIME ZONE,
    submitted_at TIMESTAMP WITH TIME ZONE,
    graded_at TIMESTAMP WITH TIME ZONE,
    graded_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    feedback TEXT,
    UNIQUE(exam_id, enrollment_id)
);

CREATE INDEX idx_exam_submissions_enrollment ON cohort_exam_submissions(enrollment_id);
CREATE INDEX idx_exam_submissions_status ON cohort_exam_submissions(status);

-- 5. Cohort Grades
CREATE TABLE IF NOT EXISTS cohort_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE CASCADE,
    missions_score DECIMAL(5, 2) DEFAULT 0,
    capstones_score DECIMAL(5, 2) DEFAULT 0,
    labs_score DECIMAL(5, 2) DEFAULT 0,
    exams_score DECIMAL(5, 2) DEFAULT 0,
    participation_score DECIMAL(5, 2) DEFAULT 0,
    overall_score DECIMAL(5, 2) DEFAULT 0,
    letter_grade VARCHAR(2),
    rank INTEGER,
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cohort_grades_overall ON cohort_grades(overall_score DESC);
CREATE INDEX idx_cohort_grades_rank ON cohort_grades(rank);

-- 6. Cohort Peer Messages
CREATE TABLE IF NOT EXISTS cohort_peer_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
    sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    is_group_message BOOLEAN DEFAULT FALSE,
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]'::jsonb,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_peer_messages_cohort ON cohort_peer_messages(cohort_id);
CREATE INDEX idx_peer_messages_sender ON cohort_peer_messages(sender_id);
CREATE INDEX idx_peer_messages_recipient ON cohort_peer_messages(recipient_id);
CREATE INDEX idx_peer_messages_created ON cohort_peer_messages(created_at DESC);

-- 7. Cohort Mentor Messages
CREATE TABLE IF NOT EXISTS cohort_mentor_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cohort_id UUID NOT NULL REFERENCES cohorts(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mentor_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    attachments JSONB DEFAULT '[]'::jsonb,
    is_read BOOLEAN DEFAULT FALSE,
    replied_at TIMESTAMP WITH TIME ZONE,
    reply_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mentor_messages_cohort ON cohort_mentor_messages(cohort_id);
CREATE INDEX idx_mentor_messages_student ON cohort_mentor_messages(student_id);
CREATE INDEX idx_mentor_messages_mentor ON cohort_mentor_messages(mentor_id);
CREATE INDEX idx_mentor_messages_created ON cohort_mentor_messages(created_at DESC);

-- 8. Cohort Payments
CREATE TABLE IF NOT EXISTS cohort_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enrollment_id UUID NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded')),
    paystack_reference VARCHAR(255) UNIQUE NOT NULL,
    paystack_access_code VARCHAR(255),
    paystack_authorization_url TEXT,
    paystack_response JSONB DEFAULT '{}'::jsonb,
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    verified_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_cohort_payments_enrollment ON cohort_payments(enrollment_id);
CREATE INDEX idx_cohort_payments_reference ON cohort_payments(paystack_reference);
CREATE INDEX idx_cohort_payments_status ON cohort_payments(status);

-- Add comments
COMMENT ON TABLE cohort_day_materials IS 'Learning materials organized by cohort day';
COMMENT ON TABLE cohort_material_progress IS 'Student progress on cohort materials';
COMMENT ON TABLE cohort_exams IS 'Exams for cohorts';
COMMENT ON TABLE cohort_exam_submissions IS 'Student exam submissions';
COMMENT ON TABLE cohort_grades IS 'Comprehensive grades for cohort students';
COMMENT ON TABLE cohort_peer_messages IS 'Peer-to-peer messaging within cohort';
COMMENT ON TABLE cohort_mentor_messages IS 'Student-to-mentor messaging within cohort';
COMMENT ON TABLE cohort_payments IS 'Cohort enrollment payments via Paystack';

-- Grant permissions (adjust as needed)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
