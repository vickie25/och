import { Suspense } from 'react'
import PaymentSuccessClient from './payment-success-client'

export default function PaymentSuccessPage() {
  // `useSearchParams()` must be inside a Suspense boundary in Next 16+.
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
          <div className="text-center">
            <p className="text-muted-foreground">Completing payment…</p>
          </div>
        </div>
      }
    >
      <PaymentSuccessClient />
    </Suspense>
  )
}

