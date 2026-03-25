-- Align contracts.status CHECK with Django Contract.STATUS_CHOICES (includes pending_payments).
-- Run against PostgreSQL, e.g. psql -f alter_contracts_status_pending_payments.sql

ALTER TABLE contracts DROP CONSTRAINT IF EXISTS contracts_status_check;

ALTER TABLE contracts ADD CONSTRAINT contracts_status_check CHECK (
  status IN (
    'proposal',
    'negotiation',
    'signed',
    'pending_payments',
    'active',
    'renewal',
    'terminated'
  )
);

COMMENT ON CONSTRAINT contracts_status_check ON contracts IS
  'Matches finance.models.Contract.STATUS_CHOICES';
