/**
 * Next.js API Route: Google OAuth Callback
 * Proxies Google OAuth callback requests to Django backend
 */

import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';
import { djangoBaseForServerFetch, forwardSetCookies } from '@/lib/djangoServerBase';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { code, state, device_fingerprint, device_name, mode, role } = body;

    logger('[Google OAuth Callback] Request:', { 
      hasCode: !!code, 
      hasState: !!state, 
      device_fingerprint: device_fingerprint ? 'present' : 'missing',
      device_name: device_name || 'missing'
    });

    const djangoUrl = djangoBaseForServerFetch();
    const apiUrl = new URL('/api/v1/auth/google/callback', djangoUrl);

    logger('[Google OAuth Callback] Forwarding to:', apiUrl.toString());

    const forwardHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'User-Agent': request.headers.get('user-agent') || '',
      'X-Forwarded-For':
        request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || '',
      'X-Forwarded-Proto': request.headers.get('x-forwarded-proto') || 'http',
    };
    const origin = request.headers.get('origin');
    if (origin) forwardHeaders.Origin = origin;
    const referer = request.headers.get('referer');
    if (referer) forwardHeaders.Referer = referer;
    const cookie = request.headers.get('cookie');
    if (cookie) {
      forwardHeaders.Cookie = cookie;
    }

    const response = await fetch(apiUrl.toString(), {
      method: 'POST',
      headers: forwardHeaders,
      body: JSON.stringify({
        code,
        state,
        device_fingerprint,
        device_name,
        mode,
        role,
      }),
    });

    logger('[Google OAuth Callback] Backend response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      logger('[Google OAuth Callback] Backend error:', errorText);

      let detail = errorText || 'Unknown error';
      try {
        const parsed = JSON.parse(errorText) as { detail?: string };
        if (typeof parsed?.detail === 'string') detail = parsed.detail;
      } catch {
        /* keep raw */
      }

      const errRes = NextResponse.json(
        {
          error: 'Failed to complete Google OAuth',
          detail,
        },
        { status: response.status }
      );
      forwardSetCookies(response, errRes);
      return errRes;
    }

    const data = await response.json();
    logger('[Google OAuth Callback] Success:', { 
      hasAccessToken: !!data.access_token,
      hasUser: !!data.user,
      accountCreated: data.account_created,
      accountActivated: data.account_activated
    });

    const okRes = NextResponse.json(data);
    forwardSetCookies(response, okRes);
    return okRes;

  } catch (error: any) {
    logger('[Google OAuth Callback] Unexpected error:', error);
    
    return NextResponse.json(
      {
        error: 'Failed to complete Google sign-in',
        detail: error?.message || 'An unexpected error occurred'
      },
      { status: 500 }
    );
  }
}
