-- Support app: all tables (use when DB issues or migrations not applied).
-- Run: psql -U postgres -d YOUR_DB -f backend/django_app/support/support_tables_full.sql
-- Requires: table "users" (Django auth) must exist.

-- 1. support_problem_codes
CREATE TABLE IF NOT EXISTS support_problem_codes (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(32) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category VARCHAR(32) NOT NULL DEFAULT 'other',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT support_problem_codes_code_key UNIQUE (code)
);
CREATE INDEX IF NOT EXISTS support_problem_codes_code_idx ON support_problem_codes (code);
CREATE INDEX IF NOT EXISTS support_problem_codes_category_idx ON support_problem_codes (category);

-- 2. support_tickets
CREATE TABLE IF NOT EXISTS support_tickets (
    id BIGSERIAL PRIMARY KEY,
    reporter_id INTEGER NULL,
    reporter_email VARCHAR(254) NOT NULL DEFAULT '',
    reporter_name VARCHAR(255) NOT NULL DEFAULT '',
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    priority VARCHAR(32) NOT NULL DEFAULT 'medium',
    problem_code_id BIGINT NULL,
    internal_notes TEXT NOT NULL DEFAULT '',
    assigned_to_id BIGINT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE NULL,
    resolution_notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by_id BIGINT NULL,
    CONSTRAINT support_tickets_problem_code_fk FOREIGN KEY (problem_code_id) REFERENCES support_problem_codes(id) ON DELETE SET NULL,
    CONSTRAINT support_tickets_assigned_to_fk FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT support_tickets_created_by_fk FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS support_tickets_reporter_id_idx ON support_tickets (reporter_id);
CREATE INDEX IF NOT EXISTS support_tickets_status_idx ON support_tickets (status);
CREATE INDEX IF NOT EXISTS support_tickets_priority_idx ON support_tickets (priority);

-- 3. support_ticket_responses
CREATE TABLE IF NOT EXISTS support_ticket_responses (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT false,
    created_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_by_name VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS support_ticket_responses_ticket_id_idx ON support_ticket_responses (ticket_id);
CREATE INDEX IF NOT EXISTS support_ticket_responses_created_at_idx ON support_ticket_responses (created_at DESC);

-- 4. support_ticket_attachments
CREATE TABLE IF NOT EXISTS support_ticket_attachments (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT REFERENCES support_tickets(id) ON DELETE CASCADE,
    response_id BIGINT REFERENCES support_ticket_responses(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NULL,
    mime_type VARCHAR(100) NULL,
    uploaded_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS support_ticket_attachments_ticket_id_idx ON support_ticket_attachments (ticket_id);
CREATE INDEX IF NOT EXISTS support_ticket_attachments_response_id_idx ON support_ticket_attachments (response_id);

-- Seed problem codes
INSERT INTO support_problem_codes (code, name, description, category)
VALUES
    ('AUTH-001', 'Login / access issue', 'User cannot log in or access account', 'auth'),
    ('BILL-001', 'Billing or payment question', 'Invoice, payment, or subscription question', 'billing'),
    ('CURR-001', 'Curriculum or content issue', 'Module, mission, or learning content problem', 'curriculum'),
    ('MENT-001', 'Mentorship or matching', 'Mentor/mentee matching or session issue', 'mentorship'),
    ('TECH-001', 'Technical / bug', 'Bug, error, or platform malfunction', 'technical'),
    ('ACCT-001', 'Account or profile', 'Profile, settings, or account data', 'account'),
    ('PLAT-001', 'Platform general', 'General platform question or feedback', 'platform')
ON CONFLICT (code) DO NOTHING;
