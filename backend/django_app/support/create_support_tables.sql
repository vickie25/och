-- Create support app tables (support_problem_codes, support_tickets)
-- Use when: relation "support_tickets" does not exist (e.g. support migrations not applied).
--
-- Option A – Prefer running migrations:
--   cd backend/django_app && python manage.py migrate support
--
-- Option B – Apply this SQL manually (PostgreSQL):
--   psql -U your_user -d your_db -f support/create_support_tables.sql
--   Or run the statements below in your DB client.
--
-- Requires: table "users" must already exist (users app migrated first).
-- PostgreSQL.

-- 1. support_problem_codes (no dependencies)
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
CREATE INDEX IF NOT EXISTS support_pro_category_7a0f0d_idx ON support_problem_codes (category, is_active);

-- 2. support_tickets (depends on support_problem_codes and users)
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
    CONSTRAINT support_tickets_problem_code_id_fk
        FOREIGN KEY (problem_code_id) REFERENCES support_problem_codes(id) ON DELETE SET NULL,
    CONSTRAINT support_tickets_assigned_to_id_fk
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT support_tickets_created_by_id_fk
        FOREIGN KEY (created_by_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS support_tickets_reporter_id_idx ON support_tickets (reporter_id);
CREATE INDEX IF NOT EXISTS support_tickets_status_idx ON support_tickets (status);
CREATE INDEX IF NOT EXISTS support_tickets_priority_idx ON support_tickets (priority);
CREATE INDEX IF NOT EXISTS support_tickets_problem_code_id_idx ON support_tickets (problem_code_id);
CREATE INDEX IF NOT EXISTS support_tickets_assigned_to_id_idx ON support_tickets (assigned_to_id);
CREATE INDEX IF NOT EXISTS support_ti_status_8b0e2a_idx ON support_tickets (status, created_at DESC);
CREATE INDEX IF NOT EXISTS support_ti_priorit_9c1f3b_idx ON support_tickets (priority, status);
CREATE INDEX IF NOT EXISTS support_ti_assigne_d2e4a5_idx ON support_tickets (assigned_to_id, status);

-- Optional: seed default problem codes (if 0002_seed_default_problem_codes was not run)
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
