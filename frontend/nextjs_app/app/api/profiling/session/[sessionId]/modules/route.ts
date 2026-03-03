import { NextRequest, NextResponse } from 'next/server'

const FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_API_URL || 'http://localhost:8001'

export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params
    const url = `${FASTAPI_URL}/api/v1/profiling/session/${sessionId}/modules`
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: errorText || 'Failed to fetch modules' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('Profiling modules proxy error:', error)
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    )
  }
}
