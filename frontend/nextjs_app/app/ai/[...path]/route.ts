import { NextRequest, NextResponse } from 'next/server'

// This route makes public `/ai/*` work everywhere (localhost, ngrok, prod)
// by proxying to FastAPI. In Docker, prefer the internal service URL.
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

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  try {
    const { path } = await context.params
    const authHeader = buildAuthHeader(request)

    // Incoming URL: /ai/<...path>?query
    // Forward to:    <FASTAPI_URL>/<...path>?query
    const upstream = new URL(`${FASTAPI_URL.replace(/\/$/, '')}/${path.join('/')}`)
    request.nextUrl.searchParams.forEach((value, key) => upstream.searchParams.append(key, value))

    const headers = new Headers(request.headers)
    headers.delete('host')
    if (authHeader) headers.set('authorization', authHeader)

    // NextRequest.body is a stream; only include for non-GET/HEAD.
    const method = request.method.toUpperCase()
    const hasBody = !['GET', 'HEAD'].includes(method)

    const res = await fetch(upstream.toString(), {
      method,
      headers,
      body: hasBody ? await request.text() : undefined,
      signal: AbortSignal.timeout(15000),
    })

    const text = await res.text()

    // Pass through status + content-type; return JSON when possible.
    const contentType = res.headers.get('content-type') || ''
    if (contentType.includes('application/json')) {
      return NextResponse.json(text ? JSON.parse(text) : {}, { status: res.status })
    }

    return new NextResponse(text, {
      status: res.status,
      headers: { 'content-type': contentType || 'text/plain' },
    })
  } catch (error: any) {
    console.error('[ai proxy] error:', error)
    return NextResponse.json({ error: error?.message || 'Proxy error' }, { status: 502 })
  }
}

export async function GET(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context)
}
export async function POST(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context)
}
export async function PUT(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context)
}
export async function PATCH(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context)
}
export async function DELETE(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  return proxy(request, context)
}

