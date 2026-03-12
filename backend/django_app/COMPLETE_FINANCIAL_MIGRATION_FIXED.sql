-- Complete Financial Module Migration - 100% Implementation (FIXED)
-- This migration creates all missing financial dashboard, analytics, and compliance models

BEGIN;

-- Create Financial Dashboards table
CREATE TABLE financial_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dashboard_type VARCHAR(20) NOT NULL CHECK (dashboard_type IN ('admin', 'student', 'institution', 'employer', 'cohort_manager', 'mentor')),
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, dashboard_type)
);

CREATE INDEX idx_financial_dashboards_user_type ON financial_dashboards(user_id, dashboard_type);
CREATE INDEX idx_financial_dashboards_type_active ON financial_dashboards(dashboard_type, is_active);

-- Create Revenue Metrics table
CREATE TABLE revenue_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type VARCHAR(20) NOT NULL CHECK (metric_type IN ('mrr', 'arr', 'churn_rate', 'ltv', 'cac', 'arpu', 'conversion_rate')),
    revenue_stream VARCHAR(20) NOT NULL CHECK (revenue_stream IN ('subscriptions', 'institutions', 'employers', 'cohorts', 'total')),
    value DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(metric_type, revenue_stream, period_start, period_end)
);

CREATE INDEX idx_revenue_metrics_type_stream ON revenue_metrics(metric_type, revenue_stream);
CREATE INDEX idx_revenue_metrics_period ON revenue_metrics(period_start, period_end);
CREATE INDEX idx_revenue_metrics_calculated ON revenue_metrics(calculated_at);

-- Create Financial KPIs table
CREATE TABLE financial_kpis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('revenue', 'growth', 'retention', 'efficiency', 'profitability')),
    current_value DECIMAL(15,2) NOT NULL,
    target_value DECIMAL(15,2),
    previous_value DECIMAL(15,2),
    unit VARCHAR(20) DEFAULT 'currency',
    period VARCHAR(20) DEFAULT 'monthly',
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_financial_kpis_category ON financial_kpis(category);
CREATE INDEX idx_financial_kpis_updated ON financial_kpis(last_updated);

-- Create Financial Alerts table
CREATE TABLE financial_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('revenue_drop', 'churn_spike', 'payment_failure', 'low_cash_flow', 'target_missed', 'anomaly_detected')),
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed')),
    assigned_to_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    acknowledged_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    resolved_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_financial_alerts_type_severity ON financial_alerts(alert_type, severity);
CREATE INDEX idx_financial_alerts_status_created ON financial_alerts(status, created_at);
CREATE INDEX idx_financial_alerts_assigned ON financial_alerts(assigned_to_id, status);

-- Create Cash Flow Projections table
CREATE TABLE cash_flow_projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_type VARCHAR(20) NOT NULL CHECK (projection_type IN ('weekly', 'monthly', 'quarterly', 'annual')),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    subscription_revenue DECIMAL(15,2) DEFAULT 0,
    institution_revenue DECIMAL(15,2) DEFAULT 0,
    employer_revenue DECIMAL(15,2) DEFAULT 0,
    cohort_revenue DECIMAL(15,2) DEFAULT 0,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    mentor_payouts DECIMAL(15,2) DEFAULT 0,
    operational_costs DECIMAL(15,2) DEFAULT 0,
    marketing_costs DECIMAL(15,2) DEFAULT 0,
    total_expenses DECIMAL(15,2) DEFAULT 0,
    net_cash_flow DECIMAL(15,2) DEFAULT 0,
    confidence_score DECIMAL(5,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(projection_type, period_start, period_end)
);

CREATE INDEX idx_cash_flow_projections_type ON cash_flow_projections(projection_type);
CREATE INDEX idx_cash_flow_projections_period ON cash_flow_projections(period_start, period_end);

-- Create Financial Reports table
CREATE TABLE financial_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(30) NOT NULL CHECK (report_type IN ('revenue_summary', 'subscription_analytics', 'cohort_financials', 'mentor_compensation', 'cash_flow', 'tax_report', 'audit_report')),
    title VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    filters JSONB DEFAULT '{}',
    format VARCHAR(10) DEFAULT 'pdf' CHECK (format IN ('pdf', 'excel', 'csv', 'json')),
    status VARCHAR(20) DEFAULT 'generating' CHECK (status IN ('generating', 'completed', 'failed')),
    file_url TEXT DEFAULT '',
    file_size BIGINT,
    generated_by_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_public BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_financial_reports_type_status ON financial_reports(report_type, status);
CREATE INDEX idx_financial_reports_generated_by ON financial_reports(generated_by_id, created_at);
CREATE INDEX idx_financial_reports_period ON financial_reports(period_start, period_end);

-- Create Compliance Records table
CREATE TABLE compliance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    compliance_type VARCHAR(30) NOT NULL CHECK (compliance_type IN ('tax_filing', 'audit_trail', 'data_retention', 'privacy_compliance', 'financial_regulation', 'payment_compliance')),
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    regulation VARCHAR(100) NOT NULL,
    requirement TEXT NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN ('compliant', 'non_compliant', 'pending_review', 'remediation_required')),
    evidence_files JSONB DEFAULT '[]',
    documentation TEXT DEFAULT '',
    reviewed_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    remediation_plan TEXT DEFAULT '',
    remediation_deadline DATE,
    compliance_date DATE NOT NULL,
    next_review_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_compliance_records_type_status ON compliance_records(compliance_type, status);
CREATE INDEX idx_compliance_records_next_review ON compliance_records(next_review_date);
CREATE INDEX idx_compliance_records_remediation ON compliance_records(remediation_deadline);

-- Create Audit Logs table
CREATE TABLE financial_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(30) NOT NULL CHECK (action_type IN ('create', 'update', 'delete', 'payment', 'refund', 'subscription_change', 'invoice_generation', 'report_generation')),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    old_values JSONB DEFAULT '{}',
    new_values JSONB DEFAULT '{}',
    changes_summary TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT DEFAULT '',
    session_id VARCHAR(100) DEFAULT '',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_financial_audit_logs_user_created ON financial_audit_logs(user_id, created_at);
CREATE INDEX idx_financial_audit_logs_action_created ON financial_audit_logs(action_type, created_at);
CREATE INDEX idx_financial_audit_logs_resource ON financial_audit_logs(resource_type, resource_id);
CREATE INDEX idx_financial_audit_logs_created ON financial_audit_logs(created_at);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_financial_dashboards_updated_at BEFORE UPDATE ON financial_dashboards FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cash_flow_projections_updated_at BEFORE UPDATE ON cash_flow_projections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_compliance_records_updated_at BEFORE UPDATE ON compliance_records FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for cash flow totals calculation
CREATE OR REPLACE FUNCTION calculate_cash_flow_totals()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_revenue = NEW.subscription_revenue + NEW.institution_revenue + NEW.employer_revenue + NEW.cohort_revenue;
    NEW.total_expenses = NEW.mentor_payouts + NEW.operational_costs + NEW.marketing_costs;
    NEW.net_cash_flow = NEW.total_revenue - NEW.total_expenses;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_cash_flow_totals_trigger 
    BEFORE INSERT OR UPDATE ON cash_flow_projections 
    FOR EACH ROW EXECUTE FUNCTION calculate_cash_flow_totals();

-- Insert default KPIs
INSERT INTO financial_kpis (name, category, current_value, target_value, unit, period) VALUES
('Monthly Recurring Revenue', 'revenue', 0, 100000, 'currency', 'monthly'),
('Annual Recurring Revenue', 'revenue', 0, 1200000, 'currency', 'annual'),
('Monthly Churn Rate', 'retention', 0, 5, 'percentage', 'monthly'),
('Customer Lifetime Value', 'profitability', 0, 2000, 'currency', 'annual'),
('Customer Acquisition Cost', 'efficiency', 0, 200, 'currency', 'monthly'),
('Average Revenue Per User', 'efficiency', 0, 50, 'currency', 'monthly'),
('Trial Conversion Rate', 'growth', 0, 15, 'percentage', 'monthly'),
('Net Revenue Retention', 'retention', 0, 110, 'percentage', 'annual'),
('Gross Margin', 'profitability', 0, 80, 'percentage', 'monthly'),
('Monthly Active Users', 'growth', 0, 10000, 'count', 'monthly');

-- Insert sample compliance records
INSERT INTO compliance_records (compliance_type, title, description, regulation, requirement, status, compliance_date, next_review_date) VALUES
('tax_filing', 'Annual Tax Filing', 'Annual corporate tax filing compliance', 'IRS Code Section 11', 'File corporate tax return by March 15th', 'compliant', CURRENT_DATE - INTERVAL '30 days', CURRENT_DATE + INTERVAL '335 days'),
('data_retention', 'Financial Data Retention', 'Maintain financial records for required period', 'SOX Section 802', 'Retain financial records for 7 years', 'compliant', CURRENT_DATE, CURRENT_DATE + INTERVAL '1 year'),
('payment_compliance', 'PCI DSS Compliance', 'Payment card industry data security standards', 'PCI DSS v3.2.1', 'Maintain secure payment processing environment', 'compliant', CURRENT_DATE - INTERVAL '90 days', CURRENT_DATE + INTERVAL '275 days'),
('privacy_compliance', 'GDPR Compliance', 'General Data Protection Regulation compliance', 'GDPR Article 32', 'Implement appropriate technical and organizational measures', 'compliant', CURRENT_DATE - INTERVAL '60 days', CURRENT_DATE + INTERVAL '305 days');

-- Create views for financial analytics
CREATE OR REPLACE VIEW financial_dashboard_summary AS
SELECT 
    'revenue' as category,
    COUNT(*) FILTER (WHERE rm.metric_type = 'mrr') as mrr_records,
    COUNT(*) FILTER (WHERE rm.metric_type = 'arr') as arr_records,
    COUNT(*) FILTER (WHERE rm.metric_type = 'churn_rate') as churn_records,
    COUNT(*) FILTER (WHERE fa.severity = 'critical') as critical_alerts,
    COUNT(*) FILTER (WHERE fa.severity = 'high') as high_alerts,
    COUNT(*) FILTER (WHERE fa.status = 'active') as active_alerts,
    COUNT(DISTINCT fr.id) FILTER (WHERE fr.status = 'completed') as completed_reports,
    COUNT(DISTINCT cr.id) FILTER (WHERE cr.status = 'compliant') as compliant_records
FROM revenue_metrics rm
CROSS JOIN financial_alerts fa
CROSS JOIN financial_reports fr
CROSS JOIN compliance_records cr;

-- Create function for automatic KPI updates
CREATE OR REPLACE FUNCTION update_financial_kpis()
RETURNS void AS $$
BEGIN
    -- Update MRR from latest revenue metrics
    UPDATE financial_kpis 
    SET current_value = (
        SELECT COALESCE(value, 0) 
        FROM revenue_metrics 
        WHERE metric_type = 'mrr' AND revenue_stream = 'total'
        ORDER BY calculated_at DESC 
        LIMIT 1
    ),
    last_updated = NOW()
    WHERE name = 'Monthly Recurring Revenue';
    
    -- Update ARR from latest revenue metrics
    UPDATE financial_kpis 
    SET current_value = (
        SELECT COALESCE(value, 0) 
        FROM revenue_metrics 
        WHERE metric_type = 'arr' AND revenue_stream = 'total'
        ORDER BY calculated_at DESC 
        LIMIT 1
    ),
    last_updated = NOW()
    WHERE name = 'Annual Recurring Revenue';
    
    -- Update Churn Rate from latest revenue metrics
    UPDATE financial_kpis 
    SET current_value = (
        SELECT COALESCE(value, 0) 
        FROM revenue_metrics 
        WHERE metric_type = 'churn_rate' AND revenue_stream = 'subscriptions'
        ORDER BY calculated_at DESC 
        LIMIT 1
    ),
    last_updated = NOW()
    WHERE name = 'Monthly Churn Rate';
    
    -- Log the update
    INSERT INTO financial_audit_logs (
        action_type, resource_type, resource_id, changes_summary, metadata
    ) VALUES (
        'update', 'financial_kpis', gen_random_uuid(), 
        'Automated KPI update from revenue metrics',
        '{"automated": true, "update_type": "kpi_refresh"}'
    );
END;
$$ LANGUAGE plpgsql;

-- Create function for compliance status checking
CREATE OR REPLACE FUNCTION check_compliance_status()
RETURNS TABLE(
    total_records INTEGER,
    compliant_records INTEGER,
    non_compliant_records INTEGER,
    pending_records INTEGER,
    compliance_rate DECIMAL(5,2),
    overdue_reviews INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_records,
        COUNT(*) FILTER (WHERE status = 'compliant')::INTEGER as compliant_records,
        COUNT(*) FILTER (WHERE status = 'non_compliant')::INTEGER as non_compliant_records,
        COUNT(*) FILTER (WHERE status = 'pending_review')::INTEGER as pending_records,
        CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND((COUNT(*) FILTER (WHERE status = 'compliant')::DECIMAL / COUNT(*)) * 100, 2)
            ELSE 0
        END as compliance_rate,
        COUNT(*) FILTER (WHERE next_review_date < CURRENT_DATE)::INTEGER as overdue_reviews
    FROM compliance_records;
END;
$$ LANGUAGE plpgsql;

-- Create performance optimization indexes (without CONCURRENTLY inside transaction)
CREATE INDEX idx_revenue_metrics_latest ON revenue_metrics(metric_type, revenue_stream, calculated_at DESC);
CREATE INDEX idx_financial_alerts_active ON financial_alerts(status, created_at DESC) WHERE status = 'active';
CREATE INDEX idx_cash_flow_latest ON cash_flow_projections(projection_type, created_at DESC);
CREATE INDEX idx_compliance_overdue ON compliance_records(next_review_date) WHERE next_review_date < CURRENT_DATE;

COMMIT;