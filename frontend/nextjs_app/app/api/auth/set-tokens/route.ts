/**
 * Set auth cookies after MFA complete (or when tokens are obtained outside login API).
 * Middleware reads access_token + och_* cookies; role cookies must match Django hints
 * when `user.roles` is empty (same logic as /api/auth/login).
 */
import { NextResponse } from 'next/server';
import {
  resolveNormalizedRoles,
  getPrimaryRole,
  getDashboardForRole,
} from '@/lib/rbacFromAuthPayload';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const access_token = body?.access_token;
    const refresh_token = body?.refresh_token;
    const user = body?.user;
    const primary_role =
      typeof body?.primary_role === 'string' ? body.primary_role : null;

    if (!access_token || typeof access_token !== 'string') {
      return NextResponse.json(
        { error: 'Missing access_token' },
        { status: 400 }
      );
    }

    const nextResponse = NextResponse.json({ ok: true }, { status: 200 });

    const proto =
      request.headers.get('x-forwarded-proto') ??
      request.headers.get('x-url-scheme') ??
      (request.url.startsWith('https') ? 'https' : null);
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

    // Role cookies: set when we have a user and/or Django sent `primary_role` (MFA edge cases).
    // Does not mint or validate tokens — only mirrors hints for middleware / client routing.
    const shouldSetRoleCookies = Boolean(user) || Boolean(primary_role);
    if (shouldSetRoleCookies) {
      const normalizedRoles = resolveNormalizedRoles(user ?? null, {
        primary_role,
        user: (user as Record<string, unknown> | undefined) ?? undefined,
      });
      const primaryRole = getPrimaryRole(normalizedRoles);

      nextResponse.cookies.set('och_roles', JSON.stringify(normalizedRoles), {
        ...cookieOptions,
        httpOnly: false,
      });
      nextResponse.cookies.set('och_primary_role', primaryRole || '', {
        ...cookieOptions,
        httpOnly: false,
      });
      nextResponse.cookies.set('och_dashboard', getDashboardForRole(primaryRole), {
        ...cookieOptions,
        httpOnly: false,
      });

      const trackKey =
        user && typeof user === 'object'
          ? String((user as { track_key?: string }).track_key || '')
          : '';
      nextResponse.cookies.set('user_track', trackKey, {
        ...cookieOptions,
        httpOnly: false,
      });
    }

    return nextResponse;
  } catch {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
