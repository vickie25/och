/**
 * Set auth cookies after MFA complete (or when tokens are obtained outside login API).
 * Middleware reads access_token cookie; without it, post-MFA redirect would send user back to login.
 */
import { NextResponse } from 'next/server';

function normalizeRoleName(roleName: string): string {
  const normalized = (roleName || '').toLowerCase().trim()
  if (normalized === 'program_director' || normalized === 'director') return 'program_director'
  if (normalized === 'sponsor_admin' || normalized === 'sponsor') return 'sponsor_admin'
  if (normalized === 'institution_admin' || normalized === 'institution admin' || normalized === 'institutional_admin' || normalized === 'institutional admin') return 'institution_admin'
  if (normalized === 'organization_admin' || normalized === 'organization admin') return 'organization_admin'
  if (normalized === 'finance' || normalized === 'finance_admin') return 'finance'
  return normalized
}

function extractNormalizedRoles(user: any): string[] {
  const rolesRaw = user?.roles || []
  if (!Array.isArray(rolesRaw)) {
    const singleRole = user?.role
    return singleRole ? [normalizeRoleName(String(singleRole))] : []
  }
  const roles = rolesRaw
    .map((ur: any) => {
      let roleValue: string
      if (typeof ur === 'string') {
        roleValue = ur
      } else if (ur && typeof ur === 'object') {
        const r = ur.role
        roleValue = typeof r === 'string' ? r : (r?.name != null ? String(r.name) : (ur?.name != null ? String(ur.name) : ''))
      } else {
        roleValue = String(ur ?? '')
      }
      return normalizeRoleName(roleValue)
    })
    .filter(Boolean)
  return Array.from(new Set(roles))
}

function getPrimaryRole(roles: string[]): string | null {
  if (roles.includes('admin')) return 'admin'
  const priority = ['program_director', 'finance', 'support', 'mentor', 'analyst', 'institution_admin', 'organization_admin', 'sponsor_admin', 'employer', 'mentee', 'student']
  for (const r of priority) {
    if (roles.includes(r)) return r
  }
  return roles[0] || null
}

function getDashboardForRole(role: string | null): string {
  switch (role) {
    case 'admin': return '/dashboard/admin'
    case 'program_director': return '/dashboard/director'
    case 'mentor': return '/dashboard/mentor'
    case 'analyst': return '/dashboard/analyst'
    case 'institution_admin': return '/dashboard/institution'
    case 'organization_admin': return '/dashboard/institution'
    case 'sponsor_admin': return '/dashboard/sponsor'
    case 'employer': return '/dashboard/employer'
    case 'finance': return '/dashboard/finance'
    case 'support': return '/support/dashboard'
    case 'mentee':
    case 'student': return '/dashboard/student'
    default: return '/dashboard/student'
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const access_token = body?.access_token;
    const refresh_token = body?.refresh_token;
    const user = body?.user;

    if (!access_token || typeof access_token !== 'string') {
      return NextResponse.json(
        { error: 'Missing access_token' },
        { status: 400 }
      );
    }

    const nextResponse = NextResponse.json({ ok: true }, { status: 200 });

    // In production (HTTPS or behind TLS proxy), cookies must have Secure or browsers may drop them
    const proto = request.headers.get('x-forwarded-proto') ?? request.headers.get('x-url-scheme') ?? (request.url.startsWith('https') ? 'https' : null);
    const isSecure = proto === 'https';

    const cookieOptions = {
      secure: isSecure,
      sameSite: 'lax' as const,
      maxAge: 60 * 60 * 24 * 30,
      path: '/',
    };

    nextResponse.cookies.set('access_token', access_token, {
      ...cookieOptions,
      httpOnly: false,
    });

    if (refresh_token && typeof refresh_token === 'string') {
      nextResponse.cookies.set('refresh_token', refresh_token, {
        ...cookieOptions,
        httpOnly: true,
      });
    }

    // Set role cookies if user data provided
    if (user) {
      const normalizedRoles = extractNormalizedRoles(user)
      const primaryRole = getPrimaryRole(normalizedRoles)
      
      nextResponse.cookies.set('och_roles', JSON.stringify(normalizedRoles), {
        ...cookieOptions,
        httpOnly: false,
      })
      nextResponse.cookies.set('och_primary_role', primaryRole || '', {
        ...cookieOptions,
        httpOnly: false,
      })
      nextResponse.cookies.set('och_dashboard', getDashboardForRole(primaryRole), {
        ...cookieOptions,
        httpOnly: false,
      })
      
      const trackKey = user?.track_key || '';
      nextResponse.cookies.set('user_track', trackKey, {
        ...cookieOptions,
        httpOnly: false,
      })
    }

    return nextResponse;
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
