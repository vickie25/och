-- Finance module SQL schema
-- Creates all tables for wallet, credits, contracts, tax management, and enhanced financial operations

-- Wallets table
CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    balance DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (balance >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    last_transaction_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS wallets_user_id_unique ON wallets(user_id);
CREATE INDEX IF NOT EXISTS wallets_balance_idx ON wallets(balance);

-- Wallet transactions table
CREATE TABLE IF NOT EXISTS wallet_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    type VARCHAR(10) NOT NULL CHECK (type IN ('credit', 'debit')),
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    description TEXT NOT NULL,
    reference_type VARCHAR(20) NOT NULL CHECK (reference_type IN ('subscription', 'cohort', 'promotion', 'refund', 'manual', 'usage')),
    reference_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS wallet_transactions_wallet_type_idx ON wallet_transactions(wallet_id, type);
CREATE INDEX IF NOT EXISTS wallet_transactions_reference_idx ON wallet_transactions(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS wallet_transactions_created_at_idx ON wallet_transactions(created_at);

-- Credits table
CREATE TABLE IF NOT EXISTS credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('purchased', 'promotional', 'referral', 'scholarship')),
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    remaining DECIMAL(12,2) NOT NULL CHECK (remaining >= 0),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS credits_user_type_idx ON credits(user_id, type);
CREATE INDEX IF NOT EXISTS credits_expires_at_idx ON credits(expires_at);

CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('institution', 'employer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'proposal' CHECK (status IN ('proposal', 'negotiation', 'signed', 'active', 'renewal', 'terminated')),
    total_value DECIMAL(15,2) NOT NULL CHECK (total_value >= 0),
    payment_terms VARCHAR(100) NOT NULL DEFAULT 'Net 30',
    auto_renew BOOLEAN NOT NULL DEFAULT FALSE,
    renewal_notice_days INTEGER NOT NULL DEFAULT 60 CHECK (renewal_notice_days >= 1),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS contracts_organization_status_idx ON contracts(organization_id, status);
CREATE INDEX IF NOT EXISTS contracts_type_status_idx ON contracts(type, status);
CREATE INDEX IF NOT EXISTS contracts_dates_idx ON contracts(start_date, end_date);

-- Tax rates table
CREATE TABLE IF NOT EXISTS tax_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country VARCHAR(2) NOT NULL,
    region VARCHAR(100) NOT NULL DEFAULT '',
    rate DECIMAL(5,2) NOT NULL CHECK (rate >= 0 AND rate <= 100),
    type VARCHAR(20) NOT NULL CHECK (type IN ('VAT', 'GST', 'sales_tax')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    effective_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS tax_rates_location_type_unique ON tax_rates(country, region, type);
CREATE INDEX IF NOT EXISTS tax_rates_country_active_idx ON tax_rates(country, is_active);
CREATE INDEX IF NOT EXISTS tax_rates_effective_date_idx ON tax_rates(effective_date);

-- Mentor payouts table
CREATE TABLE IF NOT EXISTS mentor_payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL CHECK (amount >= 0),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'paid', 'rejected')),
    payout_method VARCHAR(20) NOT NULL CHECK (payout_method IN ('bank_transfer', 'mobile_money', 'paypal')),
    paystack_transfer_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS mentor_payouts_mentor_status_idx ON mentor_payouts(mentor_id, status);
CREATE INDEX IF NOT EXISTS mentor_payouts_period_idx ON mentor_payouts(period_start, period_end);
CREATE INDEX IF NOT EXISTS mentor_payouts_status_idx ON mentor_payouts(status);

-- Enhanced invoices table
CREATE TABLE IF NOT EXISTS finance_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    organization_id BIGINT REFERENCES organizations(id) ON DELETE CASCADE,
    contract_id UUID REFERENCES contracts(id) ON DELETE SET NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('subscription', 'institution', 'employer', 'cohort', 'contract')),
    amount DECIMAL(15,2) NOT NULL CHECK (amount >= 0),
    tax DECIMAL(15,2) NOT NULL DEFAULT 0 CHECK (tax >= 0),
    total DECIMAL(15,2) NOT NULL CHECK (total >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'void')),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    paid_date TIMESTAMP WITH TIME ZONE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT finance_invoices_client_check CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS finance_invoices_user_status_idx ON finance_invoices(user_id, status);
CREATE INDEX IF NOT EXISTS finance_invoices_org_status_idx ON finance_invoices(organization_id, status);
CREATE INDEX IF NOT EXISTS finance_invoices_type_status_idx ON finance_invoices(type, status);
CREATE INDEX IF NOT EXISTS finance_invoices_due_date_idx ON finance_invoices(due_date);
CREATE INDEX IF NOT EXISTS finance_invoices_invoice_number_idx ON finance_invoices(invoice_number);

-- Enhanced payments table
CREATE TABLE IF NOT EXISTS finance_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES finance_invoices(id) ON DELETE CASCADE,
    amount DECIMAL(15,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed')),
    paystack_reference VARCHAR(255),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('card', 'mobile_money', 'bank_transfer')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS finance_payments_invoice_status_idx ON finance_payments(invoice_id, status);
CREATE INDEX IF NOT EXISTS finance_payments_paystack_ref_idx ON finance_payments(paystack_reference);
CREATE INDEX IF NOT EXISTS finance_payments_status_idx ON finance_payments(status);

-- Add wallet_id foreign key to users table (optional, for specification compliance)
-- ALTER TABLE users ADD COLUMN wallet_id UUID REFERENCES wallets(id) ON DELETE SET NULL;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_wallets_updated_at BEFORE UPDATE ON wallets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_credits_updated_at BEFORE UPDATE ON credits FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_contracts_updated_at BEFORE UPDATE ON contracts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mentor_payouts_updated_at BEFORE UPDATE ON mentor_payouts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_finance_invoices_updated_at BEFORE UPDATE ON finance_invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_finance_payments_updated_at BEFORE UPDATE ON finance_payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default tax rates for common regions
INSERT INTO tax_rates (country, region, rate, type, is_active) VALUES
('US', '', 8.25, 'sales_tax', true),
('GB', '', 20.00, 'VAT', true),
('KE', '', 16.00, 'VAT', true),
('NG', '', 7.50, 'VAT', true),
('ZA', '', 15.00, 'VAT', true),
('CA', '', 13.00, 'GST', true),
('AU', '', 10.00, 'GST', true)
ON CONFLICT (country, region, type) DO NOTHING;

-- Create wallets for existing users
INSERT INTO wallets (user_id, balance, currency)
SELECT id, 0, 'USD' FROM users 
WHERE id NOT IN (SELECT user_id FROM wallets WHERE user_id IS NOT NULL)
ON CONFLICT (user_id) DO NOTHING;