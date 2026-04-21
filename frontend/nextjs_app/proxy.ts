/**
 * Next.js Proxy (formerly middleware)
 * Handles authentication checks and RBAC-based route protection
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { normalizeRoleName } from './lib/rbacFromAuthPayload';

// Routes that always require authentication
const protectedRoutes = [
  '/dashboard',
  '/finance',
  '/support',
  '/support/dashboard',
  '/support/tickets',
  '/support/settings',
  '/support/problem-codes',
  '/profiling',
  '/onboarding',
  '/coaching',
  '/sponsor',
  '/analyst',
  '/mentor/dashboard',
];

// Public routes that are allowed without login.
// Institution onboarding must be reachable from invite links.
const openRoutes: string[] = ['/onboarding/institution', '/onboarding/employer'];
const authRoutes = ['/login', '/register'];

function getLoginRouteForPath(pathname: string) {
  if (pathname.startsWith('/dashboard/director')) return '/login/director'
  if (pathname.startsWith('/dashboard/admin')) return '/login/admin'
  if (pathname.startsWith('/dashboard/mentor')) return '/login/mentor'
  if (pathname.startsWith('/dashboard/sponsor')) return '/login/sponsor'
  if (pathname.startsWith('/dashboard/institution')) return '/login/institution'
  if (pathname.startsWith('/dashboard/analyst') || pathname.startsWith('/dashboard/analytics')) return '/login/analyst'
  if (pathname.startsWith('/dashboard/employer') || pathname.startsWith('/dashboard/marketplace')) return '/login/employer'
  if (pathname.startsWith('/dashboard/finance')) return '/login/finance'
  if (pathname.startsWith('/support')) return '/login/support'
  if (pathname.startsWith('/students/')) return '/login'
  return '/login'
}

function parseRolesCookie(raw: string | undefined): string[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      return parsed.map((r: string) => {
        const normalized = String(r).toLowerCase().trim()
        // Map all role variations to standard frontend role names
        if (normalized === 'finance_admin' || normalized === 'financeadmin') return 'finance'
        if (normalized === 'sponsor_admin' || normalized === 'sponsoremployer admin' || normalized === 'sponsor') return 'sponsor_admin'
        if (normalized === 'institution_admin' || normalized === 'institution admin' || normalized === 'institutional_admin') return 'institution_admin'
        if (normalized === 'organization_admin' || normalized === 'organization admin') return 'organization_admin'
        if (normalized === 'program_director' || normalized === 'program director' || normalized === 'director') return 'program_director'
        if (normalized === 'mentee') return 'mentee'
        if (normalized === 'student') return 'student'
        if (normalized === 'mentor') return 'mentor'
        if (normalized === 'admin') return 'admin'
        if (normalized === 'analyst') return 'analyst'
        if (normalized === 'employer') return 'employer'
        if (normalized === 'support') return 'support'
        return String(r)
      })
    }
  } catch {}
  return raw.split(',').map(s => {
    const normalized = s.trim().toLowerCase()
    if (normalized === 'finance_admin' || normalized === 'financeadmin') return 'finance'
    if (normalized === 'sponsor_admin' || normalized === 'sponsor' || normalized === 'sponsoremployer admin') return 'sponsor_admin'
    if (normalized === 'institution_admin' || normalized === 'institution admin') return 'institution_admin'
    if (normalized === 'organization_admin' || normalized === 'organization admin') return 'organization_admin'
    if (normalized === 'program_director' || normalized === 'program director' || normalized === 'director') return 'program_director'
    return s.trim()
  }).filter(Boolean)
}

function dashboardForRole(role: string | null): string {
  switch (role) {
    case 'admin': return '/dashboard/admin'
    case 'program_director': return '/dashboard/director'
    case 'mentor': return '/dashboard/mentor'
    case 'analyst': return '/dashboard/analyst'
    case 'sponsor_admin': return '/dashboard/sponsor'
    case 'institution_admin':
    case 'organization_admin':
      return '/dashboard/institution'
    case 'employer': return '/dashboard/employer'
    case 'finance':
    case 'finance_admin':
      return '/dashboard/finance'
    case 'support': return '/support/dashboard'
    case 'mentee':
    case 'student':
    default:
      return '/dashboard/student'
  }
}

function canAccess(pathname: string, roles: string[]): boolean {
  // Normalize all roles to lowercase for comparison
  const normalizedRoles = roles.map(r => r.toLowerCase().trim())
  
  // Admin has access to everything
  if (normalizedRoles.includes('admin')) return true

  if (pathname.startsWith('/students/')) {
    return normalizedRoles.includes('student') || normalizedRoles.includes('mentee')
  }

  if (pathname.startsWith('/sponsor/')) {
    return normalizedRoles.includes('sponsor') || normalizedRoles.includes('sponsor_admin') || 
           normalizedRoles.includes('institution_admin') || normalizedRoles.includes('organization_admin')
  }

  if (pathname === '/dashboard' || pathname.startsWith('/dashboard/')) {
    if (pathname.startsWith('/dashboard/director')) return normalizedRoles.includes('program_director') || normalizedRoles.includes('director')
    if (pathname.startsWith('/dashboard/admin')) return normalizedRoles.includes('admin')
    if (pathname.startsWith('/dashboard/mentor')) return normalizedRoles.includes('mentor')
    if (pathname.startsWith('/dashboard/sponsor')) {
      return normalizedRoles.includes('sponsor_admin') || normalizedRoles.includes('sponsor') ||
             normalizedRoles.includes('institution_admin') || normalizedRoles.includes('organization_admin')
    }
    if (pathname.startsWith('/dashboard/institution')) {
      return normalizedRoles.includes('institution_admin') || normalizedRoles.includes('organization_admin') || 
             normalizedRoles.includes('sponsor_admin') || normalizedRoles.includes('sponsor')
    }
    if (pathname.startsWith('/dashboard/analyst')) return normalizedRoles.includes('analyst')
    if (pathname.startsWith('/dashboard/analytics')) return normalizedRoles.includes('analyst') || normalizedRoles.includes('program_director') || normalizedRoles.includes('director')
    if (pathname.startsWith('/dashboard/employer') || pathname.startsWith('/dashboard/marketplace')) return normalizedRoles.includes('employer')
    if (pathname.startsWith('/dashboard/finance')) return normalizedRoles.includes('finance') || normalizedRoles.includes('finance_admin')
    // Student dashboard is the fallback - allow all authenticated users
    return normalizedRoles.includes('student') || normalizedRoles.includes('mentee') || normalizedRoles.length > 0
  }
  return true
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get('access_token')?.value;
  const hasToken = !!accessToken;
  const rolesCookie = request.cookies.get('och_roles')?.value;
  const primaryRoleCookie = request.cookies.get('och_primary_role')?.value || null;
  const dashboardCookie = request.cookies.get('och_dashboard')?.value || null;
  let roles = parseRolesCookie(rolesCookie);
  // If `och_roles` was empty but primary role cookie survived (cookie size / legacy writers), recover RBAC.
  if (!roles.length && primaryRoleCookie) {
    roles = [normalizeRoleName(primaryRoleCookie)];
  }
  let home = dashboardCookie || dashboardForRole(primaryRoleCookie);
  
  if (roles.includes('mentor') && (!home || home === '/dashboard/student')) {
    home = '/dashboard/mentor';
  }
  if (roles.includes('support') && (!home || home === '/dashboard/student')) {
    home = '/support/dashboard';
  }

  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isOpenRoute = openRoutes.some(route => pathname.startsWith(route));
  const isAuthRoute = authRoutes.some(route => pathname.startsWith(route));
  const loginPath = getLoginRouteForPath(pathname);
  const isSpecificLoginRoute = pathname.match(/^\/login\/(mentor|director|admin|student|sponsor|institution|analyst|employer|finance)$/);

  if (isProtectedRoute && !isOpenRoute && !hasToken) {
    const loginUrl = new URL(loginPath, request.url);
    loginUrl.searchParams.set('redirect', `${pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthRoute) {
    if (isSpecificLoginRoute) {
      return NextResponse.next();
    }
    const isRoleLoginPath = pathname.match(/^\/login\/(support|mentor|director|admin|student|sponsor|institution|analyst|employer|finance)(\/)?$/);
    if (hasToken && home && (pathname === '/login' || pathname === '/login/' || isRoleLoginPath)) {
      return NextResponse.redirect(new URL(home, request.url));
    }
    return NextResponse.next();
  }

  if (hasToken && (pathname === '/dashboard/mfa-required' || pathname.startsWith('/dashboard/mfa-required/'))) {
    return NextResponse.next();
  }

  // Support users must never see student dashboard — redirect to support dashboard
  if (hasToken && roles.includes('support') && pathname.startsWith('/dashboard/student')) {
    return NextResponse.redirect(new URL('/support/dashboard', request.url));
  }

  if (hasToken && pathname.startsWith('/dashboard') && roles.length > 0 && !pathname.startsWith('/dashboard/student')) {
    if (pathname === '/dashboard' || pathname === '/dashboard/') {
      return NextResponse.redirect(new URL(home, request.url));
    }

    if (!canAccess(pathname, roles)) {
      let redirectHome = home;
      if (roles.includes('mentor') && (!redirectHome || redirectHome === '/dashboard/student')) {
        redirectHome = '/dashboard/mentor';
      }
      return NextResponse.redirect(new URL(redirectHome, request.url));
    }
  }

  return NextResponse.next();
}

export default middleware;

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
};
