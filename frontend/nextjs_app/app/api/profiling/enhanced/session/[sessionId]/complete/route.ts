import { NextRequest, NextResponse } from 'next/server'

// In Docker, `localhost` points at the Next.js container. Prefer the internal service URL.
const FASTAPI_URL =
  process.env.FASTAPI_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_FASTAPI_API_URL ||
  'http://localhost:8001'

function buildAuthHeader(request: NextRequest): string | null {
  const hdr = request.headers.get('authorization')
  if (hdr) return hdr
  const cookieToken = request.cookies.get('access_token')?.value
  if (cookieToken) return `Bearer ${cookieToken}`
  return null
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { sessionId } = await context.params
    const authHeader = buildAuthHeader(request)

    const res = await fetch(
      `${FASTAPI_URL}/api/v1/profiling/enhanced/session/${sessionId}/complete`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
        // FastAPI endpoint doesn’t need a body, but keep compatibility.
        body: '{}',
        signal: AbortSignal.timeout(15000),
      }
    )

    const text = await res.text()
    if (!res.ok) {
      return NextResponse.json(
        { error: text || 'Failed to complete enhanced profiling session' },
        { status: res.status }
      )
    }

    const data = text ? JSON.parse(text) : {}
    return NextResponse.json(data)
  } catch (err: any) {
    console.error('[profiling/enhanced/session/complete] Proxy error:', err?.message || err)
    return NextResponse.json(
      { error: 'Profiling service is temporarily unavailable. Please try again later.' },
      { status: 503 }
    )
  }
}

