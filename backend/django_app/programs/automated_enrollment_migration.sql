-- Automated Cohort Enrollment - Database Updates
-- Run this SQL to update the database for automated enrollment

-- 1. Add payment deadline and tracking fields to applications
ALTER TABLE cohort_public_applications
ADD COLUMN IF NOT EXISTS payment_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS onboarding_link_sent_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS password_created_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS onboarding_token VARCHAR(255) UNIQUE;

-- 2. Remove interview fields (no longer needed)
ALTER TABLE cohort_public_applications
DROP COLUMN IF EXISTS interview_mentor_id,
DROP COLUMN IF EXISTS interview_score,
DROP COLUMN IF EXISTS interview_graded_at,
DROP COLUMN IF EXISTS interview_status;

-- 3. Add enrollment fee to cohorts
ALTER TABLE cohorts
ADD COLUMN IF NOT EXISTS enrollment_fee DECIMAL(10, 2) DEFAULT 100.00,
ADD COLUMN IF NOT EXISTS payment_deadline_hours INTEGER DEFAULT 48;

-- 4. Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_applications_payment_deadline 
ON cohort_public_applications(payment_deadline);

CREATE INDEX IF NOT EXISTS idx_applications_onboarding_token 
ON cohort_public_applications(onboarding_token);

CREATE INDEX IF NOT EXISTS idx_applications_review_status 
ON cohort_public_applications(cohort_id, review_status, status);

-- 5. Update existing applications to remove interview status
UPDATE cohort_public_applications
SET interview_status = NULL
WHERE interview_status IS NOT NULL;

-- 6. Add comments
COMMENT ON COLUMN cohort_public_applications.payment_deadline IS 'Deadline for payment after approval (automated)';
COMMENT ON COLUMN cohort_public_applications.onboarding_link_sent_at IS 'When onboarding email was sent';
COMMENT ON COLUMN cohort_public_applications.password_created_at IS 'When student created their password';
COMMENT ON COLUMN cohort_public_applications.onboarding_token IS 'Secure token for account creation link';
COMMENT ON COLUMN cohorts.enrollment_fee IS 'One-time enrollment fee for cohort';
COMMENT ON COLUMN cohorts.payment_deadline_hours IS 'Hours allowed for payment after approval';

-- 7. Create function to auto-expire payments
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

-- 8. Create scheduled job (optional - requires pg_cron extension)
-- SELECT cron.schedule('expire-payments', '0 * * * *', 'SELECT expire_overdue_payments()');

COMMENT ON FUNCTION expire_overdue_payments IS 'Automatically reject applications with expired payment deadlines';
