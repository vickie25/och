/**
 * Proxy for POST /api/v1/profiling/session/start
 * Starts a new profiling session via FastAPI
 */

import { NextRequest, NextResponse } from 'next/server';

// In Docker, `localhost` points at the Next.js container, not the host.
// Prefer the internal service URL when present.
const FASTAPI_URL = process.env.FASTAPI_INTERNAL_URL || process.env.NEXT_PUBLIC_FASTAPI_API_URL;

export async function POST(request: NextRequest) {
  const authHeader =
    request.headers.get('authorization') ||
    (request.cookies.get('access_token')?.value
      ? `Bearer ${request.cookies.get('access_token')?.value}`
      : null);
  
  try {
    if (!FASTAPI_URL) {
      return NextResponse.json(
        { error: 'Profiling service is not configured (missing FASTAPI url).' },
        { status: 503 }
      );
    }
    const body = await request.json();
    
    const res = await fetch(`${FASTAPI_URL}/api/v1/profiling/session/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ error: 'Failed to start profiling session' }));
      return NextResponse.json(errorData, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('[profiling/session/start] FastAPI error:', err?.message || err);
    return NextResponse.json(
      { error: 'Profiling service is temporarily unavailable. Please try again later.' },
      { status: 503 }
    );
  }
}
