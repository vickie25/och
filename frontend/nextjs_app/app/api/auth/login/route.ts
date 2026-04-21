/**
 * Next.js API Route: Login
 * Proxies credentials to Django and mirrors the same RBAC cookies as `/api/auth/set-tokens`
 * (shared resolver) so middleware and client fallbacks stay aligned.
 */

import { NextRequest, NextResponse } from 'next/server';
import type { LoginRequest } from '@/services/types';
import {
  resolveNormalizedRoles,
  getPrimaryRole,
  getDashboardForRole,
} from '@/lib/rbacFromAuthPayload';

export async function POST(request: NextRequest) {
  try {
    const body: LoginRequest = await request.json();
    const { email, password, device_fingerprint, device_name } = body;

    console.log('[Login API] Received login attempt:', { email, passwordLength: password?.length });

    // Forward authentication to Django backend.
    //
    // IMPORTANT: Use the full auth endpoint so the response includes RBAC roles.
    // The legacy `/v1/auth/login/simple` returns a minimal user object without roles,
    // which causes the frontend to default every user to the student dashboard.
    const djangoUrl =
      process.env.NEXT_PUBLIC_DJANGO_API_URL ||
      process.env.DJANGO_INTERNAL_URL ||
      process.env.DJANGO_API_URL ||
      'http://django:8000'
    const apiUrl = `${djangoUrl}/api/v1/auth/login`;
    console.log('[Login API] Forwarding to API URL:', apiUrl);
    console.log('[Login API] DJANGO_API_URL env:', process.env.DJANGO_API_URL);
    console.log('[Login API] DJANGO_INTERNAL_URL env:', process.env.DJANGO_INTERNAL_URL);
    console.log('[Login API] NEXT_PUBLIC_DJANGO_API_URL env:', process.env.NEXT_PUBLIC_DJANGO_API_URL);

    const apiResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        ...(device_fingerprint && { device_fingerprint }),
        ...(device_name && { device_name }),
      }),
    });

    console.log('[Login API] API response status:', apiResponse.status);

    if (!apiResponse.ok) {
      const statusCode = apiResponse.status;
      // Read body once as text so we can parse JSON or use as message (avoids "Body has already been read")
      const text = await apiResponse.text();
      let backendBody: { detail?: string; error?: string } = {};
      try {
        backendBody = text ? JSON.parse(text) : {};
      } catch {
        backendBody = { detail: text || 'Request failed' };
      }
      const backendDetail = backendBody.detail || backendBody.error || '';
      console.log('[Login API] API auth failed:', statusCode, backendDetail || text?.slice(0, 200));
      // 4xx: forward as-is with clear message; 5xx: return 502 with clear BAD_GATEWAY response
      const isBackendError = statusCode >= 500;
      const clientStatus = isBackendError ? 502 : statusCode === 403 ? 403 : 401;
      const userMessage = isBackendError
        ? 'The login service is temporarily unavailable. Please try again in a moment.'
        : statusCode === 401
          ? 'Invalid email or password.'
          : statusCode === 403
            ? (backendDetail || 'Account cannot sign in.')
            : 'Login failed.';
      return NextResponse.json(
        {
          error: isBackendError ? 'Service temporarily unavailable' : 'Login failed',
          detail: userMessage,
          code: isBackendError ? 'BAD_GATEWAY' : undefined,
          ...(process.env.NODE_ENV === 'development' && backendDetail ? { debug: backendDetail } : {}),
        },
        { status: clientStatus }
      );
    }

    // Parse body once (already consumed above only when !ok)
    const apiData = await apiResponse.json();
    console.log('[Login API] API response status:', apiResponse.status);
    console.log('[Login API] API response keys:', Object.keys(apiData));
    console.log('[Login API] Has access_token:', !!apiData.access_token);
    console.log('[Login API] Has refresh_token:', !!apiData.refresh_token);
    console.log('[Login API] Has mfa_required:', !!apiData.mfa_required);

    // Check if MFA is required (backend sends preferred method: TOTP → email → SMS + list of user's methods)
    if (apiData.mfa_required) {
      console.log('[Login API] MFA required for user');
      return NextResponse.json({
        mfa_required: true,
        session_id: apiData.session_id,
        refresh_token: apiData.refresh_token,
        mfa_method: apiData.mfa_method || 'totp',
        mfa_methods_available: Array.isArray(apiData.mfa_methods_available) ? apiData.mfa_methods_available : undefined,
        detail: apiData.detail || 'MFA required',
      }, { status: 200 });
    }

    // Use the API response data
    const loginResponse = apiData;
    console.log('[Login API] API auth successful for user:', loginResponse.user?.email);
    console.log('[Login API] Full login response:', JSON.stringify(loginResponse, null, 2));

    // Ensure access_token exists
    if (!loginResponse.access_token) {
      console.error('[Login API] ERROR: No access_token in Django response!');
      console.error('[Login API] Response structure:', JSON.stringify(loginResponse, null, 2));
      return NextResponse.json(
        {
          error: 'Login failed',
          detail: 'No access token received from backend. Please check backend logs.',
        },
        { status: 500 }
      );
    }

    // Create the response (include refresh_token so client can store it for auto-refresh)
    const nextResponse = NextResponse.json({
      user: loginResponse.user,
      access_token: loginResponse.access_token,
      refresh_token: loginResponse.refresh_token,
    });
    
    console.log('[Login API] Next.js response includes access_token:', !!nextResponse.body);

    // Detect HTTPS for proper cookie secure flag
    const proto = request.headers.get('x-forwarded-proto') ?? request.headers.get('x-url-scheme') ?? (request.url.startsWith('https') ? 'https' : null);
    const isSecure = proto === 'https';
    console.log('[Login API] Setting cookies with secure:', isSecure, 'proto:', proto);

    // RBAC cookies: same resolver as set-tokens. Non-HttpOnly so login UI can read `och_dashboard`
    // from document.cookie when `/auth/me` is slow; API access is still gated by the JWT.
    const lr = loginResponse as {
      user?: Record<string, unknown>;
      primary_role?: string;
    };
    const normalizedRoles = resolveNormalizedRoles(lr.user ?? null, {
      primary_role:
        typeof lr.primary_role === 'string' && lr.primary_role.trim() ? lr.primary_role : null,
      user: lr.user ?? null,
    });
    const primaryRole = getPrimaryRole(normalizedRoles);
    console.log('[Login API] RBAC cookies — roles:', normalizedRoles, 'primary:', primaryRole);
    nextResponse.cookies.set('och_roles', JSON.stringify(normalizedRoles), {
      httpOnly: false,
      secure: isSecure,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30,
      path: '/',
    });
    nextResponse.cookies.set('och_primary_role', primaryRole || '', {
      httpOnly: false,
      secure: isSecure,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30,
      path: '/',
    });
    nextResponse.cookies.set('och_dashboard', getDashboardForRole(primaryRole), {
      httpOnly: false,
      secure: isSecure,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30,
      path: '/',
    });
    // Try to get track info from user data
    const trackKey = loginResponse.user?.track_key || '';

    nextResponse.cookies.set('user_track', trackKey, {
      httpOnly: false, // Allow client-side access
      secure: isSecure,
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 * 30,
      path: '/',
    })

    // Set cookies directly on the response object
    if (loginResponse.access_token) {
      nextResponse.cookies.set('access_token', loginResponse.access_token, {
        httpOnly: false, // Allow client-side access for Authorization header
        secure: isSecure,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 30, // 30 days (matches refresh token)
        path: '/',
      });
    }

    if (loginResponse.refresh_token) {
      nextResponse.cookies.set('refresh_token', loginResponse.refresh_token, {
        httpOnly: true,
        secure: isSecure,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 30, // 30 days
        path: '/',
      });
    }

    return nextResponse;
  } catch (error: any) {
    console.error('Login API route error:', error);
    console.error('Error stack:', error?.stack);
    console.error('Error message:', error?.message);

    // Check if it's a connection error
    const isConnectionError = 
      error?.message?.includes('fetch failed') ||
      error?.message?.includes('ECONNREFUSED') ||
      error?.code === 'ECONNREFUSED' ||
      error?.cause?.code === 'ECONNREFUSED';

    if (isConnectionError) {
      return NextResponse.json(
        {
          error: 'Connection failed',
          detail: 'Cannot connect to backend server. Please ensure the Django API is running on port 8000.',
        },
        { status: 503 }
      );
    }

    return NextResponse.json(
      {
        error: 'Login failed',
        detail: error?.message || 'An unexpected error occurred',
      },
      { status: 500 }
    );
  }
}

