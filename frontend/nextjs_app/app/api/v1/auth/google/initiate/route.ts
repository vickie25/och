/**
 * Next.js API Route: Google OAuth Initiate
 * Proxies Google OAuth initiation requests to Django backend
 */

import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';

/** Server-side only: prefer internal Docker URL, then API URL, then public (may be wrong inside containers). */
function djangoBaseForServerFetch(): string {
  const raw =
    process.env.DJANGO_INTERNAL_URL ||
    process.env.DJANGO_API_URL ||
    process.env.NEXT_PUBLIC_DJANGO_API_URL ||
    'http://localhost:8000';
  const trimmed = raw.replace(/\/$/, '');
  try {
    const u = new URL(trimmed.includes('://') ? trimmed : `http://${trimmed}`);
    return u.toString().replace(/\/$/, '');
  } catch {
    return trimmed;
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const role = searchParams.get('role');
    const mode = searchParams.get('mode');

    logger('[Google OAuth Initiate] Request:', { role, mode });

    const djangoUrl = djangoBaseForServerFetch();
    const apiUrl = new URL('/api/v1/auth/google/initiate', djangoUrl);
    
    // Add query parameters
    if (role) apiUrl.searchParams.set('role', role);
    if (mode) apiUrl.searchParams.set('mode', mode);

    logger('[Google OAuth Initiate] Forwarding to:', apiUrl.toString());

    const response = await fetch(apiUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      'User-Agent': request.headers.get('user-agent') || '',
      'X-Forwarded-For': request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || '',
        'X-Forwarded-Proto': request.headers.get('x-forwarded-proto') || 'http',
        'X-Forwarded-Host': request.headers.get('x-forwarded-host') || 'localhost:3000',
      },
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

      return NextResponse.json(
        {
          error: 'Failed to initiate Google OAuth',
          detail,
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    logger('[Google OAuth Initiate] Success:', { hasAuthUrl: !!data.auth_url, hasState: !!data.state });

    return NextResponse.json(data);

  } catch (error: any) {
    logger('[Google OAuth Initiate] Unexpected error:', error);

    const msg = error?.message || 'An unexpected error occurred';
    const hint =
      /fetch failed|ECONNREFUSED|ENOTFOUND|network/i.test(msg) || msg.includes('Failed to fetch')
        ? ' Check that Django is running and DJANGO_API_URL / DJANGO_INTERNAL_URL points to it (e.g. http://localhost:8000 or http://django:8000 in Docker).'
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
