-- Add seat_cap to finance contracts (institution / employer seat allocation).
-- Run against the same database as Django, e.g. psql -f add_contract_seat_cap.sql

ALTER TABLE contracts
  ADD COLUMN IF NOT EXISTS seat_cap INTEGER NOT NULL DEFAULT 0;

COMMENT ON COLUMN contracts.seat_cap IS 'Allocated seat cap for enrollments (institution) or placements/pipeline (employer).';
