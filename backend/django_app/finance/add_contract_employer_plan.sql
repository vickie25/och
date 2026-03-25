-- Add employer_plan to contracts (employer commercial tier selection).
-- Run against the same database as Django, e.g. psql -f add_contract_employer_plan.sql

ALTER TABLE contracts
  ADD COLUMN IF NOT EXISTS employer_plan VARCHAR(20) NULL;

COMMENT ON COLUMN contracts.employer_plan IS 'Employer tier: starter, growth, enterprise, custom.';
