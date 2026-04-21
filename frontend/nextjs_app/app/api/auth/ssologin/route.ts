/**
 * Next.js API Route: SSO Login
 * Sets auth cookies from OAuth tokens returned by backend (Django).
 * Uses the same RBAC resolver as `/api/auth/login` and `/api/auth/set-tokens`.
 */

import { NextRequest, NextResponse } from 'next/server';
import {
  resolveNormalizedRoles,
  getPrimaryRole,
  getDashboardForRole,
} from '@/lib/rbacFromAuthPayload';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { access_token, refresh_token, user } = body || {};
    const primary_role =
      typeof body?.primary_role === 'string' && body.primary_role.trim()
        ? body.primary_role
        : null;

    if (!access_token || !user) {
      return NextResponse.json(
        {
          error: 'Invalid SSO payload',
          detail: 'Missing access_token or user in request body',
        },
        { status: 400 }
      );
    }

    const nextResponse = NextResponse.json({
      user,
      access_token,
    });

    const proto =
      request.headers.get('x-forwarded-proto') ??
      request.headers.get('x-url-scheme') ??
      (request.nextUrl.protocol === 'https:' ? 'https' : 'http');
    const isSecure = proto === 'https';
    const cookieBase = {
      secure: isSecure,
      sameSite: 'lax' as const,
      path: '/',
      maxAge: 60 * 60 * 24 * 30,
    };

    const normalizedRoles = resolveNormalizedRoles(user, {
      primary_role,
      user: user as Record<string, unknown>,
    });
    const primaryRole = getPrimaryRole(normalizedRoles);

    nextResponse.cookies.set('och_roles', JSON.stringify(normalizedRoles), {
      ...cookieBase,
      httpOnly: false,
    });
    nextResponse.cookies.set('och_primary_role', primaryRole || '', {
      ...cookieBase,
      httpOnly: false,
    });
    nextResponse.cookies.set('och_dashboard', getDashboardForRole(primaryRole), {
      ...cookieBase,
      httpOnly: false,
    });

    const trackKey =
      user && typeof user === 'object' && 'track_key' in user
        ? String((user as { track_key?: string }).track_key || '')
        : '';
    nextResponse.cookies.set('user_track', trackKey, {
      ...cookieBase,
      httpOnly: false,
    });

    nextResponse.cookies.set('access_token', access_token, {
      ...cookieBase,
      httpOnly: false,
    });

    if (refresh_token) {
      nextResponse.cookies.set('refresh_token', refresh_token, {
        ...cookieBase,
        httpOnly: true,
      });
    }

    return nextResponse;
  } catch (error: unknown) {
    console.error('SSO Login API route error:', error);
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json(
      {
        error: 'SSO login failed',
        detail: message,
      },
      { status: 500 }
    );
  }
}
