-- Add Support Role and Permissions
-- Matches Django schema: roles, permissions, roles_permissions (M2M; user_roles is for user-role assignments only).
-- Run after: backend migrations and support tables (create_support_tables.sql if needed).
-- Example: psql -U postgres -d ongozacyberhub -f backend/django_app/support/setup_support_permissions.sql

-- 1. Create support role in roles table (not user_roles!)
INSERT INTO roles (name, display_name, description, is_system_role, created_at, updated_at)
VALUES (
    'support',
    'Support',
    'Support staff with access to tickets and user assistance',
    true,
    NOW(),
    NOW()
)
ON CONFLICT (name) DO NOTHING;

-- 2. Create support-related permissions if missing (schema: name, resource_type, action, description, created_at)
-- Use resource_type 'ticket' / 'problem_code' to avoid conflicting with user/create, user/read, etc.
INSERT INTO permissions (name, resource_type, action, description, created_at)
VALUES
    ('create_ticket', 'ticket', 'create', 'Create support tickets', NOW()),
    ('read_ticket', 'ticket', 'read', 'Read support ticket details', NOW()),
    ('update_ticket', 'ticket', 'update', 'Update support tickets', NOW()),
    ('list_tickets', 'ticket', 'list', 'List support tickets', NOW()),
    ('list_problem_codes', 'problem_code', 'list', 'List problem tracking codes', NOW()),
    ('manage_problem_codes', 'problem_code', 'manage', 'Create/update/delete problem codes', NOW())
ON CONFLICT (name) DO NOTHING;

-- 3. Assign support permissions to support role (M2M table: roles_permissions)
INSERT INTO roles_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'support'
  AND p.name IN ('list_tickets', 'read_ticket', 'create_ticket', 'update_ticket', 'list_problem_codes', 'manage_problem_codes')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 4. Assign student-facing ticket permissions to student role (so students can create/view own tickets)
INSERT INTO roles_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
CROSS JOIN permissions p
WHERE r.name = 'student'
  AND p.name IN ('create_ticket', 'read_ticket', 'list_tickets')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- 5. Create support_ticket_responses table if not exists (requires support_tickets)
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
CREATE INDEX IF NOT EXISTS support_ticket_responses_created_by_id_idx ON support_ticket_responses (created_by_id);
CREATE INDEX IF NOT EXISTS support_ticket_responses_created_at_idx ON support_ticket_responses (created_at DESC);

-- 6. Create support_ticket_attachments table if not exists
CREATE TABLE IF NOT EXISTS support_ticket_attachments (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT REFERENCES support_tickets(id) ON DELETE CASCADE,
    response_id BIGINT REFERENCES support_ticket_responses(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    uploaded_by_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS support_ticket_attachments_ticket_id_idx ON support_ticket_attachments (ticket_id);
CREATE INDEX IF NOT EXISTS support_ticket_attachments_response_id_idx ON support_ticket_attachments (response_id);

-- 7. Create user_activity_logs table for support to track user actions
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS user_activity_logs_user_id_idx ON user_activity_logs (user_id);
CREATE INDEX IF NOT EXISTS user_activity_logs_action_idx ON user_activity_logs (action);
CREATE INDEX IF NOT EXISTS user_activity_logs_created_at_idx ON user_activity_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS user_activity_logs_resource_idx ON user_activity_logs (resource_type, resource_id);

-- Verify the setup
SELECT 'Support role' AS status, COUNT(*) AS count FROM roles WHERE name = 'support'
UNION ALL
SELECT 'Support role permissions', COUNT(*) FROM roles_permissions WHERE role_id = (SELECT id FROM roles WHERE name = 'support')
UNION ALL
SELECT 'Student ticket permissions', COUNT(*) FROM roles_permissions rp JOIN roles r ON r.id = rp.role_id WHERE r.name = 'student' AND rp.permission_id IN (SELECT id FROM permissions WHERE name IN ('create_ticket', 'read_ticket', 'list_tickets'));
