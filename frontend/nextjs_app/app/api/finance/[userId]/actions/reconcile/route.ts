import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/finance/[userId]/actions/reconcile
 * Proxies to Django POST /api/v1/finance/reconciliation/run/ (replaces mock).
 */
export async function POST(request: NextRequest) {
  const djangoUrl =
    process.env.DJANGO_API_URL ||
    process.env.NEXT_PUBLIC_DJANGO_API_URL;

  if (!djangoUrl) {
    return NextResponse.json(
      { error: 'DJANGO_API_URL not configured' },
      { status: 503 }
    );
  }

  const cookie = request.headers.get('cookie') ?? '';
  const accessToken = request.cookies.get('access_token')?.value ?? '';
  const authHeaders: Record<string, string> = {
    Cookie: cookie,
    'Content-Type': 'application/json',
  };
  if (accessToken) authHeaders['Authorization'] = `Bearer ${accessToken}`;

  let body: Record<string, unknown> = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  try {
    const resp = await fetch(`${djangoUrl}/api/v1/finance/reconciliation/run/`, {
      method: 'POST',
      headers: authHeaders,
      credentials: 'include',
      body: JSON.stringify(body),
    });

    const data = await resp.json().catch(() => ({}));
    return NextResponse.json(data, { status: resp.status });
  } catch (error) {
    console.error('Reconciliation proxy error:', error);
    return NextResponse.json({ error: 'Reconciliation request failed' }, { status: 500 });
  }
}
