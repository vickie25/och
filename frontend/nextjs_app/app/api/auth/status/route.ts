/**
 * Next.js API Route: Auth Status
 * Returns current authentication status
 */

import { NextRequest, NextResponse } from 'next/server';
import { getAccessToken } from '@/utils/auth';
import { djangoBaseForServerFetch } from '@/lib/djangoServerBase';

export async function GET(request: NextRequest) {
  try {
    const token = getAccessToken();

    if (!token) {
      return NextResponse.json({
        authenticated: false,
        user: null,
      });
    }

    // Try to get user info from Django
    const base = djangoBaseForServerFetch();
    const response = await fetch(`${base}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      signal: AbortSignal.timeout(8000),
    });

    if (response.ok) {
      const user = await response.json();
      return NextResponse.json({
        authenticated: true,
        user,
      });
    } else {
      return NextResponse.json({
        authenticated: false,
        user: null,
      });
    }
  } catch (error) {
    console.error('Auth status error:', error);
    return NextResponse.json({
      authenticated: false,
      user: null,
      error: 'Failed to check authentication status',
    }, { status: 500 });
  }
}
