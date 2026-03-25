'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import {
  INSTITUTION_TIER_LABEL,
  BILLING_CYCLE_LABEL,
  type InstitutionTierKey,
  type BillingCycleKey,
} from '@/lib/institutionContractCatalog'
import { FileText, ChevronRight } from 'lucide-react'

type ContractRow = {
  id: string
  organization_name: string
  type: string
  start_date: string
  end_date: string
  status: string
  total_value: string | number
  payment_terms: string
  seat_cap?: number
  seats_used?: number
  institution_pricing_tier?: InstitutionTierKey | null
  billing_cycle?: BillingCycleKey | null
}

function parseContractList(data: unknown): ContractRow[] {
  if (Array.isArray(data)) return data as ContractRow[]
  if (
    data &&
    typeof data === 'object' &&
    'results' in data &&
    Array.isArray((data as { results: unknown }).results)
  ) {
    return (data as { results: ContractRow[] }).results
  }
  return []
}

const STATUS_LABEL: Record<string, string> = {
  proposal: 'Proposal',
  negotiation: 'Negotiation',
  signed: 'Signed',
  pending_payments: 'Pending',
  active: 'Active',
  renewal: 'Renewal',
  terminated: 'Terminated',
}

function formatMoney(v: string | number) {
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function needsSetup(c: ContractRow) {
  const cap = c.seat_cap ?? 0
  return !c.institution_pricing_tier || !c.billing_cycle || cap < 1
}

export default function InstitutionContractsOverviewPage() {
  const [contracts, setContracts] = useState<ContractRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiGateway.get<unknown>('/finance/contracts/')
      const list = parseContractList(data).filter((c) => c.type === 'institution')
      setContracts(list)
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
                      <td className="py-3 px-4 text-white font-medium">{c.organization_name}</td>
                      <td className="py-3 px-4 text-och-steel whitespace-nowrap">
                        {c.start_date} → {c.end_date}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={c.status === 'active' ? 'mint' : 'gold'}>
                          {STATUS_LABEL[c.status] ?? c.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-och-steel text-xs max-w-[200px]">
                        {c.institution_pricing_tier ? INSTITUTION_TIER_LABEL[c.institution_pricing_tier] : '—'}
                        {c.billing_cycle ? (
                          <span className="block text-och-steel/80">
                            {BILLING_CYCLE_LABEL[c.billing_cycle]}
                          </span>
                        ) : null}
                      </td>
                      <td className="py-3 px-4 text-right text-white tabular-nums">{formatMoney(c.total_value)}</td>
                      <td className="py-3 px-4 text-right text-och-steel tabular-nums">
                        {c.seats_used ?? 0}/{c.seat_cap ?? 0}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/dashboard/institution/contracts/${c.id}/complete`}
                          className={`inline-flex text-xs font-semibold ${
                            needsSetup(c) ? 'text-och-gold hover:underline' : 'text-och-mint hover:underline'
                          }`}
                        >
                          {needsSetup(c) ? 'Complete licensing' : 'View / edit'}
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
