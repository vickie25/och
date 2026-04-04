'use client'

import { useAuth } from '@/hooks/useAuth'
import { OchLogoMark } from '@/components/brand/OchLogo'
import { Breadcrumbs } from './Breadcrumbs'
import { Notifications } from './Notifications'
import { SponsorProfileDropdown } from './SponsorProfileDropdown'

export function SponsorHeader() {
  const { user } = useAuth()
  
  return (
    <header className="sticky top-0 z-30 bg-och-midnight/95 backdrop-blur-sm border-b border-och-steel/20">
      <div className="flex items-center justify-between gap-4 px-6 py-4">
        <div className="flex shrink-0 items-center gap-3 min-w-0">
          <OchLogoMark variant="white" className="h-7 max-w-[140px]" priority />
          <span className="hidden sm:inline text-xs font-bold text-och-steel uppercase tracking-wide">Sponsors</span>
        </div>
        {/* Breadcrumbs */}
        <div className="flex-1 min-w-0">
          <Breadcrumbs />
        </div>

        {/* Right side: Sponsor Info, Notifications and Profile */}
        <div className="flex items-center gap-6">
          {/* Sponsor Info */}
          <div className="hidden md:flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-medium text-white">
                {(user as any)?.organization_name || user?.email?.split('@')[1]?.split('.')[0] || 'Corporate Sponsor'}
              </div>
              <div className="text-xs text-och-steel">Seats: 250 | Budget: Ksh 75K</div>
            </div>
          </div>
          
          <Notifications />
          <SponsorProfileDropdown />
        </div>
      </div>
    </header>
  )
}
