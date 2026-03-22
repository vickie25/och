-- COHORT_PUBLIC_APPLICATIONS_SCHEMA_FULL.sql
-- 
-- Bring the cohort_public_applications table in line with the current
-- Django CohortPublicApplication model.
--
-- Run this once per environment (e.g., production) against the same
-- database your Django app is using.

-- Core JSON + status fields (usually already present, but safe to add)
ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS form_data jsonb DEFAULT '{}'::jsonb;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS status varchar(20) DEFAULT 'pending';

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS notes text;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS enrollment_status varchar(30) DEFAULT 'none';

-- Enrollment FK pointer (may already exist in some DBs)
ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS enrollment_id uuid;

-- Review workflow fields
ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS reviewer_mentor_id bigint;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS review_score numeric(5,2);

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS review_graded_at timestamp with time zone;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS review_status varchar(30);

-- Interview workflow fields
ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS interview_mentor_id bigint;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS interview_score numeric(5,2);

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS interview_graded_at timestamp with time zone;

ALTER TABLE cohort_public_applications
    ADD COLUMN IF NOT EXISTS interview_status varchar(30);

