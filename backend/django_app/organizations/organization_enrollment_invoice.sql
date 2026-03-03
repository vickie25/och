-- =============================================================================
-- Organization enrollment & invoicing (run manually in PostgreSQL)
-- 1) Add contact fields to organizations
-- 2) Create organization_enrollment_invoices table
-- =============================================================================

-- 1) Add contact fields to organizations (for billing/invoice when enrolling from org)
ALTER TABLE organizations
  ADD COLUMN IF NOT EXISTS contact_person_name VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS contact_email VARCHAR(254) NULL,
  ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50) NULL;

COMMENT ON COLUMN organizations.contact_person_name IS 'Primary contact for billing when students are enrolled from this organization';
COMMENT ON COLUMN organizations.contact_email IS 'Email to send invoices to';
COMMENT ON COLUMN organizations.contact_phone IS 'Contact phone for the organization';

-- 2) Organization enrollment invoices (one per batch of students enrolled from an org)
CREATE TABLE IF NOT EXISTS organization_enrollment_invoices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  contact_person_name VARCHAR(255) NOT NULL,
  contact_email VARCHAR(254) NOT NULL,
  contact_phone VARCHAR(50) NULL,
  line_items JSONB NOT NULL DEFAULT '[]',
  total_amount_kes DECIMAL(12, 2) NOT NULL DEFAULT 0,
  currency VARCHAR(3) NOT NULL DEFAULT 'KES',
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'waived')),
  payment_link TEXT NULL,
  paystack_reference VARCHAR(100) NULL,
  invoice_number VARCHAR(50) NULL,
  created_by_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sent_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS idx_org_enrollment_invoices_org ON organization_enrollment_invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_org_enrollment_invoices_status ON organization_enrollment_invoices(status);
CREATE INDEX IF NOT EXISTS idx_org_enrollment_invoices_created ON organization_enrollment_invoices(created_at DESC);

COMMENT ON TABLE organization_enrollment_invoices IS 'Invoices sent to organizations when director enrolls students from that org; Finance can track status; payment via Paystack link';
