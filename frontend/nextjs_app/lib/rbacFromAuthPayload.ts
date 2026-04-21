/**
 * Single source of truth for turning Django / MFA / SSO auth payloads into
 * normalized role slugs + dashboard path. Used by Next API routes and must stay
 * in sync with proxy.ts parseRolesCookie / dashboardForRole semantics.
 */

export function normalizeRoleName(roleName: string): string {
  const normalized = (roleName || '').toLowerCase().trim();
  if (
    normalized === 'program_director' ||
    normalized === 'program director' ||
    normalized === 'programdirector' ||
    normalized === 'director'
  ) {
    return 'program_director';
  }
  if (normalized === 'mentee') return 'mentee';
  if (normalized === 'student') return 'student';
  if (normalized === 'mentor') return 'mentor';
  if (normalized === 'admin') return 'admin';
  if (
    normalized === 'sponsor_admin' ||
    normalized === 'sponsor' ||
    normalized === 'sponsor/employer admin' ||
    normalized === 'sponsoremployer admin'
  ) {
    return 'sponsor_admin';
  }
  if (
    normalized === 'institution_admin' ||
    normalized === 'institution admin' ||
    normalized === 'institutional_admin' ||
    normalized === 'institutional admin'
  ) {
    return 'institution_admin';
  }
  if (normalized === 'organization_admin' || normalized === 'organization admin') {
    return 'organization_admin';
  }
  if (normalized === 'analyst') return 'analyst';
  if (normalized === 'employer') return 'employer';
  if (normalized === 'finance' || normalized === 'finance_admin') return 'finance';
  if (normalized === 'support') return 'support';
  return normalized;
}

/** Extract role slugs from `user.roles` / `user.role` (Django serializer shapes). */
export function extractNormalizedRoles(user: unknown): string[] {
  if (!user || typeof user !== 'object') return [];
  const u = user as Record<string, unknown>;
  const rolesRaw = u.roles;
  if (!Array.isArray(rolesRaw)) {
    const singleRole = u.role;
    return singleRole ? [normalizeRoleName(String(singleRole))] : [];
  }
  const roles = rolesRaw
    .map((ur: unknown) => {
      let roleValue: string;
      if (typeof ur === 'string') {
        roleValue = ur;
      } else if (ur && typeof ur === 'object') {
        const o = ur as Record<string, unknown>;
        const r = o.role;
        if (typeof r === 'string') roleValue = r;
        else if (r && typeof r === 'object') {
          const rn = (r as Record<string, unknown>).name;
          roleValue = rn != null ? String(rn) : '';
        } else {
          roleValue = o.name != null ? String(o.name) : '';
        }
      } else {
        roleValue = String(ur ?? '');
      }
      return normalizeRoleName(roleValue);
    })
    .filter(Boolean);
  return Array.from(new Set(roles));
}

export type AuthRoleHints = {
  /** Top-level `primary_role` from LoginView / MFA (slug or display string). */
  primary_role?: string | null;
  /** Some callers nest primary on the user object. */
  user?: Record<string, unknown> | null;
};

/**
 * Prefer explicit `user.roles`; if empty, use `primary_role` hints; if still empty
 * and user is Django superuser, treat as admin.
 */
export function resolveNormalizedRoles(
  user: unknown,
  hints?: AuthRoleHints
): string[] {
  let roles = extractNormalizedRoles(user);
  if (roles.length) return roles;

  const top = hints?.primary_role;
  if (typeof top === 'string' && top.trim()) {
    roles = [normalizeRoleName(top)];
    return Array.from(new Set(roles));
  }

  const u =
    hints?.user && typeof hints.user === 'object'
      ? hints.user
      : user && typeof user === 'object'
        ? (user as Record<string, unknown>)
        : null;
  if (u) {
    const nested = u.primary_role ?? u.primaryRole;
    if (typeof nested === 'string' && nested.trim()) {
      roles = [normalizeRoleName(nested)];
      return Array.from(new Set(roles));
    }
    if (u.is_superuser === true) {
      return ['admin'];
    }
  }
  return [];
}

export function getPrimaryRole(roles: string[]): string | null {
  if (!roles.length) return null;
  if (roles.includes('admin')) return 'admin';
  const priority = [
    'program_director',
    'finance',
    'support',
    'mentor',
    'analyst',
    'institution_admin',
    'organization_admin',
    'sponsor_admin',
    'employer',
    'mentee',
    'student',
  ];
  for (const r of priority) {
    if (roles.includes(r)) return r;
  }
  return roles[0] || null;
}

export function getDashboardForRole(role: string | null): string {
  switch (role) {
    case 'admin':
      return '/dashboard/admin';
    case 'program_director':
      return '/dashboard/director';
    case 'mentor':
      return '/dashboard/mentor';
    case 'analyst':
      return '/dashboard/analyst';
    case 'institution_admin':
    case 'organization_admin':
      return '/dashboard/institution';
    case 'sponsor_admin':
      return '/dashboard/sponsor';
    case 'employer':
      return '/dashboard/employer';
    case 'finance':
      return '/dashboard/finance';
    case 'support':
      return '/support/dashboard';
    case 'mentee':
    case 'student':
      return '/dashboard/student';
    default:
      return '/dashboard/student';
  }
}
