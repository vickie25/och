-- Enhanced Billing System Migration - Academic Discounts and Promotional Codes
-- This migration adds all missing features for Stream A implementation

BEGIN;

-- Create Academic Discounts table
CREATE TABLE academic_discounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    verification_method VARCHAR(20) NOT NULL CHECK (verification_method IN ('edu_email', 'manual', 'student_id', 'faculty_id')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'rejected', 'expired')),
    
    -- Verification details
    email_domain VARCHAR(255) DEFAULT '',
    institution_name VARCHAR(255) DEFAULT '',
    student_id VARCHAR(100) DEFAULT '',
    verification_document VARCHAR(255) DEFAULT '',
    
    -- Discount details
    discount_rate DECIMAL(5,2) NOT NULL DEFAULT 30.00,
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Verification tracking
    verified_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    rejection_reason TEXT DEFAULT '',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id)
);

CREATE INDEX idx_academic_discounts_user ON academic_discounts(user_id);
CREATE INDEX idx_academic_discounts_status ON academic_discounts(status);
CREATE INDEX idx_academic_discounts_email_domain ON academic_discounts(email_domain);
CREATE INDEX idx_academic_discounts_expires_at ON academic_discounts(expires_at);

-- Create Promotional Codes table
CREATE TABLE promotional_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT DEFAULT '',
    
    -- Discount configuration
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed', 'free_trial', 'free_months')),
    discount_value DECIMAL(10,2) NOT NULL,
    
    -- Validity period
    valid_from TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Usage limits
    max_redemptions INTEGER,
    max_redemptions_per_user INTEGER DEFAULT 1,
    current_redemptions INTEGER DEFAULT 0,
    
    -- Plan restrictions
    minimum_plan_value DECIMAL(10,2),
    
    -- User restrictions
    new_users_only BOOLEAN DEFAULT FALSE,
    academic_users_only BOOLEAN DEFAULT FALSE,
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'expired', 'exhausted')),
    
    created_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_promotional_codes_code ON promotional_codes(code);
CREATE INDEX idx_promotional_codes_status ON promotional_codes(status);
CREATE INDEX idx_promotional_codes_validity ON promotional_codes(valid_from, valid_until);
CREATE INDEX idx_promotional_codes_discount_type ON promotional_codes(discount_type);

-- Create Promo Code Redemptions table
CREATE TABLE promo_code_redemptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promo_code_id UUID NOT NULL REFERENCES promotional_codes(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES user_subscriptions(id) ON DELETE CASCADE,
    
    -- Redemption details
    discount_applied DECIMAL(10,2) NOT NULL,
    original_amount DECIMAL(10,2) NOT NULL,
    final_amount DECIMAL(10,2) NOT NULL,
    
    redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(promo_code_id, user_id, subscription_id)
);

CREATE INDEX IF NOT EXISTS idx_promo_redemptions_code ON promo_code_redemptions(promo_code_id);
CREATE INDEX IF NOT EXISTS idx_promo_redemptions_user ON promo_code_redemptions(user_id);
CREATE INDEX IF NOT EXISTS idx_promo_redemptions_date ON promo_code_redemptions(redeemed_at);

-- Create Enhanced Subscription Plans table
CREATE TABLE enhanced_subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('basic', 'pro', 'premium', 'enterprise')),
    description TEXT DEFAULT '',
    
    -- Pricing
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_cycle VARCHAR(20) NOT NULL CHECK (billing_cycle IN ('monthly', 'annual', 'quarterly')),
    
    -- Trial configuration
    trial_days INTEGER DEFAULT 0,
    requires_credit_card BOOLEAN DEFAULT FALSE,
    
    -- Grace period configuration
    grace_period_days INTEGER DEFAULT 3,
    
    -- Features
    features JSONB DEFAULT '[]',
    feature_limits JSONB DEFAULT '{}',
    
    -- Plan status
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_enhanced_plans_type ON enhanced_subscription_plans(plan_type);
CREATE INDEX idx_enhanced_plans_cycle ON enhanced_subscription_plans(billing_cycle);
CREATE INDEX idx_enhanced_plans_active ON enhanced_subscription_plans(is_active);
CREATE INDEX idx_enhanced_plans_sort ON enhanced_subscription_plans(sort_order);

-- Create Enhanced Subscriptions table
CREATE TABLE IF NOT EXISTS enhanced_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES enhanced_subscription_plans(id) ON DELETE RESTRICT,
    
    -- Subscription status
    status VARCHAR(20) DEFAULT 'trial' CHECK (status IN ('trial', 'active', 'past_due', 'suspended', 'canceled', 'expired')),
    dunning_status VARCHAR(20) DEFAULT 'none' CHECK (dunning_status IN ('none', 'soft_decline', 'hard_decline', 'final_notice')),
    
    -- Billing periods
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    next_billing_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Trial period
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    trial_converted_at TIMESTAMP WITH TIME ZONE,
    
    -- Grace period
    grace_period_start TIMESTAMP WITH TIME ZONE,
    grace_period_end TIMESTAMP WITH TIME ZONE,
    
    -- Pricing and discounts
    base_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    final_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Applied discounts
    academic_discount_applied BOOLEAN DEFAULT FALSE,
    promo_code_applied_id UUID REFERENCES promotional_codes(id) ON DELETE SET NULL,
    
    -- Billing tracking
    amount_due DECIMAL(10,2) DEFAULT 0,
    last_payment_attempt TIMESTAMP WITH TIME ZONE,
    payment_retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    canceled_at TIMESTAMP WITH TIME ZONE
);

-- Ensure key columns exist even if table was created earlier
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS next_billing_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS grace_period_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS grace_period_end TIMESTAMP WITH TIME ZONE;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS dunning_status VARCHAR(20) DEFAULT 'none';
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS plan_id UUID REFERENCES enhanced_subscription_plans(id) ON DELETE RESTRICT;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS promo_code_applied_id UUID REFERENCES promotional_codes(id) ON DELETE SET NULL;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS base_amount DECIMAL(10,2) NOT NULL DEFAULT 0;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10,2) DEFAULT 0;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS final_amount DECIMAL(10,2) NOT NULL DEFAULT 0;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS academic_discount_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS amount_due DECIMAL(10,2) DEFAULT 0;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS last_payment_attempt TIMESTAMP WITH TIME ZONE;
ALTER TABLE enhanced_subscriptions
    ADD COLUMN IF NOT EXISTS payment_retry_count INTEGER DEFAULT 0;

CREATE INDEX idx_enhanced_subs_user ON enhanced_subscriptions(user_id);
CREATE INDEX idx_enhanced_subs_status ON enhanced_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_enhanced_subs_billing_date ON enhanced_subscriptions(next_billing_date);
CREATE INDEX IF NOT EXISTS idx_enhanced_subs_trial_end ON enhanced_subscriptions(trial_end);
CREATE INDEX IF NOT EXISTS idx_enhanced_subs_grace_end ON enhanced_subscriptions(grace_period_end);
CREATE INDEX IF NOT EXISTS idx_enhanced_subs_dunning ON enhanced_subscriptions(dunning_status);

-- Create Promotional Code Plan Restrictions table (many-to-many)
CREATE TABLE promotional_code_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotional_code_id UUID NOT NULL REFERENCES promotional_codes(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES enhanced_subscription_plans(id) ON DELETE CASCADE,
    UNIQUE(promotional_code_id, plan_id)
);

CREATE INDEX idx_promo_code_plans_code ON promotional_code_plans(promotional_code_id);
CREATE INDEX idx_promo_code_plans_plan ON promotional_code_plans(plan_id);

-- Add enhanced trial configurations to existing subscription plans
ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS trial_days INTEGER DEFAULT 0;
ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS requires_credit_card BOOLEAN DEFAULT FALSE;
ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS grace_period_days INTEGER DEFAULT 3;
ALTER TABLE subscription_plans ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR(20) DEFAULT 'monthly';

-- Update existing plans with trial configurations
UPDATE subscription_plans SET 
    trial_days = CASE 
        WHEN LOWER(name) LIKE '%basic%' THEN 7
        WHEN LOWER(name) LIKE '%pro%' THEN 14
        WHEN LOWER(name) LIKE '%premium%' THEN 7
        ELSE 7
    END,
    requires_credit_card = CASE 
        WHEN LOWER(name) LIKE '%premium%' THEN TRUE
        ELSE FALSE
    END,
    grace_period_days = CASE 
        WHEN billing_cycle = 'annual' THEN 7
        WHEN billing_cycle = 'quarterly' THEN 5
        ELSE 3
    END;

-- Add enhanced fields to existing subscriptions
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS trial_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS trial_end TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS grace_period_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS grace_period_end TIMESTAMP WITH TIME ZONE;
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS academic_discount_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS promo_code_applied_id UUID REFERENCES promotional_codes(id) ON DELETE SET NULL;
ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS dunning_status VARCHAR(20) DEFAULT 'none';

-- Insert sample promotional codes
INSERT INTO promotional_codes (code, name, description, discount_type, discount_value, valid_from, valid_until, max_redemptions, new_users_only) VALUES
('WELCOME20', 'Welcome Discount', '20% off for new users', 'percentage', 20.00, NOW(), NOW() + INTERVAL '1 year', 1000, TRUE),
('STUDENT50', 'Student Special', '50% off first month for students', 'percentage', 50.00, NOW(), NOW() + INTERVAL '6 months', 500, FALSE),
('SAVE10', 'Save $10', '$10 off any plan', 'fixed', 10.00, NOW(), NOW() + INTERVAL '3 months', 200, FALSE),
('ACADEMIC30', 'Academic Discount', '30% off for academic users', 'percentage', 30.00, NOW(), NOW() + INTERVAL '1 year', NULL, FALSE);

-- Update promotional codes for academic users only
UPDATE promotional_codes SET academic_users_only = TRUE WHERE code IN ('STUDENT50', 'ACADEMIC30');

-- Insert enhanced subscription plans
INSERT INTO enhanced_subscription_plans (name, plan_type, description, price, billing_cycle, trial_days, requires_credit_card, grace_period_days, features, sort_order) VALUES
('Basic Monthly', 'basic', 'Essential features for getting started', 9.99, 'monthly', 7, FALSE, 3, '["Basic curriculum access", "Community support", "Progress tracking"]', 1),
('Pro Monthly', 'pro', 'Advanced features for serious learners', 19.99, 'monthly', 14, FALSE, 3, '["Full curriculum access", "1-on-1 mentoring", "Advanced analytics", "Priority support"]', 2),
('Premium Monthly', 'premium', 'Complete access with premium features', 39.99, 'monthly', 7, TRUE, 3, '["Everything in Pro", "Unlimited mentoring", "Custom learning paths", "Career coaching"]', 3),
('Basic Annual', 'basic', 'Essential features - annual billing', 99.99, 'annual', 7, FALSE, 7, '["Basic curriculum access", "Community support", "Progress tracking"]', 4),
('Pro Annual', 'pro', 'Advanced features - annual billing', 199.99, 'annual', 14, FALSE, 7, '["Full curriculum access", "1-on-1 mentoring", "Advanced analytics", "Priority support"]', 5),
('Premium Annual', 'premium', 'Complete access - annual billing', 399.99, 'annual', 7, TRUE, 7, '["Everything in Pro", "Unlimited mentoring", "Custom learning paths", "Career coaching"]', 6);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_academic_discounts_updated_at BEFORE UPDATE ON academic_discounts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_promotional_codes_updated_at BEFORE UPDATE ON promotional_codes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_enhanced_plans_updated_at BEFORE UPDATE ON enhanced_subscription_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_enhanced_subs_updated_at BEFORE UPDATE ON enhanced_subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to automatically check academic eligibility based on email domain
CREATE OR REPLACE FUNCTION check_academic_email_domain(email_address TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Common academic email domains
    RETURN email_address ~* '\.(edu|ac\.uk|edu\.au|ac\.in|edu\.sg|ac\.jp|edu\.cn|uni-.*\.de|.*\.university\..*|.*\.college\..*|.*\.school\..*)$';
END;
$$ LANGUAGE plpgsql;

-- Create function to auto-create academic discount for .edu emails
CREATE OR REPLACE FUNCTION auto_create_academic_discount()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if user has .edu email and doesn't already have academic discount
    IF check_academic_email_domain(NEW.email) AND NOT EXISTS (
        SELECT 1 FROM academic_discounts WHERE user_id = NEW.id
    ) THEN
        INSERT INTO academic_discounts (
            user_id, 
            verification_method, 
            status, 
            email_domain,
            verified_at,
            expires_at
        ) VALUES (
            NEW.id,
            'edu_email',
            'verified',
            SUBSTRING(NEW.email FROM '@(.*)$'),
            NOW(),
            NOW() + INTERVAL '1 year'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto academic discount creation
CREATE TRIGGER trigger_auto_academic_discount
    AFTER INSERT ON users
    FOR EACH ROW
    EXECUTE FUNCTION auto_create_academic_discount();

-- Create view for subscription analytics with discounts
CREATE OR REPLACE VIEW subscription_analytics_enhanced AS
SELECT 
    s.id,
    s.user_id,
    u.email,
    p.name as plan_name,
    p.plan_type,
    s.status,
    s.base_amount,
    s.discount_amount,
    s.final_amount,
    s.academic_discount_applied,
    pc.code as promo_code,
    s.trial_start,
    s.trial_end,
    s.grace_period_start,
    s.grace_period_end,
    s.dunning_status,
    CASE 
        WHEN s.trial_start IS NOT NULL AND s.trial_end > NOW() THEN 'trial_active'
        WHEN s.grace_period_start IS NOT NULL AND s.grace_period_end > NOW() THEN 'grace_period'
        ELSE s.status
    END as effective_status,
    CASE 
        WHEN s.trial_end IS NOT NULL AND s.trial_end > NOW() THEN 
            EXTRACT(DAYS FROM s.trial_end - NOW())
        ELSE 0
    END as trial_days_remaining,
    CASE 
        WHEN s.grace_period_end IS NOT NULL AND s.grace_period_end > NOW() THEN 
            EXTRACT(DAYS FROM s.grace_period_end - NOW())
        ELSE 0
    END as grace_days_remaining
FROM enhanced_subscriptions s
JOIN users u ON s.user_id = u.id
JOIN enhanced_subscription_plans p ON s.plan_id = p.id
LEFT JOIN promotional_codes pc ON s.promo_code_applied_id = pc.id;

COMMIT;