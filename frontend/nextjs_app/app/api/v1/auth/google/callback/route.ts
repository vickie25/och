/**
 * Next.js API Route: Google OAuth Callback
 * Proxies Google OAuth callback requests to Django backend
 */

import { NextRequest, NextResponse } from 'next/server';
import { logger } from '@/lib/logger';

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

    // Forward to Django backend
    const djangoUrl = process.env.DJANGO_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
    const apiUrl = new URL('/api/v1/auth/google/callback', djangoUrl);

    logger('[Google OAuth Callback] Forwarding to:', apiUrl.toString());

    const response = await fetch(apiUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': request.headers.get('user-agent') || '',
        'X-Forwarded-For': request.headers.get('x-forwarded-for') || request.headers.get('x-real-ip') || '',
        'X-Forwarded-Proto': request.headers.get('x-forwarded-proto') || 'http',
        'X-Forwarded-Host': request.headers.get('x-forwarded-host') || 'localhost:3000',
      },
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
      
      return NextResponse.json(
        { 
          error: 'Failed to complete Google OAuth',
          detail: errorText || 'Unknown error'
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    logger('[Google OAuth Callback] Success:', { 
      hasAccessToken: !!data.access_token,
      hasUser: !!data.user,
      accountCreated: data.account_created,
      accountActivated: data.account_activated
    });

    return NextResponse.json(data);

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
