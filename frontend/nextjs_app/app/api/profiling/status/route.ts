/**
 * Proxy for GET /api/v1/profiling/status
 * Tries FastAPI first; returns fallback when FastAPI is unavailable so the profiling page still loads.
 */

import { NextRequest, NextResponse } from 'next/server';

// In Docker, `localhost` points at the Next.js container. Prefer the internal service URL.
const FASTAPI_URL = process.env.FASTAPI_INTERNAL_URL || process.env.NEXT_PUBLIC_FASTAPI_API_URL;

function buildAuthHeader(request: NextRequest): string | null {
  const hdr = request.headers.get('authorization');
  if (hdr) return hdr;
  const cookieToken = request.cookies.get('access_token')?.value;
  if (cookieToken) return `Bearer ${cookieToken}`;
  return null;
}

function fallbackStatus() {
  return NextResponse.json({
    completed: false,
    session_id: null,
    has_active_session: false,
    progress: null,
    completed_at: null,
  });
}

export async function GET(request: NextRequest) {
  const authHeader = buildAuthHeader(request);
  try {
    if (!FASTAPI_URL) {
      return fallbackStatus();
    }
    const res = await fetch(`${FASTAPI_URL}/api/v1/profiling/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      signal: AbortSignal.timeout(8000),
    });
    if (!res.ok) {
      console.warn('[profiling/status] FastAPI returned', res.status);
      return fallbackStatus();
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.warn('[profiling/status] FastAPI unavailable:', err?.message || err);
    return fallbackStatus();
  }
}
