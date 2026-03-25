'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Breadcrumbs } from './Breadcrumbs'
import { Notifications } from './Notifications'
import { EmployerProfileDropdown } from './EmployerProfileDropdown'
import { apiGateway } from '@/services/apiGateway'

type ContractRow = {
  id: string
  type: string
  seat_cap: number
  seats_used?: number
  organization_name?: string
}

export function EmployerHeader() {
  const { user } = useAuth()
  const [summary, setSummary] = useState<{ label: string; sub: string } | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await apiGateway.get<unknown>('/finance/contracts/')
        const list: ContractRow[] = Array.isArray(data)
          ? (data as ContractRow[])
          : (data as { results?: ContractRow[] })?.results ?? []
        const employer = list.filter((c) => c.type === 'employer')
        if (cancelled || employer.length === 0) {
          if (!cancelled) {
            setSummary({
              label: (user as { organization_name?: string })?.organization_name || user?.email?.split('@')[0] || 'Employer',
              sub: 'Seat allocation: set when contract is created',
            })
          }
          return
        }
        const cap = employer.reduce((s, c) => s + (c.seat_cap ?? 0), 0)
        const used = employer.reduce((s, c) => s + (c.seats_used ?? 0), 0)
        const orgName = employer[0]?.organization_name || 'Your organization'
        if (!cancelled) {
          setSummary({
            label: orgName,
            sub: `Seats: ${used} / ${cap} allocated (${employer.length} contract${employer.length !== 1 ? 's' : ''})`,
          })
        }
      } catch {
        if (!cancelled) {
          setSummary({
            label: (user as { organization_name?: string })?.organization_name || 'Employer',
            sub: 'Contracts load when available',
          })
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [user])

  return (
    <header className="sticky top-0 z-30 bg-och-midnight/95 backdrop-blur-sm border-b border-och-steel/20">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex-1 min-w-0">
          <Breadcrumbs />
        </div>

        <div className="flex items-center gap-6 shrink-0">
          <div className="hidden md:flex items-center gap-4 text-right">
            <div>
              <div className="text-sm font-medium text-white">
                {summary?.label ?? 'Employer'}
              </div>
              <div className="text-xs text-och-steel max-w-[280px] truncate">{summary?.sub ?? '…'}</div>
            </div>
          </div>

          <Notifications />
          <EmployerProfileDropdown />
        </div>
      </div>
    </header>
  )
}
