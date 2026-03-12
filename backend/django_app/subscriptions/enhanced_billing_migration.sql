-- Enhanced Billing Engine Migration
-- Adds comprehensive billing engine tables with full functional requirements

-- Subscription Plan Versions (Plan Versioning System)
CREATE TABLE IF NOT EXISTS subscription_plan_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id VARCHAR(50) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    name VARCHAR(100) NOT NULL,
    price_monthly DECIMAL(10,2) NOT NULL CHECK (price_monthly >= 0),
    price_annual DECIMAL(10,2) CHECK (price_annual >= 0),
    billing_cycles JSONB DEFAULT '[]'::jsonb,
    trial_days INTEGER NOT NULL DEFAULT 14 CHECK (trial_days >= 0 AND trial_days <= 365),
    tier_access JSONB DEFAULT '[]'::jsonb,
    track_access JSONB DEFAULT '[]'::jsonb,
    feature_flags JSONB DEFAULT '{}'::jsonb,
    mentorship_credits INTEGER NOT NULL DEFAULT 0 CHECK (mentorship_credits >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'deprecated', 'archived')),
    regional_pricing JSONB DEFAULT '{}'::jsonb,
    created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    effective_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(plan_id, version)
);

CREATE INDEX IF NOT EXISTS subscription_plan_versions_plan_status_idx ON subscription_plan_versions(plan_id, status);
CREATE INDEX IF NOT EXISTS subscription_plan_versions_status_effective_idx ON subscription_plan_versions(status, effective_date);

-- Enhanced Subscriptions (Complete State Machine)
CREATE TABLE IF NOT EXISTS enhanced_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    plan_version_id UUID NOT NULL REFERENCES subscription_plan_versions(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'TRIAL' CHECK (status IN ('TRIAL', 'ACTIVE', 'PAST_DUE', 'SUSPENDED', 'CANCELED', 'EXPIRED')),
    billing_cycle VARCHAR(10) NOT NULL DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'annual')),
    cycle_anchor_day INTEGER NOT NULL CHECK (cycle_anchor_day >= 1 AND cycle_anchor_day <= 31),
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    cancellation_type VARCHAR(20) CHECK (cancellation_type IN ('immediate', 'end_of_period')),
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
    suspended_at TIMESTAMP WITH TIME ZONE,
    reactivation_window_end TIMESTAMP WITH TIME ZONE,
    stripe_subscription_id VARCHAR(255) UNIQUE,
    paystack_subscription_code VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS enhanced_subscriptions_user_status_idx ON enhanced_subscriptions(user_id, status);
CREATE INDEX IF NOT EXISTS enhanced_subscriptions_status_period_end_idx ON enhanced_subscriptions(status, current_period_end);
CREATE INDEX IF NOT EXISTS enhanced_subscriptions_cycle_anchor_idx ON enhanced_subscriptions(cycle_anchor_day);
CREATE INDEX IF NOT EXISTS enhanced_subscriptions_reactivation_window_idx ON enhanced_subscriptions(reactivation_window_end);

-- Billing Periods (Audit and Reconciliation)
CREATE TABLE IF NOT EXISTS billing_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES enhanced_subscriptions(id) ON DELETE CASCADE,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'upcoming' CHECK (status IN ('upcoming', 'current', 'completed', 'failed')),
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_attempted_at TIMESTAMP WITH TIME ZONE,
    payment_completed_at TIMESTAMP WITH TIME ZONE,
    payment_failed_at TIMESTAMP WITH TIME ZONE,
    invoice_id UUID,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS billing_periods_subscription_status_idx ON billing_periods(subscription_id, status);
CREATE INDEX IF NOT EXISTS billing_periods_period_dates_idx ON billing_periods(period_start, period_end);
CREATE INDEX IF NOT EXISTS billing_periods_payment_attempted_idx ON billing_periods(payment_attempted_at);

-- Dunning Sequences (Automated Retry Management)
CREATE TABLE IF NOT EXISTS dunning_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES enhanced_subscriptions(id) ON DELETE CASCADE,
    billing_period_id UUID NOT NULL REFERENCES billing_periods(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'exhausted', 'canceled')),
    retry_schedule JSONB NOT NULL DEFAULT '[1, 3, 7]'::jsonb,
    current_attempt INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    grace_period_days INTEGER NOT NULL DEFAULT 3,
    grace_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    next_retry_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_notification_sent TIMESTAMP WITH TIME ZONE,
    suspension_warning_sent BOOLEAN NOT NULL DEFAULT FALSE,
    final_warning_sent BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS dunning_sequences_subscription_status_idx ON dunning_sequences(subscription_id, status);
CREATE INDEX IF NOT EXISTS dunning_sequences_next_retry_status_idx ON dunning_sequences(next_retry_at, status);
CREATE INDEX IF NOT EXISTS dunning_sequences_grace_period_idx ON dunning_sequences(grace_period_end);

-- Subscription Changes (Complete Audit Trail)
CREATE TABLE IF NOT EXISTS subscription_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES enhanced_subscriptions(id) ON DELETE CASCADE,
    change_type VARCHAR(30) NOT NULL CHECK (change_type IN ('plan_change', 'status_change', 'billing_cycle_change', 'cancellation', 'reactivation', 'trial_conversion', 'proration_adjustment')),
    old_value TEXT,
    new_value TEXT,
    proration_credit DECIMAL(10,2) CHECK (proration_credit >= 0),
    proration_charge DECIMAL(10,2) CHECK (proration_charge >= 0),
    net_proration DECIMAL(10,2),
    reason VARCHAR(30) NOT NULL CHECK (reason IN ('user_initiated', 'admin_initiated', 'system_initiated', 'payment_failure', 'trial_expiration', 'dunning_exhausted')),
    description TEXT NOT NULL,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS subscription_changes_subscription_type_idx ON subscription_changes(subscription_id, change_type);
CREATE INDEX IF NOT EXISTS subscription_changes_created_at_idx ON subscription_changes(created_at);
CREATE INDEX IF NOT EXISTS subscription_changes_reason_idx ON subscription_changes(reason);

-- Proration Credits (Credit Management)
CREATE TABLE IF NOT EXISTS proration_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES enhanced_subscriptions(id) ON DELETE CASCADE,
    subscription_change_id UUID NOT NULL UNIQUE REFERENCES subscription_changes(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'applied', 'carried_forward', 'refunded')),
    applied_to_invoice_id UUID,
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS proration_credits_subscription_status_idx ON proration_credits(subscription_id, status);
CREATE INDEX IF NOT EXISTS proration_credits_expires_at_idx ON proration_credits(expires_at);

-- Enhanced Subscription Invoices
CREATE TABLE IF NOT EXISTS enhanced_subscription_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES enhanced_subscriptions(id) ON DELETE CASCADE,
    billing_period_id UUID NOT NULL UNIQUE REFERENCES billing_periods(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'void')),
    subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
    discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    credit_applied DECIMAL(10,2) NOT NULL DEFAULT 0 CHECK (credit_applied >= 0),
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    invoice_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    paid_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    line_items JSONB NOT NULL DEFAULT '[]'::jsonb,
    pdf_url TEXT,
    pdf_generated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS enhanced_subscription_invoices_subscription_status_idx ON enhanced_subscription_invoices(subscription_id, status);
CREATE INDEX IF NOT EXISTS enhanced_subscription_invoices_invoice_date_idx ON enhanced_subscription_invoices(invoice_date);
CREATE INDEX IF NOT EXISTS enhanced_subscription_invoices_due_date_idx ON enhanced_subscription_invoices(due_date);
CREATE INDEX IF NOT EXISTS enhanced_subscription_invoices_status_idx ON enhanced_subscription_invoices(status);

-- Add foreign key constraint to billing_periods after invoice table is created
ALTER TABLE billing_periods ADD CONSTRAINT billing_periods_invoice_fk 
    FOREIGN KEY (invoice_id) REFERENCES enhanced_subscription_invoices(id) ON DELETE SET NULL;

-- Add foreign key constraint to proration_credits after invoice table is created
ALTER TABLE proration_credits ADD CONSTRAINT proration_credits_invoice_fk
    FOREIGN KEY (applied_to_invoice_id) REFERENCES enhanced_subscription_invoices(id) ON DELETE SET NULL;

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_enhanced_subscriptions_updated_at 
    BEFORE UPDATE ON enhanced_subscriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_billing_periods_updated_at 
    BEFORE UPDATE ON billing_periods 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_enhanced_subscription_invoices_updated_at 
    BEFORE UPDATE ON enhanced_subscription_invoices 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default plan versions for existing plans
INSERT INTO subscription_plan_versions (plan_id, version, name, price_monthly, price_annual, billing_cycles, trial_days, tier_access, track_access, feature_flags, mentorship_credits, status, created_by)
SELECT 
    'free' as plan_id,
    1 as version,
    'Free Tier' as name,
    0.00 as price_monthly,
    0.00 as price_annual,
    '["monthly"]'::jsonb as billing_cycles,
    14 as trial_days,
    '["beginner"]'::jsonb as tier_access,
    '["defender"]'::jsonb as track_access,
    '{"curriculum_read": true, "profiler_basic": true}'::jsonb as feature_flags,
    0 as mentorship_credits,
    'active' as status,
    (SELECT id FROM users WHERE is_superuser = true LIMIT 1) as created_by
WHERE NOT EXISTS (SELECT 1 FROM subscription_plan_versions WHERE plan_id = 'free');

INSERT INTO subscription_plan_versions (plan_id, version, name, price_monthly, price_annual, billing_cycles, trial_days, tier_access, track_access, feature_flags, mentorship_credits, status, created_by)
SELECT 
    'starter' as plan_id,
    1 as version,
    'Starter Tier' as name,
    3.00 as price_monthly,
    30.00 as price_annual,
    '["monthly", "annual"]'::jsonb as billing_cycles,
    14 as trial_days,
    '["beginner", "intermediate"]'::jsonb as tier_access,
    '["defender", "grc"]'::jsonb as track_access,
    '{"curriculum_read": true, "profiler_full": true, "missions": true, "ai_coach": true, "portfolio": true}'::jsonb as feature_flags,
    2 as mentorship_credits,
    'active' as status,
    (SELECT id FROM users WHERE is_superuser = true LIMIT 1) as created_by
WHERE NOT EXISTS (SELECT 1 FROM subscription_plan_versions WHERE plan_id = 'starter');

INSERT INTO subscription_plan_versions (plan_id, version, name, price_monthly, price_annual, billing_cycles, trial_days, tier_access, track_access, feature_flags, mentorship_credits, status, created_by)
SELECT 
    'premium' as plan_id,
    1 as version,
    'Premium Tier' as name,
    7.00 as price_monthly,
    70.00 as price_annual,
    '["monthly", "annual"]'::jsonb as billing_cycles,
    14 as trial_days,
    '["beginner", "intermediate", "advanced", "mastery"]'::jsonb as tier_access,
    '["defender", "grc", "innovation", "leadership", "offensive"]'::jsonb as track_access,
    '{"curriculum_read": true, "profiler_full": true, "missions": true, "ai_coach": true, "portfolio": true, "talentscope": true, "mentorship": true, "marketplace": true}'::jsonb as feature_flags,
    5 as mentorship_credits,
    'active' as status,
    (SELECT id FROM users WHERE is_superuser = true LIMIT 1) as created_by
WHERE NOT EXISTS (SELECT 1 FROM subscription_plan_versions WHERE plan_id = 'premium');

-- Add comments for documentation
COMMENT ON TABLE subscription_plan_versions IS 'Plan versioning system - when plans are modified, new versions are created while existing customers remain on old versions';
COMMENT ON TABLE enhanced_subscriptions IS 'Complete subscription lifecycle state machine with TRIAL->ACTIVE->PAST_DUE->SUSPENDED->EXPIRED transitions';
COMMENT ON TABLE billing_periods IS 'Billing period tracking for audit and reconciliation with period_start, period_end, status, invoice_id';
COMMENT ON TABLE dunning_sequences IS 'Automated retry sequence with Day 1, 3, 7 retries and grace period management';
COMMENT ON TABLE subscription_changes IS 'Complete audit trail for all subscription changes with proration tracking';
COMMENT ON TABLE proration_credits IS 'Proration credit management for mid-cycle plan changes with credit application tracking';
COMMENT ON TABLE enhanced_subscription_invoices IS 'Enhanced invoice generation with line items, tax calculation, and credit application';

-- Grant permissions (adjust as needed for your user roles)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;