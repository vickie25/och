/**
 * Login-only helpers: staff / multi-role users must not be forced through
 * student profiling when they also carry student/mentee assignments.
 */

const ELEVATED_STUDENT_FLOW_BLOCK = new Set<string>([
  'admin',
  'finance',
  'finance_admin',
  'program_director',
  'mentor',
  'support',
  'analyst',
  'sponsor_admin',
  'sponsor',
  'institutional_admin',
  'institution_admin',
  'organization_admin',
  'employer',
]);

export function roleNamesFromUser(user: { roles?: unknown[] } | null | undefined): string[] {
  const roles = user?.roles;
  if (!Array.isArray(roles) || roles.length === 0) return [];
  return roles
    .map((r) => {
      const name =
        typeof r === 'string' ? r : (r as { role?: string; name?: string; role_display_name?: string })?.role
          || (r as { name?: string })?.name
          || (r as { role_display_name?: string })?.role_display_name
          || '';
      return String(name).toLowerCase().trim();
    })
    .filter(Boolean);
}

function hasElevatedRole(roleNames: string[]): boolean {
  return roleNames.some((n) => ELEVATED_STUDENT_FLOW_BLOCK.has(n));
}

/**
 * True only for learner-only accounts: student/mentee without any staff/elevated role,
 * and backend primary role (when provided) is still learner.
 */
export function shouldRunStudentProfilerFlow(
  roleNames: string[],
  primaryRoleFromLogin: string | null | undefined,
): boolean {
  const pr = (primaryRoleFromLogin || '').toLowerCase().trim();
  if (pr && pr !== 'student' && pr !== 'mentee') {
    return false;
  }
  if (hasElevatedRole(roleNames)) {
    return false;
  }
  return roleNames.some((n) => n === 'student' || n === 'mentee');
}
