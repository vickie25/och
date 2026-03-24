'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import { useSearchParams } from 'next/navigation'
import InstitutionalBillingDashboard from '@/app/dashboard/director/institutional-billing/page'

export default function InstitutionDashboardPage() {
  const searchParams = useSearchParams()
  const created = searchParams.get('created') === '1'

  return (
    <RouteGuard requiredRoles={['institution_admin', 'organization_admin', 'sponsor_admin', 'admin']}>
      <div className="space-y-4">
        {created && (
          <div className="mx-auto w-full max-w-7xl rounded-md border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
            Account created successfully. Welcome to your institution dashboard.
          </div>
        )}
        <InstitutionalBillingDashboard />
      </div>
    </RouteGuard>
  )
}
