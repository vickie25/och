/**
 * Google OAuth Callback Page
 * Handles the redirect from Google after user authenticates
 */
'use client'

export const dynamic = 'force-dynamic'

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { googleOAuthClient } from '@/services/googleOAuthClient'
import { apiGateway } from '@/services/apiGateway'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { getRedirectRoute } from '@/utils/redirect'
import type { User } from '@/services/types/user'

function normalizeRoleName(roleName: string): string {
  const normalized = (roleName || '').toLowerCase().trim()
  if (
    normalized === 'program_director' ||
    normalized === 'program director' ||
    normalized === 'programdirector' ||
    normalized === 'director'
  )
    return 'program_director'
  if (normalized === 'mentee') return 'mentee'
  if (normalized === 'student') return 'student'
  if (normalized === 'mentor') return 'mentor'
  if (normalized === 'admin') return 'admin'
  if (
    normalized === 'sponsor_admin' ||
    normalized === 'sponsor' ||
    normalized === 'sponsor/employer admin' ||
    normalized === 'sponsoremployer admin'
  )
    return 'sponsor_admin'
  if (
    normalized === 'institution_admin' ||
    normalized === 'institution admin' ||
    normalized === 'institutional_admin' ||
    normalized === 'institutional admin'
  )
    return 'institution_admin'
  if (normalized === 'organization_admin' || normalized === 'organization admin')
    return 'organization_admin'
  if (normalized === 'analyst') return 'analyst'
  if (normalized === 'employer') return 'employer'
  if (normalized === 'finance' || normalized === 'finance_admin') return 'finance'
  if (normalized === 'support') return 'support'
  return normalized
}

function extractNormalizedRoles(user: any): string[] {
  const rolesRaw = user?.roles || []
  if (!Array.isArray(rolesRaw)) return []
  const roles = rolesRaw
    .map((ur: any) => {
      let roleValue: string
      if (typeof ur === 'string') roleValue = ur
      else if (ur && typeof ur === 'object') {
        const r = ur.role
        roleValue =
          typeof r === 'string'
            ? r
            : r?.name != null
              ? String(r.name)
              : ur?.name != null
                ? String(ur.name)
                : ''
      } else roleValue = String(ur ?? '')
      return normalizeRoleName(roleValue)
    })
    .filter(Boolean)
  return Array.from(new Set(roles))
}

function getPrimaryRole(roles: string[]): string | null {
  if (roles.includes('admin')) return 'admin'
  const priority = [
    'program_director',
    'finance',
    'support',
    'mentor',
    'analyst',
    'institution_admin',
    'organization_admin',
    'sponsor_admin',
    'employer',
    'mentee',
    'student',
  ]
  for (const r of priority) if (roles.includes(r)) return r
  return roles[0] || null
}

function GoogleOAuthCallbackPageInner() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [message, setMessage] = useState('Processing Google authentication...')
  const [error, setError] = useState<string | null>(null)
  const [showRedirectMessage, setShowRedirectMessage] = useState(true)
  const [resendEmail, setResendEmail] = useState<string | null>(null)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendSuccess, setResendSuccess] = useState<string | null>(null)
  const [resendError, setResendError] = useState<string | null>(null)
  const [resendCooldownSeconds, setResendCooldownSeconds] = useState(0)

  useEffect(() => {
    let redirectTimer: NodeJS.Timeout | null = null

    const handleCallback = async () => {
      try {
        // Fresh OAuth round-trip always includes ?code=… — never skip the token exchange
        // just because sessionStorage still has oauth_callback_handled from an older visit
        // (that would redirect to /dashboard with no tokens → 401 → /login).
        const oauthCode = searchParams.get('code')

        // If we're in a real callback (code present), proactively clear stale tokens so an
        // expired access_token doesn't cause an immediate /auth/me 401 → redirect loop
        // before we finish exchanging the code and setting fresh cookies.
        if (oauthCode && typeof window !== 'undefined') {
          try {
            localStorage.removeItem('access_token')
            localStorage.removeItem('auth_token')
            localStorage.removeItem('refresh_token')
          } catch {
            // ignore
          }
        }
        const fromSuccess = searchParams.get('success') === '1'
        const alreadyHandled = typeof window !== 'undefined' && sessionStorage.getItem('oauth_callback_handled') === '1'
        // Replay / success-page UX only when Google did not just return an authorization code
        if (!oauthCode && (fromSuccess || alreadyHandled)) {
          setStatus('success')
          const studentEmailFlow =
            typeof window !== 'undefined' &&
            sessionStorage.getItem('oauth_student_email_flow') === '1'
          if (studentEmailFlow) {
            setMessage(
              'Your account has been created. Please check your email for a self-onboarding link to set your password, secure your account with MFA, and complete profiling.'
            )
            setShowRedirectMessage(false)
            // So Back is intercepted and sends user to /register (see popstate effect below)
            if (typeof window !== 'undefined' && !window.history.state?.oauthSuccessBackGuard) {
              window.history.replaceState({ oauthSuccessBackGuard: true }, '', window.location.pathname + '?' + (new URLSearchParams(window.location.search)).toString())
              window.history.pushState({ oauthSuccessBackGuard: true }, '', window.location.href)
            }
          } else {
            setMessage("You're signed in. Redirecting…")
            setShowRedirectMessage(true)
            redirectTimer = setTimeout(() => {
              window.location.replace('/dashboard')
            }, 600)
          }
          return
        }

        // Get authorization code and state from URL
        const code = searchParams.get('code')
        const state = searchParams.get('state')
        const errorParam = searchParams.get('error')

        console.log('[OAuth Callback] URL parameters:', { code: code?.substring(0, 20) + '...', state, error: errorParam })
        console.log('[OAuth Callback] Full URL:', window.location.href)

        // Handle OAuth errors from Google
        if (errorParam) {
          setStatus('error')
          setError(`Google authentication failed: ${errorParam}`)
          return
        }

        if (!code || !state) {
          setStatus('error')
          setError('Missing authorization code or state parameter')
          return
        }

        // Get device fingerprint
        const deviceFingerprint = typeof window !== 'undefined' 
          ? `web-${Date.now()}-${navigator.userAgent.slice(0, 50)}`
          : 'unknown'
        
        const deviceName = typeof window !== 'undefined'
          ? navigator.userAgent.includes('Mobile') ? 'Mobile Device' : 'Web Browser'
          : 'Unknown Device'

        // Exchange code for tokens and create/activate account
        console.log('[OAuth Callback] Sending callback request:', {
          code: code.substring(0, 20) + '...',
          state,
          device_fingerprint: deviceFingerprint,
          device_name: deviceName
        })

        const response = await googleOAuthClient.callback({
          code,
          state,
          device_fingerprint: deviceFingerprint,
          device_name: deviceName,
        })

        console.log('[OAuth Callback] Backend response:', response)
        const accountCreated = !!response.account_created
        const onboardingEmailSent = !!response.onboarding_email_sent

        setStatus('success')
        setMessage(
          accountCreated
            ? 'Account created successfully!'
            : 'Login successful!'
        )

        // Determine redirect path based on role and profiling status
        const userRoles = response.user?.roles || []
        const user = response.user || {}
        console.log('[OAuth Callback] User data:', { roles: userRoles, profiling_complete: user.profiling_complete })

        const normalizedRoles = extractNormalizedRoles(user)
        const primaryRole = getPrimaryRole(normalizedRoles)
        
        const hasPrivilegedDashboardRole = userRoles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase()
          return [
            'sponsor',
            'sponsor_admin',
            'institution_admin',
            'organization_admin',
            'employer',
            'mentor',
            'program_director',
            'director',
            'admin',
            'analyst',
            'finance',
            'finance_admin',
            'support',
          ].includes(roleName)
        })

        const isStudent = !hasPrivilegedDashboardRole && userRoles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase()
          console.log('[OAuth Callback] Checking role:', roleName)
          return roleName === 'student' || roleName === 'mentee'
        })

        let redirectPath = getRedirectRoute(user as User)
        
        // CRITICAL: Double safety for mentor/finance/support roles
        // This mirrors the logic in LoginForm-full.tsx for total consistency
        const roles = userRoles.map((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim()
          return roleName
        })

        if (roles.includes('mentor')) {
          redirectPath = '/dashboard/mentor'
        } else if (roles.includes('finance') || roles.includes('finance_admin')) {
          redirectPath = '/dashboard/finance'
        } else if (roles.includes('support')) {
          redirectPath = '/support/dashboard'
        }

        if (isStudent) {
          // For newly created student accounts via Google SSO, we now send a
          // self-onboarding email (password → MFA → profiling). Do NOT drop
          // them directly into onboarding here; instead, instruct them to
          // check their email.
          const profilingComplete = user.profiling_complete ?? false
          console.log('[OAuth Callback] Student profiling_complete:', profilingComplete)

          // Brand-new student via Google: we send a self-onboarding email (password → MFA → profiling).
          // Do not use onboardingEmailSent alone — the backend may resend on later logins; that should
          // not block the user with an "account created" screen.
          if (accountCreated) {
            const email = user.email || response.user?.email || ''
            setResendEmail(email || null)
            setResendCooldownSeconds(60)
            setMessage(
              'Your account has been created. Please check your email for a self-onboarding link to set your password, secure your account with MFA, and complete profiling.'
            )
            setShowRedirectMessage(false)
            // Mark as handled and replace URL so Back doesn't reload this page with code
            if (typeof window !== 'undefined') {
              sessionStorage.setItem('oauth_student_email_flow', '1')
              sessionStorage.setItem('oauth_callback_handled', '1')
              const url = new URL(window.location.href)
              url.searchParams.delete('code')
              url.searchParams.delete('state')
              url.searchParams.set('success', '1')
              const successUrl = url.pathname + '?' + url.searchParams.toString()
              window.history.replaceState(null, '', successUrl)
              // Push an extra history entry so Back stays on this page and we can intercept with popstate,
              // then send user to /register instead of Google or dashboard
              window.history.pushState({ oauthSuccessBackGuard: true }, '', successUrl)
            }
            return
          }

          // Existing students logging in with Google keep the previous behavior.
          if (!profilingComplete) {
            redirectPath = '/onboarding/ai-profiler'
          } else {
            redirectPath = '/dashboard/student'
          }
        }

        // For all flows that reach this point (i.e. not in the student + onboarding-email branch),
        // persist tokens locally and via the ssologin route so the app can use them.
        if (response.access_token) {
          localStorage.setItem('access_token', response.access_token)
          localStorage.setItem('auth_token', response.access_token)
          if (typeof document !== 'undefined') {
            document.cookie = `access_token=${response.access_token}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`
            if (primaryRole) document.cookie = `och_primary_role=${primaryRole}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`
            // Instead of getDashboardForRole, just use redirectPath because it's already calculated above!
            document.cookie = `och_dashboard=${redirectPath}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax`
          }
          if (response.refresh_token) {
            localStorage.setItem('refresh_token', response.refresh_token)
          }
          try {
            await fetch('/api/auth/ssologin', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                access_token: response.access_token,
                refresh_token: response.refresh_token,
                user: response.user,
              }),
            })
          } catch (e) {
            console.error('[OAuth] Failed to set cookies via ssologin route', e)
          }
        }
        
        console.log('[OAuth Callback] Will redirect to:', redirectPath)

        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('oauth_student_email_flow')
        }

        // Redirect with a short delay; use replace so callback is not left in history
        // (avoids back-button going callback → Google → … instead of to app)
        redirectTimer = setTimeout(() => {
          console.log('[OAuth Callback] Executing redirect to:', redirectPath)
          window.location.replace(redirectPath)
        }, 1000)

      } catch (err: any) {
        console.error('Google OAuth callback error:', err)
        setStatus('error')
        setError(
          err?.data?.detail || 
          err?.response?.data?.detail ||
          err?.message || 
          'Failed to complete Google authentication'
        )
      }
    }

    handleCallback()
    
    // Cleanup timer on unmount
    return () => {
      if (redirectTimer) {
        clearTimeout(redirectTimer)
      }
    }
  }, [searchParams, router])

  const handleResendOnboardingEmail = async () => {
    if (!resendEmail) return
    if (resendCooldownSeconds > 0) return
    setResendLoading(true)
    setResendSuccess(null)
    setResendError(null)
    try {
      await apiGateway.post('/admin/students/send-onboarding-email/', {
        email: resendEmail,
      })
      setResendSuccess('Onboarding email has been resent. Please check your inbox (and spam folder).')
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.data?.detail ||
        err?.data?.error ||
        'Failed to resend onboarding email. Please try again or contact support.'
      setResendError(detail)
    } finally {
      setResendLoading(false)
    }
  }

  // Countdown timer for resend cooldown
  useEffect(() => {
    if (resendCooldownSeconds <= 0) return
    const timer = setInterval(() => {
      setResendCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [resendCooldownSeconds])

  // When showing "account created" success, intercept Back so user goes to /register instead of Google or dashboard
  useEffect(() => {
    if (status !== 'success' || showRedirectMessage) return

    const handlePopState = () => {
      window.removeEventListener('popstate', handlePopState)
      sessionStorage.removeItem('oauth_callback_handled')
      window.location.replace('/register')
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [status, showRedirectMessage])

  return (
    <div className="min-h-screen bg-gradient-to-br from-och-midnight via-och-space to-och-crimson flex items-center justify-center px-4">
      <Card className="p-8 max-w-md w-full">
        <div className="text-center space-y-4">
          {status === 'processing' && (
            <>
              <Loader2 className="w-12 h-12 text-och-orange animate-spin mx-auto" />
              <h2 className="text-xl font-bold text-white">Processing...</h2>
              <p className="text-gray-300">{message}</p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle2 className="w-12 h-12 text-och-mint mx-auto" />
              <h2 className="text-xl font-bold text-white">Success!</h2>
              <p className="text-gray-300">{message}</p>
              {!showRedirectMessage && resendEmail && (
                <div className="mt-4 space-y-2">
                  {resendSuccess && (
                    <p className="text-xs text-emerald-300">{resendSuccess}</p>
                  )}
                  {resendError && (
                    <p className="text-xs text-red-300">{resendError}</p>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={resendLoading || resendCooldownSeconds > 0}
                    onClick={handleResendOnboardingEmail}
                  >
                    {resendLoading
                      ? 'Resending...'
                      : resendCooldownSeconds > 0
                        ? `You can resend in ${resendCooldownSeconds}s`
                        : "Didn't receive the email? Resend now"}
                  </Button>
                </div>
              )}
              {showRedirectMessage && (
                <p className="text-sm text-gray-400">Redirecting to your dashboard...</p>
              )}
              {!showRedirectMessage && (
                <div className="flex flex-col sm:flex-row gap-3 justify-center mt-4">
                  <Button
                    onClick={() => {
                      if (typeof window !== 'undefined') sessionStorage.removeItem('oauth_callback_handled')
                      router.push('/register')
                    }}
                    variant="outline"
                    className="w-full sm:w-auto"
                  >
                    Back to registration
                  </Button>
                  <Button
                    onClick={() => {
                      if (typeof window !== 'undefined') sessionStorage.removeItem('oauth_callback_handled')
                      router.push('/')
                    }}
                    className="w-full sm:w-auto"
                  >
                    Go to home
                  </Button>
                </div>
              )}
            </>
          )}

          {status === 'error' && (
            <>
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
              <h2 className="text-xl font-bold text-white">Authentication Failed</h2>
              <p className="text-gray-300">{error}</p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center mt-4">
                <Button
                  onClick={() => router.push('/register')}
                  className="w-full sm:w-auto"
                >
                  Go to Registration
                </Button>
                <Button
                  onClick={() => router.push('/login')}
                  variant="outline"
                  className="w-full sm:w-auto"
                >
                  Return to Login
                </Button>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  )
}

export default function GoogleOAuthCallbackPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-white">Loading...</div>}>
      <GoogleOAuthCallbackPageInner />
    </Suspense>
  )
}
