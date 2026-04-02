/**
 * Next.js API Route: Signup
 * Handles user registration and forwards to Django backend
 */

import { NextRequest, NextResponse } from 'next/server';
import type { SignupRequest } from '@/services/types';
import { logger } from '@/lib/logger';

export async function POST(request: NextRequest) {
  try {
    const body: SignupRequest = await request.json();
    const { email, password, first_name, last_name, role, country, passwordless } = body;

    logger('[Signup API] Received signup attempt:', { 
      email, 
      passwordLength: password?.length,
      first_name,
      last_name,
      role,
      country,
      passwordless
    });

    // Forward registration to Django backend
    const djangoUrl = process.env.DJANGO_API_URL || process.env.NEXT_PUBLIC_DJANGO_API_URL;
    const apiUrl = `http://localhost:8000/api/auth/register`;
    logger('[Signup API] Forwarding to API URL:', apiUrl);

    const apiResponse = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        first_name,
        last_name,
        role: role || 'student',
        country,
        passwordless: passwordless || false,
      }),
    });

    logger('[Signup API] API response status:', apiResponse.status);

    if (!apiResponse.ok) {
      const statusCode = apiResponse.status;
      const text = await apiResponse.text();
      let backendBody: { detail?: string; error?: string } = {};
      try {
        backendBody = text ? JSON.parse(text) : {};
      } catch {
        backendBody = { detail: text || 'Request failed' };
      }
      const backendDetail = backendBody.detail || backendBody.error || '';
      logger('[Signup API] API registration failed:', statusCode, backendDetail || text?.slice(0, 200));
      
      const isBackendError = statusCode >= 500;
      const clientStatus = isBackendError ? 502 : statusCode;
      const userMessage = isBackendError
        ? 'The registration service is temporarily unavailable. Please try again in a moment.'
        : statusCode === 400
          ? backendDetail || 'Invalid registration data.'
          : 'Registration failed.';
      
      return NextResponse.json(
        {
          error: isBackendError ? 'Service temporarily unavailable' : 'Registration failed',
          detail: userMessage,
          code: isBackendError ? 'BAD_GATEWAY' : undefined,
          ...(process.env.NODE_ENV === 'development' && backendDetail ? { debug: backendDetail } : {}),
        },
        { status: clientStatus }
      );
    }

    const apiData = await apiResponse.json();
    logger('[Signup API] API response keys:', Object.keys(apiData));

    // Return successful registration response
    return NextResponse.json({
      detail: apiData.detail || apiData.message || 'Registration successful',
      user_id: apiData.user_id,
      message: apiData.message,
      redirect_url: apiData.redirect_url,
      requires_profiling: apiData.requires_profiling,
    });

  } catch (error: any) {
    logger('[Signup API] Unexpected error:', error);
    return NextResponse.json(
      {
        error: 'Registration failed',
        detail: 'An unexpected error occurred during registration.',
        code: 'INTERNAL_ERROR',
      },
      { status: 500 }
    );
  }
}
