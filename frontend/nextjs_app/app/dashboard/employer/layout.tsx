'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import { EmployerNavigation } from '@/components/navigation/EmployerNavigation'
import { EmployerHeader } from '@/components/navigation/EmployerHeader'

export default function EmployerLayout({ children }: { children: React.ReactNode }) {
  return (
    <RouteGuard>
      <div className="min-h-screen bg-och-midnight flex print:block">
        <div className="print:hidden">
          <EmployerNavigation />
        </div>
        <div className="flex-1 flex flex-col lg:ml-64 min-w-0 print:ml-0">
          <div className="print:hidden">
            <EmployerHeader />
          </div>
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </RouteGuard>
  )
}
