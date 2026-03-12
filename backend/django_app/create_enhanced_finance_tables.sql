-- Enhanced Finance module SQL schema
-- Creates all tables for security, compliance, analytics, and automation

-- Audit logs table for immutable audit trail
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id) ON DELETE RESTRICT,
    user_email VARCHAR(254) NOT NULL,
    user_ip INET,
    user_agent TEXT,
    action VARCHAR(20) NOT NULL CHECK (action IN ('create', 'update', 'delete', 'payment', 'refund', 'transfer', 'login', 'access')),
    entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('wallet', 'transaction', 'invoice', 'payment', 'contract', 'credit', 'user', 'subscription')),
    entity_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    session_id VARCHAR(255),
    old_values TEXT, -- Encrypted JSON
    new_values TEXT, -- Encrypted JSON
    description TEXT NOT NULL,
    risk_level VARCHAR(10) NOT NULL DEFAULT 'low' CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    retention_until TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() + INTERVAL '7 years'),
    is_pci_relevant BOOLEAN NOT NULL DEFAULT FALSE,
    is_gdpr_relevant BOOLEAN NOT NULL DEFAULT FALSE,
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS audit_logs_timestamp_entity_idx ON audit_logs(timestamp, entity_type);
CREATE INDEX IF NOT EXISTS audit_logs_user_action_idx ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS audit_logs_entity_idx ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS audit_logs_risk_timestamp_idx ON audit_logs(risk_level, timestamp);
CREATE INDEX IF NOT EXISTS audit_logs_retention_idx ON audit_logs(retention_until);

-- Security events table
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(30) NOT NULL CHECK (event_type IN ('failed_login', 'suspicious_transaction', 'data_access', 'payment_fraud', 'api_abuse', 'privilege_escalation')),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    user_ip INET NOT NULL,
    user_agent TEXT,
    description TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    detected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS security_events_severity_resolved_idx ON security_events(severity, is_resolved);
CREATE INDEX IF NOT EXISTS security_events_type_detected_idx ON security_events(event_type, detected_at);
CREATE INDEX IF NOT EXISTS security_events_ip_detected_idx ON security_events(user_ip, detected_at);

-- Compliance reports table
CREATE TABLE IF NOT EXISTS compliance_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(20) NOT NULL CHECK (report_type IN ('pci_dss', 'gdpr', 'sox', 'audit_trail', 'data_retention')),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    report_data TEXT NOT NULL, -- Encrypted JSON
    summary TEXT NOT NULL,
    compliance_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    issues_found INTEGER NOT NULL DEFAULT 0,
    critical_issues INTEGER NOT NULL DEFAULT 0,
    generated_by BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    file_path VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS compliance_reports_type_generated_idx ON compliance_reports(report_type, generated_at);
CREATE INDEX IF NOT EXISTS compliance_reports_period_idx ON compliance_reports(period_start, period_end);

-- Financial metrics table for analytics
CREATE TABLE IF NOT EXISTS financial_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(30) NOT NULL CHECK (metric_type IN (
        'revenue_total', 'revenue_subscription', 'revenue_institution', 'revenue_employer', 'revenue_cohort',
        'payment_success_rate', 'churn_rate', 'customer_growth', 'avg_revenue_per_user', 'cohort_utilization',
        'cost_per_hire', 'placement_rate', 'roi_institution', 'roi_employer'
    )),
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    value DECIMAL(15,2) NOT NULL DEFAULT 0,
    count INTEGER NOT NULL DEFAULT 0,
    percentage DECIMAL(5,2),
    organization_id UUID,
    user_segment VARCHAR(50),
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE UNIQUE INDEX IF NOT EXISTS financial_metrics_unique_idx ON financial_metrics(metric_type, period_type, period_start, organization_id, user_segment);
CREATE INDEX IF NOT EXISTS financial_metrics_type_period_idx ON financial_metrics(metric_type, period_start);
CREATE INDEX IF NOT EXISTS financial_metrics_org_type_idx ON financial_metrics(organization_id, metric_type);
CREATE INDEX IF NOT EXISTS financial_metrics_current_calc_idx ON financial_metrics(is_current, calculated_at);

-- Revenue streams table
CREATE TABLE IF NOT EXISTS revenue_streams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stream_type VARCHAR(20) NOT NULL CHECK (stream_type IN ('subscription', 'institution', 'employer', 'cohort', 'marketplace', 'mentorship')),
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    source_id UUID NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    customer_id UUID,
    customer_type VARCHAR(20),
    recognized_date DATE NOT NULL,
    payment_date DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS revenue_streams_type_date_idx ON revenue_streams(stream_type, recognized_date);
CREATE INDEX IF NOT EXISTS revenue_streams_customer_type_idx ON revenue_streams(customer_id, stream_type);
CREATE INDEX IF NOT EXISTS revenue_streams_date_idx ON revenue_streams(recognized_date);

-- Customer metrics table
CREATE TABLE IF NOT EXISTS customer_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    customer_type VARCHAR(20) NOT NULL,
    total_revenue DECIMAL(15,2) NOT NULL DEFAULT 0,
    monthly_recurring_revenue DECIMAL(15,2) NOT NULL DEFAULT 0,
    lifetime_value DECIMAL(15,2) NOT NULL DEFAULT 0,
    first_payment_date DATE,
    last_payment_date DATE,
    payment_count INTEGER NOT NULL DEFAULT 0,
    cohort_month DATE NOT NULL,
    months_active INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    churn_date DATE,
    churn_reason VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS customer_metrics_unique_idx ON customer_metrics(customer_id, customer_type);
CREATE INDEX IF NOT EXISTS customer_metrics_type_active_idx ON customer_metrics(customer_type, is_active);
CREATE INDEX IF NOT EXISTS customer_metrics_cohort_idx ON customer_metrics(cohort_month);
CREATE INDEX IF NOT EXISTS customer_metrics_churn_idx ON customer_metrics(churn_date);

-- Automation rules table
CREATE TABLE IF NOT EXISTS automation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(30) NOT NULL CHECK (rule_type IN ('invoice_generation', 'payment_retry', 'dunning_sequence', 'late_fee', 'account_suspension', 'collection_escalation')),
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('time_based', 'event_based', 'amount_based', 'status_based')),
    conditions JSONB NOT NULL DEFAULT '{}',
    actions JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    max_executions INTEGER,
    execution_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_executed TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS automation_rules_type_active_idx ON automation_rules(rule_type, is_active);
CREATE INDEX IF NOT EXISTS automation_rules_trigger_active_idx ON automation_rules(trigger_type, is_active);

-- Dunning sequences table
CREATE TABLE IF NOT EXISTS dunning_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES finance_invoices(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sequence_name VARCHAR(100) NOT NULL DEFAULT 'Standard Dunning',
    total_attempts INTEGER NOT NULL DEFAULT 5,
    current_attempt INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    next_attempt_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    original_amount DECIMAL(15,2) NOT NULL,
    recovered_amount DECIMAL(15,2) NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS dunning_sequences_status_next_idx ON dunning_sequences(status, next_attempt_at);
CREATE INDEX IF NOT EXISTS dunning_sequences_user_status_idx ON dunning_sequences(user_id, status);

-- Payment retry attempts table
CREATE TABLE IF NOT EXISTS payment_retry_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dunning_sequence_id UUID NOT NULL REFERENCES dunning_sequences(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL,
    retry_method VARCHAR(50) NOT NULL DEFAULT 'automatic',
    amount DECIMAL(15,2) NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    attempted_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'success', 'failed', 'cancelled')),
    gateway_response JSONB DEFAULT '{}',
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS payment_retry_attempts_status_scheduled_idx ON payment_retry_attempts(status, scheduled_at);
CREATE INDEX IF NOT EXISTS payment_retry_attempts_sequence_attempt_idx ON payment_retry_attempts(dunning_sequence_id, attempt_number);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_security_events_updated_at BEFORE UPDATE ON security_events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customer_metrics_updated_at BEFORE UPDATE ON customer_metrics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_automation_rules_updated_at BEFORE UPDATE ON automation_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default automation rules
INSERT INTO automation_rules (name, rule_type, trigger_type, conditions, actions, priority) VALUES
('Standard Invoice Generation', 'invoice_generation', 'event_based', 
 '{"trigger_event": "subscription_renewal", "delay_minutes": 0}',
 '{"generate_invoice": true, "send_email": true, "due_days": 30}', 100),

('Payment Retry Sequence', 'payment_retry', 'status_based',
 '{"payment_status": "failed", "max_amount": 1000}',
 '{"retry_attempts": 5, "retry_intervals": [1, 3, 7, 14, 30]}', 90),

('Standard Dunning Process', 'dunning_sequence', 'time_based',
 '{"days_overdue": 1, "min_amount": 10}',
 '{"sequence_type": "standard", "total_attempts": 5, "escalate_after": 3}', 80),

('Late Fee Application', 'late_fee', 'time_based',
 '{"days_overdue": 15, "min_amount": 50}',
 '{"late_fee_percentage": 5, "max_late_fee": 50}', 70)

ON CONFLICT DO NOTHING;

-- Insert sample financial metrics for current month
INSERT INTO financial_metrics (metric_type, period_type, period_start, period_end, value, count) VALUES
('revenue_total', 'monthly', DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day', 0, 0),
('payment_success_rate', 'monthly', DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day', 95.0, 0),
('customer_growth', 'monthly', DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day', 0, 0),
('churn_rate', 'monthly', DATE_TRUNC('month', CURRENT_DATE), DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day', 0, 0)

ON CONFLICT (metric_type, period_type, period_start, organization_id, user_segment) DO NOTHING;

-- Create function to automatically create customer metrics when first payment is made
CREATE OR REPLACE FUNCTION create_customer_metrics()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'paid' AND OLD.status != 'paid' THEN
        INSERT INTO customer_metrics (
            customer_id,
            customer_type,
            cohort_month,
            first_payment_date,
            last_payment_date,
            payment_count,
            total_revenue
        ) VALUES (
            COALESCE(NEW.user_id::text::uuid, NEW.organization_id),
            CASE WHEN NEW.user_id IS NOT NULL THEN 'user' ELSE 'organization' END,
            DATE_TRUNC('month', NEW.paid_date::date),
            NEW.paid_date::date,
            NEW.paid_date::date,
            1,
            NEW.total
        )
        ON CONFLICT (customer_id, customer_type) DO UPDATE SET
            last_payment_date = NEW.paid_date::date,
            payment_count = customer_metrics.payment_count + 1,
            total_revenue = customer_metrics.total_revenue + NEW.total,
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customer_metrics_on_payment
    AFTER UPDATE ON finance_invoices
    FOR EACH ROW
    EXECUTE FUNCTION create_customer_metrics();

-- Create function to log high-value transactions as security events
CREATE OR REPLACE FUNCTION monitor_high_value_transactions()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.amount > 5000 THEN
        INSERT INTO security_events (
            event_type,
            severity,
            user_id,
            user_ip,
            description,
            event_data
        ) VALUES (
            'suspicious_transaction',
            CASE WHEN NEW.amount > 10000 THEN 'high' ELSE 'medium' END,
            (SELECT user_id FROM wallets WHERE id = NEW.wallet_id),
            '127.0.0.1', -- Would be populated from request context
            'High-value wallet transaction detected',
            jsonb_build_object(
                'transaction_id', NEW.id,
                'amount', NEW.amount,
                'type', NEW.type,
                'description', NEW.description
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER monitor_wallet_transactions
    AFTER INSERT ON wallet_transactions
    FOR EACH ROW
    EXECUTE FUNCTION monitor_high_value_transactions();