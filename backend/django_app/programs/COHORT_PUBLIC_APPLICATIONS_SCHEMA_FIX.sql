-- Fix missing columns on cohort_public_applications table to match Django models.
-- Run this manually against your Postgres database (once).

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS reviewer_mentor_id bigint NULL;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS interview_mentor_id bigint NULL;

-- Optionally add foreign keys (safe but not strictly required for the app to work)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'cohort_public_applications_reviewer_mentor_fk'
    ) THEN
        ALTER TABLE cohort_public_applications
            ADD CONSTRAINT cohort_public_applications_reviewer_mentor_fk
            FOREIGN KEY (reviewer_mentor_id) REFERENCES users_user(id) DEFERRABLE INITIALLY DEFERRED;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'cohort_public_applications_interview_mentor_fk'
    ) THEN
        ALTER TABLE cohort_public_applications
            ADD CONSTRAINT cohort_public_applications_interview_mentor_fk
            FOREIGN KEY (interview_mentor_id) REFERENCES users_user(id) DEFERRABLE INITIALLY DEFERRED;
    END IF;
END$$;

