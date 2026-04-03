/**
 * Legacy route: Mentor Payouts
 * Redirects to Mentor Credit Wallets.
 */

'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { RouteGuard } from '@/components/auth/RouteGuard'

export default function MentorPayoutsPage() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/finance/mentor-credit-wallets')
  }, [router])

  return (
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
          <p className="text-och-steel text-sm">Redirecting…</p>
        </div>
      </div>
    </RouteGuard>
  )
}

