import { NextRequest, NextResponse } from 'next/server'

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

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ sessionId: string }> }
) {
  try {
    const { sessionId } = await context.params
    const authHeader = buildAuthHeader(request)

    const res = await fetch(
      `${FASTAPI_URL}/api/v1/profiling/enhanced/session/${sessionId}/blueprint`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(authHeader ? { Authorization: authHeader } : {}),
        },
        signal: AbortSignal.timeout(15000),
      }
    )

    const text = await res.text()
    if (!res.ok) {
      return NextResponse.json(
        { error: text || 'Failed to fetch blueprint' },
        { status: res.status }
      )
    }

    const data = text ? JSON.parse(text) : {}
    return NextResponse.json(data)
  } catch (err: any) {
    console.error('[profiling/enhanced/session/blueprint] Proxy error:', err?.message || err)
    return NextResponse.json(
      { error: 'Profiling service is temporarily unavailable. Please try again later.' },
      { status: 503 }
    )
  }
}

