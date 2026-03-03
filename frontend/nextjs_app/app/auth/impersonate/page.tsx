'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { setAuthTokens } from '@/utils/auth'

/**
 * Support impersonation: either redeem a one-time code (student tokens) or receive tokens via postMessage.
 * Code flow: ?code=xxx → GET /api/auth/redeem-impersonate?code=xxx → set-tokens → redirect to student dashboard.
 * Shows student identity and 40-min timer after redirect.
 */
function ImpersonateContent() {
  const searchParams = useSearchParams()
  const code = searchParams.get('code')
  const [status, setStatus] = useState<'loading' | 'setting' | 'done' | 'error'>('loading')
  const [message, setMessage] = useState('Loading…')

  useEffect(() => {
    if (typeof window === 'undefined') return

    const applyTokens = async (payload: {
      access_token: string
      refresh_token?: string
      user?: unknown
      impersonation_expires_at?: string | null
    }) => {
      const { access_token, refresh_token = '', user, impersonation_expires_at } = payload
      if (!access_token) {
        setStatus('error')
        setMessage('Missing tokens.')
        return
      }
      if (impersonation_expires_at && typeof impersonation_expires_at === 'string') {
        try {
          sessionStorage.setItem('impersonation_expires_at', impersonation_expires_at)
        } catch {
          // ignore
        }
      }
      setStatus('setting')
      setMessage('Logging in as student…')
      try {
        const res = await fetch('/api/auth/set-tokens', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token, refresh_token, user }),
        })
        if (!res.ok) {
          setStatus('error')
          setMessage('Failed to set session.')
          return
        }
        setAuthTokens(access_token, refresh_token ?? '')
        setStatus('done')
        setMessage('Redirecting to student dashboard…')
        window.location.href = '/dashboard/student'
      } catch {
        setStatus('error')
        setMessage('Request failed.')
      }
    }

    if (code) {
      setMessage('Redeeming session…')
      fetch(`/api/auth/redeem-impersonate?code=${encodeURIComponent(code)}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.error || data.detail) {
            setStatus('error')
            setMessage(data.error || data.detail || 'Invalid or expired code.')
            return
          }
          applyTokens(data)
        })
        .catch(() => {
          setStatus('error')
          setMessage('Failed to redeem code.')
        })
      return
    }

    const origin = window.location.origin
    const sendReady = () => {
      if (window.opener && !window.opener.closed) {
        window.opener.postMessage({ type: 'impersonate_ready' }, origin)
      }
    }
    sendReady()
    const readyInterval = setInterval(sendReady, 400)
    const readyTimeout = setTimeout(() => clearInterval(readyInterval), 8000)

    const handler = (event: MessageEvent) => {
      if (event.origin !== origin || event.data?.type !== 'impersonation_tokens') return
      clearInterval(readyInterval)
      clearTimeout(readyTimeout)
      window.removeEventListener('message', handler)
      applyTokens({
        access_token: event.data.access_token,
        refresh_token: event.data.refresh_token,
        user: event.data.user,
        impersonation_expires_at: event.data.impersonation_expires_at ?? null,
      })
    }
    window.addEventListener('message', handler)
    return () => {
      window.removeEventListener('message', handler)
      clearInterval(readyInterval)
      clearTimeout(readyTimeout)
    }
  }, [code])

  return (
    <div className="min-h-screen bg-och-midnight flex items-center justify-center p-6">
      <div className="text-center text-white">
        {status === 'loading' && <p>{message}</p>}
        {status === 'setting' && <p>{message}</p>}
        {status === 'done' && <p>{message}</p>}
        {status === 'error' && <p className="text-och-orange">{message}</p>}
      </div>
    </div>
  )
}

export default function AuthImpersonatePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-6">
        <p className="text-white">Loading…</p>
      </div>
    }>
      <ImpersonateContent />
    </Suspense>
  )
}
