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
    const body = await request.json().catch(() => ({}))

    const res = await fetch(`${FASTAPI_URL}/api/v1/profiling/session/${sessionId}/respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(8000),
    })

    const text = await res.text()
    if (!res.ok) {
      return NextResponse.json(
        { error: text || 'Failed to submit response' },
        { status: res.status }
      )
    }

    // FastAPI returns JSON; be tolerant if it ever returns empty.
    const data = text ? JSON.parse(text) : {}
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[profiling/session/respond] Proxy error:', error)
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    )
  }
}

