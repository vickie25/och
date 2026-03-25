'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import { InstitutionNavigation } from '@/components/navigation/InstitutionNavigation'
import { InstitutionHeader } from '@/components/navigation/InstitutionHeader'

export default function InstitutionLayout({ children }: { children: React.ReactNode }) {
  return (
    <RouteGuard requiredRoles={['institution_admin', 'organization_admin', 'sponsor_admin', 'admin']}>
      <div className="min-h-screen bg-och-midnight flex print:block">
        <div className="print:hidden">
          <InstitutionNavigation />
        </div>
        <div className="flex-1 flex flex-col lg:ml-64 min-w-0 print:ml-0">
          <div className="print:hidden">
            <InstitutionHeader />
          </div>
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </RouteGuard>
  )
}
