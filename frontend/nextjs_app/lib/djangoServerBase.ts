/**
 * Base URL for server-side Next.js routes to reach Django (Docker internal, then fallbacks).
 *
 * Production / Docker:
 * - Browser: use `NEXT_PUBLIC_*` https URL for links and any intentional cross-origin calls.
 * - Next.js Route Handlers (BFF): set `DJANGO_INTERNAL_URL` or `DJANGO_API_URL` (e.g. `http://django:8000`)
 *   so server-side `fetch` does not depend on public HTTPS or hairpin NAT.
 * - Local dev: `http://localhost:8000` or host.docker.internal as appropriate.
 */

import { existsSync } from 'fs';
import type { NextResponse } from 'next/server';

/** True inside typical Linux containers (Docker / similar). */
function isRunningInDocker(): boolean {
  if (process.env.NEXT_RUNTIME_DOCKER === '1') return true;
  try {
    return existsSync('/.dockerenv');
  } catch {
    return false;
  }
}

/**
 * Normalize to scheme + host + port only (no /api path) so `new URL('/api/v1/...', base)` is correct.
 */
function djangoOriginFromRaw(raw: string): string {
  const trimmed = raw.replace(/\/$/, '');
  try {
    const u = new URL(trimmed.includes('://') ? trimmed : `http://${trimmed}`);
    return u.origin;
  } catch {
    return trimmed;
  }
}

export function djangoBaseForServerFetch(): string {
  const internal =
    process.env.DJANGO_INTERNAL_URL?.trim() || process.env.DJANGO_API_URL?.trim();
  if (internal) {
    // If Next is running on the host (not in Docker) but env points at the Docker service DNS,
    // fall back to the host-mapped port instead.
    if (!isRunningInDocker()) {
      try {
        const u = new URL(internal.includes('://') ? internal : `http://${internal}`);
        const host = (u.hostname || '').toLowerCase();
        if (host === 'django') {
          return 'http://localhost:8000';
        }
      } catch {
        // ignore
      }
    }
    return djangoOriginFromRaw(internal);
  }

  // Inside Docker, never fall back to NEXT_PUBLIC HTTPS (hairpin / routing often breaks fetch).
  if (isRunningInDocker()) {
    return 'http://django:8000';
  }

  const pub = process.env.NEXT_PUBLIC_DJANGO_API_URL?.trim();
  if (pub) {
    const stripped = pub
      .replace(/\/$/, '')
      .replace(/\/api\/v1\/?$/i, '')
      .replace(/\/api\/?$/i, '');
    return djangoOriginFromRaw(stripped);
  }

  return 'http://localhost:8000';
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
