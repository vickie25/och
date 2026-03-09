'use client'

import { ReactNode } from 'react'
import { DirectorNavigation } from '@/components/navigation/DirectorNavigation'
import { DirectorHeader } from './DirectorHeader'
import { MFARequiredGuard } from '@/components/auth/MFARequiredGuard'

interface DirectorLayoutProps {
  children: ReactNode
}

export function DirectorLayout({ children }: DirectorLayoutProps) {
  return (
    <MFARequiredGuard>
      <div className="h-screen bg-och-midnight flex overflow-hidden">
        {/* Persistent sidebar with its own scrolling (DirectorNavigation already includes its own desktop spacer) */}
        <DirectorNavigation />

        {/* Main content area sits directly beside the sidebar spacer with no extra gap */}
        <div className="flex-1 flex flex-col">
          <main className="flex-1 overflow-y-auto">
            <DirectorHeader />
            <div className="w-full p-4 lg:p-6">
              {children}
            </div>
          </main>
        </div>
      </div>
    </MFARequiredGuard>
  )
}

