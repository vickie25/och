'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Breadcrumbs } from './Breadcrumbs'
import { Notifications } from './Notifications'
import { InstitutionProfileDropdown } from './InstitutionProfileDropdown'
import { institutionalService, type InstitutionalContractListItem } from '@/services/institutionalService'

export function InstitutionHeader() {
  const { user } = useAuth()
  const [summary, setSummary] = useState<{ label: string; sub: string } | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await institutionalService.listContracts()
        const inst: InstitutionalContractListItem[] = Array.isArray((data as any)?.contracts) ? (data as any).contracts : []
        if (cancelled || inst.length === 0) {
          if (!cancelled) {
            setSummary({
              label:
                (user as { organization_name?: string })?.organization_name ||
                user?.email?.split('@')[0] ||
                'Institution',
              sub: 'Contract licensing: set tier and seats when your agreement is ready',
            })
          }
          return
        }
        const cap = inst.reduce((s, c) => s + (c.student_seat_count ?? 0), 0)
        const used = inst.reduce((s, c) => s + (c.active_students ?? 0), 0)
        const orgName = inst[0]?.organization?.name || 'Your organization'
        const rate = inst[0]?.per_student_rate
        const rateNote = typeof rate === 'number' ? `$${rate}/student/mo` : 'rate not set'
        if (!cancelled) {
          setSummary({
            label: orgName,
            sub: `Seats: ${used} / ${cap} · ${rateNote} · ${inst.length} contract${inst.length !== 1 ? 's' : ''}`,
          })
        }
      } catch {
        if (!cancelled) {
          setSummary({
            label: (user as { organization_name?: string })?.organization_name || 'Institution',
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
              <div className="text-sm font-medium text-white">{summary?.label ?? 'Institution'}</div>
              <div className="text-xs text-och-steel max-w-[280px] truncate">{summary?.sub ?? '…'}</div>
            </div>
          </div>

          <Notifications />
          <InstitutionProfileDropdown />
        </div>
      </div>
    </header>
  )
}
