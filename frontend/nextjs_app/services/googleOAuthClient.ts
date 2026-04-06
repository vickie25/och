/**
 * Google OAuth 2.0 Client
 * Handles Google SSO for account activation and signup
 *
 * Always uses root-relative `/api/v1/auth/google/*` URLs resolved against `window.location.origin`
 * so we never POST to NEXT_PUBLIC_DJANGO_API_URL (e.g. production) from localhost — that causes
 * CORS preflight failures after Google redirects back to http://localhost:3000.
 */

import { fetcher } from '@/utils/fetcher'

export interface GoogleOAuthInitiateRequest {
  role?: string
  mode?: 'login' | 'register'
}

export interface GoogleOAuthInitiateResponse {
  auth_url: string
  state: string
}

export interface GoogleOAuthCallbackRequest {
  code: string
  state: string
  device_fingerprint?: string
  device_name?: string
}

export interface GoogleOAuthCallbackResponse {
  access_token: string
  refresh_token: string
  user: any
  consent_scopes: string[]
  account_created: boolean
  account_activated: boolean
  onboarding_email_sent?: boolean
}

export const googleOAuthClient = {
  /**
   * Initiate Google OAuth flow
   * GET /api/v1/auth/google/initiate
   * Returns the Google authorization URL to redirect user to
   */
  async initiate(data?: GoogleOAuthInitiateRequest): Promise<GoogleOAuthInitiateResponse> {
    const params: Record<string, string> = {}
    if (data?.role) params.role = data.role
    if (data?.mode) params.mode = data.mode
    return fetcher<GoogleOAuthInitiateResponse>('/api/v1/auth/google/initiate', {
      method: 'GET',
      skipAuth: true,
      params,
    })
  },

  /**
   * Handle Google OAuth callback
   * POST /api/v1/auth/google/callback
   * Exchanges authorization code for tokens and creates/activates account
   */
  async callback(data: GoogleOAuthCallbackRequest): Promise<GoogleOAuthCallbackResponse> {
    return fetcher<GoogleOAuthCallbackResponse>('/api/v1/auth/google/callback', {
      method: 'POST',
      skipAuth: true,
      body: JSON.stringify(data),
    })
  },
}
