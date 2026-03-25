-- Institution contract fields: tier, billing cadence, curriculum blueprint (PostgreSQL)
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS institution_pricing_tier VARCHAR(30);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(20);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS institution_curriculum JSONB;
