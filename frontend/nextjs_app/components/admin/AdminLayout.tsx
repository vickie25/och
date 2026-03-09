'use client'

import { ReactNode } from 'react'
import { AdminNavigation } from '@/components/navigation/AdminNavigation'
import { MFARequiredGuard } from '@/components/auth/MFARequiredGuard'

interface AdminLayoutProps {
  children: ReactNode
}

export function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <MFARequiredGuard>
      <div className="h-screen bg-och-midnight flex overflow-hidden">
        {/* Persistent sidebar with its own scrolling; AdminNavigation includes its own desktop spacer */}
        <AdminNavigation />

        {/* Main content area beside sidebar spacer, no extra gap */}
        <div className="flex-1 flex flex-col">
          <main className="flex-1 overflow-y-auto">
            <div className="w-full p-4 lg:p-6">
              {children}
            </div>
          </main>
        </div>
      </div>
    </MFARequiredGuard>
  )
}

