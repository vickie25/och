/**
 * Next.js API Route: Google OAuth Initiate
 * Proxies Google OAuth initiation requests to Django backend
 */

import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';
import { djangoBaseForServerFetch, forwardSetCookies } from '@/lib/djangoServerBase';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const role = searchParams.get('role');
    const mode = searchParams.get('mode');

    logger('[Google OAuth Initiate] Request:', { role, mode });

    const djangoUrl = djangoBaseForServerFetch();
    const apiUrl = new URL('/api/v1/auth/google/initiate', djangoUrl);

    if (role) apiUrl.searchParams.set('role', role);
    if (mode) apiUrl.searchParams.set('mode', mode);

    logger('[Google OAuth Initiate] Forwarding to:', apiUrl.toString());

    // Do not forward X-Forwarded-Host: if Django ever uses USE_X_FORWARDED_HOST, the browser's
    // Host (e.g. localhost:3000) can trigger DisallowedHost against a production-only ALLOWED_HOSTS.
    const forwardHeaders: Record<string, string> = {
      Accept: 'application/json',
      'User-Agent': request.headers.get('user-agent') || '',
      'X-Forwarded-For':
        request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || '',
      'X-Forwarded-Proto': request.headers.get('x-forwarded-proto') || 'http',
    };
    const cookie = request.headers.get('cookie');
    if (cookie) {
      forwardHeaders.Cookie = cookie;
    }

    const response = await fetch(apiUrl.toString(), {
      method: 'GET',
      headers: forwardHeaders,
    });

    logger('[Google OAuth Initiate] Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      logger('[Google OAuth Initiate] Backend error:', errorText);

      let detail = errorText || 'Unknown error';
      try {
        const parsed = JSON.parse(errorText) as { detail?: string };
        if (typeof parsed?.detail === 'string') detail = parsed.detail;
      } catch {
        /* keep raw */
      }

      const errRes = NextResponse.json(
        {
          error: 'Failed to initiate Google OAuth',
          detail,
        },
        { status: response.status }
      );
      forwardSetCookies(response, errRes);
      return errRes;
    }

    const data = await response.json();
    logger('[Google OAuth Initiate] Success:', { hasAuthUrl: !!data.auth_url, hasState: !!data.state });

    const okRes = NextResponse.json(data);
    forwardSetCookies(response, okRes);
    return okRes;
  } catch (error: unknown) {
    logger('[Google OAuth Initiate] Unexpected error:', error);

    const msg = error instanceof Error ? error.message : 'An unexpected error occurred';
    const hint =
      /fetch failed|ECONNREFUSED|ENOTFOUND|network/i.test(msg) || msg.includes('Failed to fetch')
        ? ' Check that Django is running and DJANGO_INTERNAL_URL / DJANGO_API_URL points to it (e.g. http://localhost:8000 or http://django:8000 in Docker).'
        : '';

    return NextResponse.json(
      {
        error: 'Failed to initiate Google sign-in',
        detail: `${msg}${hint}`,
      },
      { status: 500 }
    );
  }
}
