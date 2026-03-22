-- Run in pgAdmin against your OCH database (PostgreSQL).
-- Adds mentor cohort fields, scholarship cohort link, reconciliation runs, marketplace escrow + commission ledger.

-- 1) Credits: optional cohort for scholarship tracking
ALTER TABLE credits
    ADD COLUMN IF NOT EXISTS cohort_id UUID NULL REFERENCES cohorts(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS credits_cohort_id_type_idx ON credits(cohort_id, type);

-- 2) Mentor payouts: cohort allocation + volunteer mode
ALTER TABLE mentor_payouts
    ADD COLUMN IF NOT EXISTS cohort_id UUID NULL REFERENCES cohorts(id) ON DELETE SET NULL;
ALTER TABLE mentor_payouts
    ADD COLUMN IF NOT EXISTS compensation_mode VARCHAR(20) NOT NULL DEFAULT 'paid';
ALTER TABLE mentor_payouts
    ADD COLUMN IF NOT EXISTS allocation_notes TEXT NOT NULL DEFAULT '';
ALTER TABLE mentor_payouts
    ADD COLUMN IF NOT EXISTS cohort_budget_share_percent DECIMAL(5,2) NULL;

-- Extend payout_method check for volunteer rows
ALTER TABLE mentor_payouts DROP CONSTRAINT IF EXISTS mentor_payouts_payout_method_check;
ALTER TABLE mentor_payouts ADD CONSTRAINT mentor_payouts_payout_method_check
    CHECK (payout_method IN ('bank_transfer', 'mobile_money', 'paypal', 'not_applicable'));

CREATE INDEX IF NOT EXISTS mentor_payouts_cohort_mode_idx ON mentor_payouts(cohort_id, compensation_mode);

-- 3) Reconciliation runs
CREATE TABLE IF NOT EXISTS reconciliation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    book_total DECIMAL(15,2) NOT NULL,
    bank_total DECIMAL(15,2) NOT NULL,
    difference DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_count INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    created_by_id BIGINT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS reconciliation_runs_period_idx ON reconciliation_runs(period_start, period_end);

-- 4) Marketplace escrow + commission ledger
CREATE TABLE IF NOT EXISTS marketplace_escrows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_application_id UUID NOT NULL REFERENCES marketplace_job_applications(id) ON DELETE CASCADE,
    gross_amount DECIMAL(12,2) NOT NULL CHECK (gross_amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    commission_rate_percent DECIMAL(5,2) NOT NULL DEFAULT 10.00 CHECK (commission_rate_percent >= 0 AND commission_rate_percent <= 100),
    commission_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    net_to_candidate DECIMAL(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'held' CHECK (status IN ('held', 'released', 'refunded', 'disputed')),
    paystack_reference VARCHAR(255) NOT NULL DEFAULT '',
    released_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS marketplace_escrows_status_created_idx ON marketplace_escrows(status, created_at);
CREATE INDEX IF NOT EXISTS marketplace_escrows_app_status_idx ON marketplace_escrows(job_application_id, status);

CREATE TABLE IF NOT EXISTS marketplace_commission_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    escrow_id UUID NOT NULL UNIQUE REFERENCES marketplace_escrows(id) ON DELETE CASCADE,
    job_application_id UUID NOT NULL REFERENCES marketplace_job_applications(id) ON DELETE CASCADE,
    gross_amount DECIMAL(12,2) NOT NULL,
    commission_amount DECIMAL(12,2) NOT NULL,
    net_to_candidate DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 5) revenue_streams may already exist; ensure it exists for analytics (from finance analytics)
-- Skip if you already ran analytics migrations.

COMMENT ON TABLE marketplace_escrows IS 'Placement fee escrow; commission deducted on release.';
COMMENT ON TABLE reconciliation_runs IS 'Book vs bank reconciliation snapshots.';
