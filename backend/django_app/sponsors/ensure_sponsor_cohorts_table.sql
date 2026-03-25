-- =============================================================================
-- sponsor_cohorts — matches sponsors.models.SponsorCohort (organization FK).
-- Fixes: Organization DELETE failing with "relation sponsor_cohorts does not exist"
--        when Django cascades to sponsor_cohorts.
--
-- Run against the SAME database Django uses, e.g.:
--   psql "$DATABASE_URL" -f ensure_sponsor_cohorts_table.sql
--   psql -h localhost -U postgres -d your_db -f ensure_sponsor_cohorts_table.sql
--
-- Prerequisites:
--   - Table `organizations` exists with column `id` (BIGINT), matching Django
--     organizations_organization / db_table `organizations`.
-- PostgreSQL 13+ recommended (uses gen_random_uuid()).
-- =============================================================================

CREATE TABLE IF NOT EXISTS sponsor_cohorts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    track_slug VARCHAR(50) NOT NULL,

    target_size INTEGER NOT NULL DEFAULT 100,
    students_enrolled INTEGER NOT NULL DEFAULT 0,

    start_date DATE NULL,
    expected_graduation_date DATE NULL,

    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    completion_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,

    target_completion_date DATE NULL,
    budget_allocated NUMERIC(12, 2) NOT NULL DEFAULT 0,
    ai_interventions_count INTEGER NOT NULL DEFAULT 0,
    placement_goal INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT sponsor_cohorts_org_name_uniq UNIQUE (organization_id, name)
);

CREATE INDEX IF NOT EXISTS sponsor_cohorts_org_active_idx
    ON sponsor_cohorts (organization_id, is_active);
CREATE INDEX IF NOT EXISTS sponsor_cohorts_org_status_idx
    ON sponsor_cohorts (organization_id, status);
CREATE INDEX IF NOT EXISTS sponsor_cohorts_track_slug_idx
    ON sponsor_cohorts (track_slug);
CREATE INDEX IF NOT EXISTS sponsor_cohorts_status_idx
    ON sponsor_cohorts (status);
CREATE INDEX IF NOT EXISTS sponsor_cohorts_start_date_idx
    ON sponsor_cohorts (start_date);
CREATE INDEX IF NOT EXISTS sponsor_cohorts_target_completion_idx
    ON sponsor_cohorts (target_completion_date);

-- If you already had a legacy sponsor_cohorts table with sponsor_id and no
-- organization_id, do NOT run this file blindly — back up, then either migrate
-- data or drop the old table if empty. This script only creates the table when
-- it is missing (IF NOT EXISTS).
