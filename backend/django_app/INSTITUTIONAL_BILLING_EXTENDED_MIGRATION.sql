-- Extended Institutional Billing Migration
-- Add SSO, Academic Calendar, and Track Assignment features

-- Add SSO fields to institutional_contracts
ALTER TABLE institutional_contracts ADD COLUMN sso_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE institutional_contracts ADD COLUMN sso_provider_type VARCHAR(50) DEFAULT '';
ALTER TABLE institutional_contracts ADD COLUMN sso_entity_id VARCHAR(255) DEFAULT '';
ALTER TABLE institutional_contracts ADD COLUMN sso_url TEXT DEFAULT '';
ALTER TABLE institutional_contracts ADD COLUMN sso_certificate TEXT DEFAULT '';
ALTER TABLE institutional_contracts ADD COLUMN domain_auto_enrollment BOOLEAN DEFAULT FALSE;
ALTER TABLE institutional_contracts ADD COLUMN allowed_domains TEXT[] DEFAULT '{}';

-- Add Academic Calendar fields
ALTER TABLE institutional_contracts ADD COLUMN academic_calendar_alignment BOOLEAN DEFAULT FALSE;
ALTER TABLE institutional_contracts ADD COLUMN semester_start VARCHAR(20) DEFAULT '';
ALTER TABLE institutional_contracts ADD COLUMN quarter_system BOOLEAN DEFAULT FALSE;
ALTER TABLE institutional_contracts ADD COLUMN quarter_start VARCHAR(20) DEFAULT '';
ALTER TABLE institutional_contracts ADD COLUMN fiscal_year_alignment BOOLEAN DEFAULT FALSE;
ALTER TABLE institutional_contracts ADD COLUMN fiscal_year_start VARCHAR(20) DEFAULT 'july';

-- Add Summer Program fields
ALTER TABLE institutional_contracts ADD COLUMN summer_program_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE institutional_contracts ADD COLUMN summer_pricing_type VARCHAR(20) DEFAULT 'reduced_rate';
ALTER TABLE institutional_contracts ADD COLUMN summer_months TEXT[] DEFAULT '{june,july,august}';

-- Create Seat Pools table
CREATE TABLE institutional_seat_pools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES institutional_contracts(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    pool_type VARCHAR(20) DEFAULT 'general',
    allocated_seats INTEGER NOT NULL,
    description TEXT DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    auto_assign BOOLEAN DEFAULT FALSE,
    assignment_criteria JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(contract_id, name)
);

CREATE INDEX idx_institutional_seat_pools_contract ON institutional_seat_pools(contract_id);
CREATE INDEX idx_institutional_seat_pools_active ON institutional_seat_pools(is_active);

-- Create Seat Pool Assignments table
CREATE TABLE institutional_seat_pool_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pool_id UUID NOT NULL REFERENCES institutional_seat_pools(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES institutional_students(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(pool_id, student_id)
);

CREATE INDEX idx_seat_pool_assignments_pool ON institutional_seat_pool_assignments(pool_id);
CREATE INDEX idx_seat_pool_assignments_student ON institutional_seat_pool_assignments(student_id);

-- Create Track Assignments table
CREATE TABLE institutional_track_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES institutional_contracts(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES institutional_students(id) ON DELETE CASCADE,
    track_id UUID NOT NULL,
    track_name VARCHAR(255) NOT NULL,
    is_mandatory BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completion_deadline DATE,
    status VARCHAR(20) DEFAULT 'assigned',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    department_filter VARCHAR(255) DEFAULT '',
    program_filter VARCHAR(255) DEFAULT '',
    assigned_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(student_id, track_id)
);

CREATE INDEX idx_track_assignments_contract ON institutional_track_assignments(contract_id);
CREATE INDEX idx_track_assignments_student ON institutional_track_assignments(student_id);
CREATE INDEX idx_track_assignments_status ON institutional_track_assignments(status);
CREATE INDEX idx_track_assignments_deadline ON institutional_track_assignments(completion_deadline, status);

-- Create Billing Adjustments table
CREATE TABLE institutional_billing_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES institutional_contracts(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    adjustment_percentage DECIMAL(5,2) DEFAULT 0.00,
    fixed_amount DECIMAL(10,2) DEFAULT 0.00,
    description TEXT NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    created_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_billing_adjustments_contract ON institutional_billing_adjustments(contract_id);
CREATE INDEX idx_billing_adjustments_dates ON institutional_billing_adjustments(start_date, end_date);

-- Create SSO Configurations table
CREATE TABLE institutional_sso_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES institutional_contracts(id) ON DELETE CASCADE UNIQUE,
    provider_type VARCHAR(20) NOT NULL,
    provider_name VARCHAR(255) NOT NULL,
    entity_id VARCHAR(255) NOT NULL UNIQUE,
    sso_url TEXT NOT NULL,
    slo_url TEXT DEFAULT '',
    x509_certificate TEXT NOT NULL,
    private_key TEXT DEFAULT '',
    attribute_mapping JSONB DEFAULT '{}',
    domain_auto_enrollment BOOLEAN DEFAULT FALSE,
    allowed_domains TEXT[] DEFAULT '{}',
    auto_create_users BOOLEAN DEFAULT TRUE,
    auto_update_users BOOLEAN DEFAULT TRUE,
    default_user_role VARCHAR(50) DEFAULT 'student',
    is_active BOOLEAN DEFAULT TRUE,
    last_sync TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sso_configurations_contract ON institutional_sso_configurations(contract_id);
CREATE INDEX idx_sso_configurations_entity ON institutional_sso_configurations(entity_id);
CREATE INDEX idx_sso_configurations_active ON institutional_sso_configurations(is_active);

-- Add indexes for performance
CREATE INDEX idx_institutional_contracts_sso ON institutional_contracts(sso_enabled) WHERE sso_enabled = TRUE;
CREATE INDEX idx_institutional_contracts_academic ON institutional_contracts(academic_calendar_alignment) WHERE academic_calendar_alignment = TRUE;
CREATE INDEX idx_institutional_contracts_fiscal ON institutional_contracts(fiscal_year_alignment) WHERE fiscal_year_alignment = TRUE;

-- Add triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_institutional_seat_pools_updated_at BEFORE UPDATE ON institutional_seat_pools FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_institutional_track_assignments_updated_at BEFORE UPDATE ON institutional_track_assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_institutional_sso_configurations_updated_at BEFORE UPDATE ON institutional_sso_configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for analytics
CREATE OR REPLACE VIEW institutional_contract_analytics AS
SELECT 
    c.id,
    c.contract_number,
    c.organization_id,
    c.status,
    c.student_seat_count,
    c.per_student_rate,
    (c.student_seat_count * c.per_student_rate) AS monthly_amount,
    (c.student_seat_count * c.per_student_rate * 12) AS annual_amount,
    COUNT(DISTINCT s.id) FILTER (WHERE s.is_active = TRUE) as active_students,
    COUNT(DISTINCT s.id) as total_enrolled_students,
    COALESCE(SUM(b.total_amount), 0) as total_invoiced,
    COALESCE(SUM(b.total_amount) FILTER (WHERE b.status = 'paid'), 0) as total_paid,
    COALESCE(SUM(b.total_amount) FILTER (WHERE b.status = 'overdue'), 0) as total_overdue,
    ROUND(
        (COUNT(DISTINCT s.id) FILTER (WHERE s.is_active = TRUE)::DECIMAL / 
         NULLIF(c.student_seat_count, 0) * 100), 2
    ) as seat_utilization_percentage
FROM institutional_contracts c
LEFT JOIN institutional_students s ON c.id = s.contract_id
LEFT JOIN institutional_billing b ON c.id = b.contract_id
GROUP BY c.id, c.contract_number, c.organization_id, c.status, 
         c.student_seat_count, c.per_student_rate;

-- Create function for automatic seat pool assignment
CREATE OR REPLACE FUNCTION auto_assign_student_to_pool()
RETURNS TRIGGER AS $$
DECLARE
    pool_record RECORD;
BEGIN
    -- Only process active students
    IF NEW.is_active = FALSE THEN
        RETURN NEW;
    END IF;
    
    -- Find matching pools with auto-assignment enabled
    FOR pool_record IN 
        SELECT sp.* 
        FROM institutional_seat_pools sp 
        WHERE sp.contract_id = NEW.contract_id 
        AND sp.auto_assign = TRUE 
        AND sp.is_active = TRUE
        AND sp.allocated_seats > (
            SELECT COUNT(*) 
            FROM institutional_seat_pool_assignments spa 
            JOIN institutional_students s ON spa.student_id = s.id 
            WHERE spa.pool_id = sp.id AND s.is_active = TRUE
        )
    LOOP
        -- Check if assignment criteria match (simplified logic)
        -- In practice, this would check JSON criteria against user profile
        INSERT INTO institutional_seat_pool_assignments (pool_id, student_id)
        VALUES (pool_record.id, NEW.id)
        ON CONFLICT (pool_id, student_id) DO NOTHING;
        
        -- Exit after first successful assignment
        EXIT;
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto pool assignment
CREATE TRIGGER trigger_auto_assign_student_pool
    AFTER INSERT OR UPDATE ON institutional_students
    FOR EACH ROW
    WHEN (NEW.is_active = TRUE)
    EXECUTE FUNCTION auto_assign_student_to_pool();

-- Insert default seat pools for existing contracts
INSERT INTO institutional_seat_pools (contract_id, name, pool_type, allocated_seats, description)
SELECT 
    id,
    'General Pool',
    'general',
    student_seat_count,
    'Default general seat pool for all students'
FROM institutional_contracts
WHERE status = 'active'
ON CONFLICT (contract_id, name) DO NOTHING;

COMMIT;