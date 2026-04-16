'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { useAuth } from '@/hooks/useAuth'
import { CommunityDashboard } from '@/components/community/CommunityDashboard'
import { Card } from '@/components/ui/Card'

export default function CommunityPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const run = async () => {
      // Wait for auth to settle
      if (authLoading || !isAuthenticated || !user) return

      try {
        // Always enforce university mapping before community access.
        const { djangoClient } = await import('@/services/djangoClient')
        const freshUser = await djangoClient.auth.getCurrentUser()
        const uniId = (freshUser as any)?.university_id
        const uniName = (freshUser as any)?.university_name
        const universitySet = Boolean(uniId) || (typeof uniName === 'string' && uniName.trim().length > 0)

        if (!universitySet) {
          const next = `/dashboard/student/community${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
          router.replace(`/dashboard/student/settings/profile?highlight=university&next=${encodeURIComponent(next)}`)
          return
        }
      } catch {
        // If we can't confirm, don't block community entirely; allow render.
      } finally {
        setChecking(false)
      }
    }
    void run()
  }, [authLoading, isAuthenticated, router, searchParams, user])

  if (checking) {
    return (
      <RouteGuard>
        <div className="min-h-screen bg-och-midnight flex items-center justify-center p-6">
          <Card className="p-8 bg-och-midnight border border-och-steel/20">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
              <p className="text-och-steel text-sm">Preparing community…</p>
            </div>
          </Card>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard>
      <div className="p-6">
        <CommunityDashboard />
      </div>
    </RouteGuard>
  )
}

