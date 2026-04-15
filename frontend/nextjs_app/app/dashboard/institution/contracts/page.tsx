'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { BILLING_CYCLE_LABEL, type BillingCycleKey } from '@/lib/institutionContractCatalog'
import { FileText, ChevronRight } from 'lucide-react'
import { institutionalService, type InstitutionalContractListItem } from '@/services/institutionalService'

const STATUS_LABEL: Record<string, string> = {
  draft: 'Draft',
  active: 'Active',
  pending_renewal: 'Pending renewal',
  expired: 'Expired',
  terminated: 'Terminated',
}

function formatMoneyUsd(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export default function InstitutionContractsOverviewPage() {
  const [contracts, setContracts] = useState<InstitutionalContractListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await institutionalService.listContracts()
      setContracts(Array.isArray(data?.contracts) ? data.contracts : [])
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load')
      setContracts([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold text-och-gold">Contracts</h1>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/dashboard/institution/contracts/commercial-terms"
              className="inline-flex items-center gap-2 rounded-lg border border-och-steel/35 px-3 py-2 text-xs font-medium text-och-mint hover:bg-och-defender/20"
            >
              <FileText className="h-4 w-4" />
              Commercial terms (print/PDF)
            </Link>
            <Link
              href="/dashboard/institution/students"
              className="inline-flex items-center gap-1 rounded-lg border border-och-steel/35 px-3 py-2 text-xs text-och-steel hover:text-white"
            >
              Students <ChevronRight className="h-3 w-3" />
            </Link>
            <Link
              href="/dashboard/institution/contracts/invoices"
              className="inline-flex items-center gap-1 rounded-lg border border-och-steel/35 px-3 py-2 text-xs text-och-steel hover:text-white"
            >
              Invoices <ChevronRight className="h-3 w-3" />
            </Link>
            <Link
              href="/dashboard/institution/contracts/payments"
              className="inline-flex items-center gap-1 rounded-lg border border-och-steel/35 px-3 py-2 text-xs text-och-steel hover:text-white"
            >
              Payments <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-100">{error}</div>
        )}

        <Card className="border border-och-steel/20 overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-och-steel/25 bg-och-steel/5 text-left text-xs uppercase tracking-wide text-och-steel">
                <tr>
                  <th className="py-3 px-4 text-left">Organization</th>
                  <th className="py-3 px-4 text-left">Term</th>
                  <th className="py-3 px-4 text-left">Status</th>
                  <th className="py-3 px-4 text-left">Tier / billing</th>
                  <th className="py-3 px-4 text-right">Value</th>
                  <th className="py-3 px-4 text-right">Seats</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-och-steel/15">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-och-steel">
                      Loading…
                    </td>
                  </tr>
                ) : contracts.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-och-steel">
                      No institution contracts yet.
                    </td>
                  </tr>
                ) : (
                  contracts.map((c) => (
                    <tr key={c.id} className="hover:bg-och-steel/10">
                      <td className="py-3 px-4 text-white font-medium">{c.organization?.name}</td>
                      <td className="py-3 px-4 text-och-steel whitespace-nowrap">
                        {c.start_date} → {c.end_date}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={c.status === 'active' ? 'mint' : 'gold'}>
                          {STATUS_LABEL[c.status] ?? c.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-och-steel text-xs max-w-[200px]">
                        {typeof c.per_student_rate === 'number' ? `${formatMoneyUsd(c.per_student_rate)}/student/mo` : '—'}
                        {c.billing_cycle ? (
                          <span className="block text-och-steel/80">
                            {BILLING_CYCLE_LABEL[c.billing_cycle]}
                          </span>
                        ) : null}
                      </td>
                      <td className="py-3 px-4 text-right text-white tabular-nums">{formatMoneyUsd(c.annual_amount)}</td>
                      <td className="py-3 px-4 text-right text-och-steel tabular-nums">
                        {c.active_students ?? 0}/{c.student_seat_count ?? 0}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/dashboard/institution/contracts/${c.id}/complete`}
                          className={`inline-flex text-xs font-semibold ${
                            c.status === 'draft' ? 'text-och-gold hover:underline' : 'text-och-mint hover:underline'
                          }`}
                        >
                          {c.status === 'draft' ? 'Review & activate' : 'View / edit'}
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  )
}
