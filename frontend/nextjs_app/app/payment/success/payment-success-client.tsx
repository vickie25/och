'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { apiGateway } from '@/services/apiGateway'

type Status = 'loading' | 'success' | 'failed'

export default function PaymentSuccessClient() {
  const searchParams = useSearchParams()
  const reference = searchParams.get('reference') || ''
  const [status, setStatus] = useState<Status>('loading')
  const [message, setMessage] = useState('Completing payment…')
  const [hasOpener, setHasOpener] = useState(false)

  const origin = useMemo(() => (typeof window !== 'undefined' ? window.location.origin : ''), [])

  useEffect(() => {
    if (!reference) {
      setStatus('failed')
      setMessage('No payment reference found.')
      return
    }
    if (typeof window === 'undefined') return

    const openerWindow = window.opener
    setHasOpener(Boolean(openerWindow))

    const notifyOpener = () => {
      if (openerWindow) {
        openerWindow.postMessage({ type: 'paystack_success', reference }, origin)
        setTimeout(() => window.close(), 700)
      }
    }

    const run = async () => {
      try {
        // 1) Try subscription verification (Paystack → activates plan).
        try {
          await apiGateway.post('/subscription/paystack/verify', { reference })
          setStatus('success')
          setMessage('Payment successful. Your subscription has been activated.')
          notifyOpener()
          return
        } catch {
          // Continue to next verifier
        }

        // 2) Try cohort payment verification (Paystack → activates enrollment).
        await apiGateway.get(`/cohorts/payment/verify/?reference=${encodeURIComponent(reference)}`)
        setStatus('success')
        setMessage('Payment successful. Your cohort enrollment has been activated.')
        notifyOpener()
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Payment verification failed'
        setStatus('failed')
        setMessage(msg)
      }
    }

    void run()
  }, [reference, origin])

  if (status === 'success' && !hasOpener) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <div className="text-center">
          <p className="text-foreground font-medium">Payment completed.</p>
          <p className="text-muted-foreground text-sm mt-1">{message}</p>
          <Link href="/dashboard/student/subscription" className="mt-4 inline-block text-primary underline">
            Back to dashboard
          </Link>
        </div>
      </div>
    )
  }

  if (status === 'failed') {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <div className="text-center">
          <p className="text-red-400 font-medium">Payment verification failed.</p>
          <p className="text-muted-foreground text-sm mt-1">{message}</p>
          <Link href="/dashboard/student/subscription" className="mt-4 inline-block text-primary underline">
            Back to dashboard
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="text-center">
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}

