-- ============================================================================
-- COHORT SYSTEM - COMPLETE DATABASE SETUP
-- ============================================================================
-- This script creates all tables and updates needed for the cohort system
-- Run this on your PostgreSQL database
-- ============================================================================

-- ============================================================================
-- PART 1: COHORT LEARNING TABLES (New Tables)
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_cohort_day_materials_cohort ON cohort_day_materials(cohort_id);
CREATE INDEX IF NOT EXISTS idx_cohort_day_materials_day ON cohort_day_materials(day_number);

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

CREATE INDEX IF NOT EXISTS idx_material_progress_enrollment ON cohort_material_progress(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_material_progress_status ON cohort_material_progress(status);

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

CREATE INDEX IF NOT EXISTS idx_cohort_exams_cohort ON cohort_exams(cohort_id);
CREATE INDEX IF NOT EXISTS idx_cohort_exams_scheduled ON cohort_exams(scheduled_date);

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

CREATE INDEX IF NOT EXISTS idx_exam_submissions_enrollment ON cohort_exam_submissions(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_exam_submissions_status ON cohort_exam_submissions(status);

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

CREATE INDEX IF NOT EXISTS idx_cohort_grades_overall ON cohort_grades(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_cohort_grades_rank ON cohort_grades(rank);

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

CREATE INDEX IF NOT EXISTS idx_peer_messages_cohort ON cohort_peer_messages(cohort_id);
CREATE INDEX IF NOT EXISTS idx_peer_messages_sender ON cohort_peer_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_peer_messages_recipient ON cohort_peer_messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_peer_messages_created ON cohort_peer_messages(created_at DESC);

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

CREATE INDEX IF NOT EXISTS idx_mentor_messages_cohort ON cohort_mentor_messages(cohort_id);
CREATE INDEX IF NOT EXISTS idx_mentor_messages_student ON cohort_mentor_messages(student_id);
CREATE INDEX IF NOT EXISTS idx_mentor_messages_mentor ON cohort_mentor_messages(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_messages_created ON cohort_mentor_messages(created_at DESC);

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

CREATE INDEX IF NOT EXISTS idx_cohort_payments_enrollment ON cohort_payments(enrollment_id);
CREATE INDEX IF NOT EXISTS idx_cohort_payments_reference ON cohort_payments(paystack_reference);
CREATE INDEX IF NOT EXISTS idx_cohort_payments_status ON cohort_payments(status);

-- ============================================================================
-- PART 2: AUTOMATED ENROLLMENT UPDATES (Modify Existing Tables)
-- ============================================================================

-- Update cohort_public_applications table for automated enrollment
ALTER TABLE cohort_public_applications
ADD COLUMN IF NOT EXISTS payment_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS onboarding_link_sent_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS password_created_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS onboarding_token VARCHAR(255) UNIQUE;

-- Remove interview fields (no longer needed)
ALTER TABLE cohort_public_applications
DROP COLUMN IF EXISTS interview_mentor_id,
DROP COLUMN IF EXISTS interview_score,
DROP COLUMN IF EXISTS interview_graded_at,
DROP COLUMN IF EXISTS interview_status;

-- Add enrollment fee and payment deadline to cohorts
ALTER TABLE cohorts
ADD COLUMN IF NOT EXISTS enrollment_fee DECIMAL(10, 2) DEFAULT 100.00,
ADD COLUMN IF NOT EXISTS payment_deadline_hours INTEGER DEFAULT 48;

-- Add indexes for automated enrollment
CREATE INDEX IF NOT EXISTS idx_applications_payment_deadline 
ON cohort_public_applications(payment_deadline);

CREATE INDEX IF NOT EXISTS idx_applications_onboarding_token 
ON cohort_public_applications(onboarding_token);

CREATE INDEX IF NOT EXISTS idx_applications_review_status 
ON cohort_public_applications(cohort_id, review_status, status);

-- ============================================================================
-- PART 3: HELPER FUNCTIONS
-- ============================================================================

-- Function to auto-expire payments
CREATE OR REPLACE FUNCTION expire_overdue_payments()
RETURNS void AS $$
BEGIN
    -- Update applications with expired payment deadlines
    UPDATE cohort_public_applications
    SET status = 'rejected'
    WHERE payment_deadline < NOW()
    AND status = 'approved'
    AND enrollment_id IS NULL;  -- Not yet enrolled
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- PART 4: COMMENTS (Documentation)
-- ============================================================================

-- Cohort learning tables
COMMENT ON TABLE cohort_day_materials IS 'Learning materials organized by cohort day';
COMMENT ON TABLE cohort_material_progress IS 'Student progress on cohort materials';
COMMENT ON TABLE cohort_exams IS 'Exams for cohorts';
COMMENT ON TABLE cohort_exam_submissions IS 'Student exam submissions';
COMMENT ON TABLE cohort_grades IS 'Comprehensive grades for cohort students';
COMMENT ON TABLE cohort_peer_messages IS 'Peer-to-peer messaging within cohort';
COMMENT ON TABLE cohort_mentor_messages IS 'Student-to-mentor messaging within cohort';
COMMENT ON TABLE cohort_payments IS 'Cohort enrollment payments via Paystack';

-- Automated enrollment fields
COMMENT ON COLUMN cohort_public_applications.payment_deadline IS 'Deadline for payment after approval (automated)';
COMMENT ON COLUMN cohort_public_applications.onboarding_link_sent_at IS 'When onboarding email was sent';
COMMENT ON COLUMN cohort_public_applications.password_created_at IS 'When student created their password';
COMMENT ON COLUMN cohort_public_applications.onboarding_token IS 'Secure token for account creation link';
COMMENT ON COLUMN cohorts.enrollment_fee IS 'One-time enrollment fee for cohort';
COMMENT ON COLUMN cohorts.payment_deadline_hours IS 'Hours allowed for payment after approval';

-- Helper function
COMMENT ON FUNCTION expire_overdue_payments IS 'Automatically reject applications with expired payment deadlines';

-- ============================================================================
-- PART 5: VERIFICATION QUERIES
-- ============================================================================

-- Run these queries to verify the tables were created successfully

-- Check cohort learning tables
SELECT 'cohort_day_materials' as table_name, COUNT(*) as exists 
FROM information_schema.tables 
WHERE table_name = 'cohort_day_materials'
UNION ALL
SELECT 'cohort_material_progress', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_material_progress'
UNION ALL
SELECT 'cohort_exams', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_exams'
UNION ALL
SELECT 'cohort_exam_submissions', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_exam_submissions'
UNION ALL
SELECT 'cohort_grades', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_grades'
UNION ALL
SELECT 'cohort_peer_messages', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_peer_messages'
UNION ALL
SELECT 'cohort_mentor_messages', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_mentor_messages'
UNION ALL
SELECT 'cohort_payments', COUNT(*) 
FROM information_schema.tables 
WHERE table_name = 'cohort_payments';

-- Check new columns in cohort_public_applications
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'cohort_public_applications' 
AND column_name IN ('payment_deadline', 'onboarding_token', 'onboarding_link_sent_at', 'password_created_at')
ORDER BY column_name;

-- Check new columns in cohorts
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'cohorts' 
AND column_name IN ('enrollment_fee', 'payment_deadline_hours')
ORDER BY column_name;

-- Check that interview columns were removed
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'cohort_public_applications' 
AND column_name LIKE 'interview%';
-- Should return 0 rows

-- ============================================================================
-- EXECUTION COMPLETE
-- ============================================================================

-- Summary of changes:
-- ✅ Created 8 new tables for cohort learning system
-- ✅ Added 4 new columns to cohort_public_applications
-- ✅ Removed 4 interview columns from cohort_public_applications
-- ✅ Added 2 new columns to cohorts table
-- ✅ Created 8 indexes for performance
-- ✅ Created 1 helper function
-- ✅ Added documentation comments

-- Next steps:
-- 1. Verify all tables were created (run verification queries above)
-- 2. Update Django models if needed
-- 3. Deploy backend code
-- 4. Deploy frontend code
-- 5. Test the complete flow

-- ============================================================================
