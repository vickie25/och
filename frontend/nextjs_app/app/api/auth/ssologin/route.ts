/**
 * Next.js API Route: SSO Login
 * Sets auth cookies from OAuth tokens returned by backend (Django)
 */

import { NextRequest, NextResponse } from 'next/server';

function normalizeRoleName(roleName: string): string {
  const normalized = (roleName || '').toLowerCase().trim()
  if (normalized === 'program_director' || normalized === 'program director' || normalized === 'programdirector' || normalized === 'director') return 'program_director'
  if (normalized === 'mentee') return 'mentee'
  if (normalized === 'student') return 'student'
  if (normalized === 'mentor') return 'mentor'
  if (normalized === 'admin') return 'admin'
  if (normalized === 'sponsor_admin' || normalized === 'sponsor' || normalized === 'sponsor/employer admin' || normalized === 'sponsoremployer admin') return 'sponsor_admin'
  if (normalized === 'institution_admin' || normalized === 'institution admin' || normalized === 'institutional_admin' || normalized === 'institutional admin') return 'institution_admin'
  if (normalized === 'organization_admin' || normalized === 'organization admin') return 'organization_admin'
  if (normalized === 'analyst') return 'analyst'
  if (normalized === 'employer') return 'employer'
  if (normalized === 'finance' || normalized === 'finance_admin') return 'finance'
  return normalized
}

function extractNormalizedRoles(user: any): string[] {
  const rolesRaw = user?.roles || []
  if (!Array.isArray(rolesRaw)) return []
  const roles = rolesRaw
    .map((ur: any) => {
      let roleValue: string
      if (typeof ur === 'string') roleValue = ur
      else if (ur && typeof ur === 'object') {
        const r = ur.role
        roleValue = typeof r === 'string' ? r : (r?.name != null ? String(r.name) : (ur?.name != null ? String(ur.name) : ''))
      } else roleValue = String(ur ?? '')
      return normalizeRoleName(roleValue)
    })
    .filter(Boolean)
  return Array.from(new Set(roles))
}

function getPrimaryRole(roles: string[]): string | null {
  if (roles.includes('admin')) return 'admin'
  const priority = ['program_director', 'finance', 'support', 'mentor', 'analyst', 'institution_admin', 'organization_admin', 'sponsor_admin', 'employer', 'mentee', 'student']
  for (const r of priority) if (roles.includes(r)) return r
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
    case 'student':
    default:
      return '/dashboard/student'
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { access_token, refresh_token, user } = body || {};

    if (!access_token || !user) {
      return NextResponse.json({
        error: 'Invalid SSO payload',
        detail: 'Missing access_token or user in request body',
      }, { status: 400 });
    }

    const nextResponse = NextResponse.json({
      user,
      access_token,
    });

    // Match /api/auth/set-tokens: do not force Secure on plain HTTP (local Docker / http://localhost).
    const proto =
      request.headers.get('x-forwarded-proto') ??
      request.headers.get('x-url-scheme') ??
      (request.nextUrl.protocol === 'https:' ? 'https' : 'http')
    const isSecure = proto === 'https'
    const cookieBase = {
      secure: isSecure,
      sameSite: 'lax' as const,
      path: '/',
    }

    // RBAC cookies for middleware
    const normalizedRoles = extractNormalizedRoles(user)
    const primaryRole = getPrimaryRole(normalizedRoles)
    nextResponse.cookies.set('och_roles', JSON.stringify(normalizedRoles), {
      ...cookieBase,
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 30,
    })
    nextResponse.cookies.set('och_primary_role', primaryRole || '', {
      ...cookieBase,
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 30,
    })
    nextResponse.cookies.set('och_dashboard', getDashboardForRole(primaryRole), {
      ...cookieBase,
      httpOnly: true,
      maxAge: 60 * 60 * 24 * 30,
    })

    // Access token (readable by client for Authorization header)
    nextResponse.cookies.set('access_token', access_token, {
      ...cookieBase,
      httpOnly: false,
      maxAge: 60 * 15,
    })

    // Refresh token (HttpOnly for server refresh flow), optional
    if (refresh_token) {
      nextResponse.cookies.set('refresh_token', refresh_token, {
        ...cookieBase,
        httpOnly: true,
        maxAge: 60 * 60 * 24 * 30,
      })
    }

    return nextResponse;
  } catch (error: any) {
    console.error('SSO Login API route error:', error);
    return NextResponse.json({
      error: 'SSO login failed',
      detail: error?.message || 'Unknown error',
    }, { status: 500 })
  }
}
