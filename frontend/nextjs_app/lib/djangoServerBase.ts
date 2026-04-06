/**
 * Base URL for server-side Next.js routes to reach Django (Docker internal, then fallbacks).
 */

import type { NextResponse } from 'next/server';

export function djangoBaseForServerFetch(): string {
  const raw =
    process.env.DJANGO_INTERNAL_URL ||
    process.env.DJANGO_API_URL ||
    process.env.NEXT_PUBLIC_DJANGO_API_URL ||
    'http://localhost:8000';
  const trimmed = raw.replace(/\/$/, '');
  try {
    const u = new URL(trimmed.includes('://') ? trimmed : `http://${trimmed}`);
    return u.toString().replace(/\/$/, '');
  } catch {
    return trimmed;
  }
}

/** Collect Set-Cookie headers from a fetch Response (Node / undici). */
export function collectSetCookieHeaders(res: Response): string[] {
  const h = res.headers;
  if (typeof h.getSetCookie === 'function') {
    return h.getSetCookie();
  }
  const single = h.get('set-cookie');
  return single ? [single] : [];
}

export function forwardSetCookies(from: Response, to: NextResponse): void {
  for (const c of collectSetCookieHeaders(from)) {
    if (c) to.headers.append('Set-Cookie', c);
  }
}
