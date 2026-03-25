'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import {
  EMPLOYER_PLAN_LABEL,
  TIER_COMPARISON,
  RETAINER_FEATURES,
  formatUsd,
  type EmployerPlanKey,
} from '@/lib/employerPlanCatalog'
import { Check, FileText } from 'lucide-react'

type ContractDetail = {
  id: string
  organization_name: string
  type: string
  status: string
  start_date: string
  end_date: string
  total_value: string | number
  payment_terms: string
  seat_cap?: number
  seats_used?: number
  employer_plan: EmployerPlanKey | null
}

export default function CompleteContractPage() {
  const params = useParams()
  const router = useRouter()
  const contractId = typeof params.contractId === 'string' ? params.contractId : ''

  const [contract, setContract] = useState<ContractDetail | null>(null)
  const [selected, setSelected] = useState<EmployerPlanKey | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!contractId) return
    setLoading(true)
    setError(null)
    try {
      const c = await apiGateway.get<ContractDetail>(`/finance/contracts/${contractId}/`)
      setContract(c)
      setSelected((c.employer_plan as EmployerPlanKey) || null)
    } catch (e: unknown) {
      setContract(null)
      setError(e instanceof Error ? e.message : 'Failed to load contract')
    } finally {
      setLoading(false)
    }
  }, [contractId])

  useEffect(() => {
    void load()
  }, [load])

  const savePlan = async () => {
    if (!contractId || !selected) return
    setSaving(true)
    setError(null)
    try {
      await apiGateway.patch(`/finance/contracts/${contractId}/`, { employer_plan: selected })
      await load()
      router.push('/dashboard/employer/contracts/invoices')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not save plan')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-och-midnight p-6 flex items-center justify-center text-och-steel text-sm">
        Loading…
      </div>
    )
  }

  if (error && !contract) {
    return (
      <div className="min-h-screen bg-och-midnight p-6 max-w-lg mx-auto">
        <p className="text-red-300 text-sm">{error}</p>
        <Link href="/dashboard/employer/contracts" className="text-och-mint text-sm mt-4 inline-block">
          ← Back
        </Link>
      </div>
    )
  }

  if (!contract || contract.type !== 'employer') {
    return (
      <div className="min-h-screen bg-och-midnight p-6">
        <p className="text-och-steel text-sm">Contract not found.</p>
        <Link href="/dashboard/employer/contracts" className="text-och-mint text-sm mt-4 inline-block">
          ← Contracts
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link href="/dashboard/employer/contracts" className="text-sm text-och-mint hover:underline">
              ← Contracts
            </Link>
            <h1 className="text-2xl font-bold text-och-gold mt-2">Contract &amp; plan</h1>
            <p className="text-och-steel text-sm mt-1">{contract.organization_name}</p>
          </div>
          <Link
            href="/dashboard/employer/contracts/commercial-terms"
            className="inline-flex items-center gap-2 text-xs font-medium text-och-mint border border-och-steel/30 rounded-lg px-3 py-2 hover:bg-och-defender/20"
          >
            <FileText className="h-4 w-4" />
            Full terms (print/PDF)
          </Link>
        </div>

        <Card className="border border-och-steel/25 p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-xs text-och-steel">Status</p>
              <Badge variant="gold">{contract.status}</Badge>
            </div>
            <div>
              <p className="text-xs text-och-steel">Term</p>
              <p className="text-white">
                {contract.start_date} → {contract.end_date}
              </p>
            </div>
            <div>
              <p className="text-xs text-och-steel">Seats</p>
              <p className="text-white">
                {contract.seats_used ?? 0} / {contract.seat_cap ?? 0}
              </p>
            </div>
            <div>
              <p className="text-xs text-och-steel">Current plan</p>
              <p className="text-white">
                {contract.employer_plan ? EMPLOYER_PLAN_LABEL[contract.employer_plan] : '—'}
              </p>
            </div>
          </div>
        </Card>

        {error && (
          <div className="rounded-lg border border-och-orange/40 bg-och-orange/10 px-4 py-2 text-sm text-och-orange">
            {error}
          </div>
        )}

        <div>
          <h2 className="text-sm font-semibold text-white mb-3">Choose a plan</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {TIER_COMPARISON.map((row) => {
              const active = selected === row.key
              return (
                <button
                  key={row.key}
                  type="button"
                  onClick={() => setSelected(row.key)}
                  className={`text-left rounded-xl border p-4 transition-colors ${
                    active
                      ? 'border-och-mint bg-och-mint/10 ring-1 ring-och-mint/40'
                      : 'border-och-steel/30 hover:border-och-steel/50 bg-och-midnight/80'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-semibold text-white">{EMPLOYER_PLAN_LABEL[row.key]}</span>
                    {active && <Check className="h-5 w-5 text-och-mint shrink-0" />}
                  </div>
                  <dl className="space-y-1 text-xs text-och-steel">
                    <div className="flex justify-between gap-2">
                      <dt>Monthly retainer</dt>
                      <dd className="text-white">{formatUsd(row.monthlyUsd)}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt>Candidates / qtr</dt>
                      <dd className="text-white">{row.candidatesPerQuarter}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt>Placement fee</dt>
                      <dd className="text-white">{formatUsd(row.placementFeeUsd)}</dd>
                    </div>
                    <div className="flex justify-between gap-2">
                      <dt>Account manager</dt>
                      <dd className="text-white">{row.dedicatedAm ? 'Yes' : 'No'}</dd>
                    </div>
                    <p className="text-och-steel/90 pt-1 border-t border-och-steel/20 mt-2">
                      {RETAINER_FEATURES[row.key]}
                    </p>
                  </dl>
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <Button variant="gold" disabled={!selected || saving} onClick={() => void savePlan()}>
            {saving ? 'Saving…' : 'Save plan selection'}
          </Button>
          <Link
            href="/dashboard/employer/contracts/commercial-terms"
            className="inline-flex items-center justify-center rounded-lg border border-och-steel/40 px-4 py-2 text-sm text-och-steel hover:text-white"
          >
            Read full commercial reference
          </Link>
        </div>
      </div>
    </div>
  )
}
