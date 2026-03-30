'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { apiGateway } from '@/services/apiGateway'

export default function PaystackReturnPage() {
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'failed'>('loading')
  const [message, setMessage] = useState('Completing payment...')
  const [hasOpener, setHasOpener] = useState(false)
  const reference = searchParams.get('reference')

  useEffect(() => {
    if (!reference) {
      setStatus('failed')
      setMessage('No payment reference found.')
      return
    }

    if (typeof window === 'undefined') {
      return
    }

    const openerWindow = window.opener
    const openerExists = Boolean(openerWindow)
    setHasOpener(openerExists)

    const verifyPayment = async () => {
      try {
        await apiGateway.post('/subscription/paystack/verify', { reference })
        setStatus('success')
        setMessage('Payment successful. Your subscription has been activated.')

        if (openerWindow) {
          openerWindow.postMessage({ type: 'paystack_success', reference }, window.location.origin)
          setTimeout(() => {
            window.close()
          }, 700)
        }
      } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : 'Payment verification failed'
        setStatus('failed')
        setMessage(errorMessage)
      }
    }

    void verifyPayment()
  }, [reference])

  if (!reference) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <div className="text-center">
          <p className="text-muted-foreground">No payment reference found.</p>
          <Link href="/dashboard/student/subscription" className="text-primary underline mt-2 inline-block">
            Back to subscription
          </Link>
        </div>
      </div>
    )
  }

  if (status === 'success' && !hasOpener) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4 bg-background">
        <div className="text-center">
          <p className="text-foreground font-medium">Payment completed.</p>
          <p className="text-muted-foreground text-sm mt-1">{message}</p>
          <Link
            href="/dashboard/student/subscription"
            className="mt-4 inline-block text-primary underline"
          >
            Back to subscription
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
          <Link
            href="/dashboard/student/subscription"
            className="mt-4 inline-block text-primary underline"
          >
            Back to subscription
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
