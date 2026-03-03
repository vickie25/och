'use client'

import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'next/navigation'

const API_BASE = process.env.NEXT_PUBLIC_DJANGO_API_URL;

export default function PayInvoiceReturnPage() {
  const params = useParams()
  const searchParams = useSearchParams()
  const id = params?.id as string
  const reference = searchParams?.get('reference')
  const [status, setStatus] = useState<'loading' | 'success' | 'failed'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!id || !reference) {
      setStatus('failed')
      setMessage('Missing invoice or payment reference')
      return
    }
    fetch(`${API_BASE}/api/v1/billing/org-enrollment-invoices/${id}/verify-payment/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'omit',
      body: JSON.stringify({ reference }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'paid') {
          setStatus('success')
          setMessage('Payment verified. Thank you.')
        } else {
          setStatus('failed')
          setMessage(data.error || 'Payment verification failed')
        }
      })
      .catch(() => {
        setStatus('failed')
        setMessage('Could not verify payment')
      })
  }, [id, reference])

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full rounded-lg border border-slate-700 bg-slate-900/50 p-6 text-center">
        {status === 'loading' && <p className="text-slate-400">Verifying payment…</p>}
        {status === 'success' && (
          <>
            <h1 className="text-xl font-semibold text-green-400 mb-2">Payment successful</h1>
            <p className="text-slate-300">{message}</p>
          </>
        )}
        {status === 'failed' && (
          <>
            <h1 className="text-xl font-semibold text-red-400 mb-2">Payment verification failed</h1>
            <p className="text-slate-300">{message}</p>
          </>
        )}
      </div>
    </div>
  )
}
