/**
 * Next.js API Route: GET /api/auth/me
 *
 * Proxies the request to Django's /api/v1/auth/me endpoint using the
 * access_token stored in the HttpOnly cookie set during login.
 *
 * Error contract:
 *  - 401 from Django  → 401 here  (useAuth will clear tokens — token is genuinely invalid)
 *  - 5xx / network   → 503 here  (useAuth must NOT clear tokens — transient error)
 *  - No cookie        → 401 here  (no session at all)
 */

import { NextRequest, NextResponse } from 'next/server';

const DJANGO_API_URL =
  process.env.NEXT_PUBLIC_DJANGO_API_URL ||
  process.env.DJANGO_INTERNAL_URL ||
  'http://django:8000';

export async function GET(request: NextRequest) {
  // Read the access token from the HttpOnly cookie set during login
  const accessToken = request.cookies.get('access_token')?.value;

  if (!accessToken) {
    return NextResponse.json(
      { error: 'Authentication required', code: 'no_token' },
      { status: 401 }
    );
  }

  try {
    const djangoUrl = `${DJANGO_API_URL}/api/v1/auth/me`;

    const djangoResponse = await fetch(djangoUrl, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        // Forward real client IP for audit logging
        'X-Forwarded-For':
          request.headers.get('x-forwarded-for') ||
          request.headers.get('x-real-ip') ||
          '',
      },
      // Short timeout — this is on the critical login path
      signal: AbortSignal.timeout(8000),
    });

    const data = await djangoResponse.json().catch(() => null);

    if (djangoResponse.status === 401) {
      // Token is genuinely invalid — tell the client to clear it
      return NextResponse.json(
        { error: 'Session expired', code: 'token_invalid' },
        { status: 401 }
      );
    }

    if (!djangoResponse.ok) {
      // Django 4xx (other than 401) or 5xx — do NOT clear token (transient)
      console.error(
        `[/api/auth/me] Django returned ${djangoResponse.status}:`,
        data
      );
      return NextResponse.json(
        { error: 'Service temporarily unavailable', code: 'django_error' },
        { status: 503 }
      );
    }

    // Success — return Django's response as-is
    return NextResponse.json(data, { status: 200 });
  } catch (err: any) {
    const isTimeout =
      err?.name === 'TimeoutError' || err?.name === 'AbortError';
    const isNetwork =
      err?.cause?.code === 'ECONNREFUSED' ||
      err?.message?.includes('fetch failed') ||
      err?.message?.includes('ECONNREFUSED');

    console.error('[/api/auth/me] Proxy error:', err?.message || err);

    // Network / timeout errors — do NOT return 401 (would clear valid tokens)
    return NextResponse.json(
      {
        error: isTimeout
          ? 'Request timed out'
          : isNetwork
          ? 'Cannot reach auth service'
          : 'Internal error',
        code: isTimeout ? 'timeout' : isNetwork ? 'network_error' : 'unknown',
      },
      { status: 503 }
    );
  }
}
