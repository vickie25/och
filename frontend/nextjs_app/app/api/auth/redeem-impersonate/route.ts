/**
 * Redeem one-time impersonation code for student tokens.
 * GET /api/auth/redeem-impersonate?code=xxx
 * Proxies to Django; returns { access_token, refresh_token, user, impersonation_expires_at }.
 */
import { NextRequest, NextResponse } from 'next/server';

const DJANGO_API_URL = process.env.NEXT_PUBLIC_DJANGO_API_URL;

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get('code');
  if (!code) {
    return NextResponse.json({ error: 'Missing code' }, { status: 400 });
  }
  try {
    const url = `${DJANGO_API_URL}/api/v1/support/impersonate/redeem/?code=${encodeURIComponent(code)}`;
    const res = await fetch(url, { method: 'GET', headers: { Accept: 'application/json' } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(data || { error: 'Invalid or expired code' }, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (e) {
    return NextResponse.json({ error: 'Failed to redeem code' }, { status: 500 });
  }
}
