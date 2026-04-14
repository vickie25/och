/**
 * Proxy for GET /api/v1/profiling/enhanced/questions
 * Returns profiling questions from FastAPI
 */

import { NextRequest, NextResponse } from 'next/server';

// In Docker, `localhost` points at the Next.js container. Prefer the internal service URL.
const FASTAPI_URL = process.env.FASTAPI_INTERNAL_URL || process.env.NEXT_PUBLIC_FASTAPI_API_URL;

export async function GET(request: NextRequest) {
  const authHeader =
    request.headers.get('authorization') ||
    (request.cookies.get('access_token')?.value
      ? `Bearer ${request.cookies.get('access_token')?.value}`
      : null);

  if (authHeader) {
    console.log('[profiling/auth] Token present. Length:', authHeader.length);
    console.log('[profiling/auth] Token preview:', authHeader.substring(0, 15), '...', authHeader.substring(authHeader.length - 10));
  } else {
    console.log('[profiling/auth] No Auth header found in request.');
  }

  
  try {

    console.log('[profiling/enhanced/questions] FASTAPI_URL:', FASTAPI_URL);
    console.log('[profiling/enhanced/questions] Auth header present:', !!authHeader);
    
    const res = await fetch(`${FASTAPI_URL}/api/v1/profiling/enhanced/questions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      signal: AbortSignal.timeout(5000),
    });
    console.log('[profiling/enhanced/questions] FastAPI response status:', res.status);


    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ error: 'Failed to load profiling questions' }));
      return NextResponse.json(errorData, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('[profiling/enhanced/questions] FastAPI error:', err?.message || err);
    return NextResponse.json(
      { error: 'Unable to connect to profiling service. Please ensure FastAPI is running.' },
      { status: 503 }
    );
  }
}
