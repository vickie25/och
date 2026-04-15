'use client'

import { useEffect, useState, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import {
  FileSignature,
  ArrowRight,
  Loader2,
  CheckCircle2,
  Users,
  GraduationCap,
  X,
} from 'lucide-react'
import { BILLING_CYCLE_LABEL } from '@/lib/institutionContractCatalog'
import { institutionalService, type InstitutionalContractListItem } from '@/services/institutionalService'

const STATUS_LABEL: Record<string, string> = {
  active: 'Active',
  draft: 'Draft',
  pending_renewal: 'Pending renewal',
  expired: 'Expired',
  terminated: 'Terminated',
}

function needsAcceptance(status: string) {
  return status === 'draft'
}

function formatMoneyUsd(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export default function InstitutionClient() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const urlCleaned = useRef(false)

  const [contracts, setContracts] = useState<InstitutionalContractListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [welcomeBanner, setWelcomeBanner] = useState(false)
  const [acceptingId, setAcceptingId] = useState<string | null>(null)
  const [termsChecked, setTermsChecked] = useState(false)

  const loadContracts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await institutionalService.listContracts()
      setContracts(Array.isArray(data?.contracts) ? data.contracts : [])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load contracts'
      setError(msg)
      setContracts([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadContracts()
  }, [loadContracts])

  useEffect(() => {
    if (urlCleaned.current) return
    if (!searchParams.toString()) return
    const contract = searchParams.get('contract')
    const created = searchParams.get('created')
    if (contract) {
      try {
        sessionStorage.setItem('och_institution_focus_contract', contract)
      } catch {
        /* ignore */
      }
    }
    if (created === '1') setWelcomeBanner(true)
    urlCleaned.current = true
    router.replace('/dashboard/institution', { scroll: false })
  }, [searchParams, router])

  const focusId =
    typeof window !== 'undefined' ? sessionStorage.getItem('och_institution_focus_contract') : null

  const primaryContract = (() => {
    if (focusId) {
      const hit = contracts.find((c) => c.id === focusId)
      if (hit) return hit
    }
    const needSign = contracts.find((c) => needsAcceptance(c.status))
    const firstLive = contracts.find((c) => c.status !== 'terminated')
    return needSign ?? firstLive ?? contracts[0] ?? null
  })()

  const showAcceptGate = primaryContract && needsAcceptance(primaryContract.status)
  const showLicensingGate = false

  const handleAcceptContract = async (id: string) => {
    if (!termsChecked) return
    setAcceptingId(id)
    setError(null)
    try {
      await institutionalService.activateContract(id)
      try {
        sessionStorage.removeItem('och_institution_focus_contract')
      } catch {
        /* ignore */
      }
      setTermsChecked(false)
      await loadContracts()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Could not update contract'
      setError(msg)
    } finally {
      setAcceptingId(null)
    }
  }

  return (
    <div className="w-full max-w-7xl py-8 px-4 sm:px-6 lg:pl-0 lg:pr-6 xl:pr-8 space-y-8">
      {welcomeBanner && (
        <div className="flex items-start justify-between gap-4 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
          <p>
            <span className="font-medium text-emerald-50">Welcome.</span> Your institution account is ready. Complete
            licensing on your contract, pay the generated invoice, then enroll students within your seat cap.
          </p>
          <button
            type="button"
            onClick={() => setWelcomeBanner(false)}
            className="shrink-0 rounded p-1 text-emerald-200 hover:bg-emerald-500/20"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="mb-2">
        <h1 className="text-3xl sm:text-4xl font-bold mb-2 text-white tracking-tight">Institution dashboard</h1>
        <p className="text-och-steel text-base max-w-2xl">
          Your finance contract sets per-student tier, billing cycle, and a curriculum blueprint. Students inherit that
          tier under an active contract.
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-100">{error}</div>
      )}

      {loading ? (
        <div className="flex flex-col items-center gap-4 min-h-[40vh] justify-center">
          <div className="w-10 h-10 border-2 border-och-mint/40 border-t-och-mint rounded-full animate-spin" aria-hidden />
          <p className="text-och-steel text-sm font-medium">Loading dashboard…</p>
        </div>
      ) : (
        <>
          {showAcceptGate && primaryContract && (
            <Card className="border-2 border-och-gold/40 bg-och-midnight/80 p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-och-gold">
                    <FileSignature className="h-5 w-5" />
                    <span className="font-semibold text-lg text-white">Accept your contract</span>
                  </div>
                  <p className="text-sm text-och-steel max-w-xl">
                    Review the institutional agreement. When you accept, your contract becomes <strong className="text-white">Active</strong>{' '}
                    and invoicing starts on the configured billing cycle (net 30).
                  </p>
                  <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-2 text-sm mt-4">
                    <div>
                      <dt className="text-och-steel">Organization</dt>
                      <dd className="text-white font-medium">{primaryContract.organization?.name}</dd>
                    </div>
                    <div>
                      <dt className="text-och-steel">Status</dt>
                      <dd>
                        <Badge variant="gold">{STATUS_LABEL[primaryContract.status] ?? primaryContract.status}</Badge>
                      </dd>
                    </div>
                    <div>
                      <dt className="text-och-steel">Term</dt>
                      <dd className="text-white">
                        {primaryContract.start_date} → {primaryContract.end_date}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-och-steel">Licensed seats</dt>
                      <dd className="text-white">{primaryContract.student_seat_count ?? 0}</dd>
                    </div>
                  </dl>
                  <label className="flex items-start gap-3 text-sm text-och-steel mt-4 cursor-pointer">
                    <input
                      type="checkbox"
                      className="mt-1 rounded border-och-steel/40"
                      checked={termsChecked}
                      onChange={(e) => setTermsChecked(e.target.checked)}
                    />
                    <span>
                      I confirm our institution has reviewed this contract proposal and authorizes OCH to proceed on
                      the terms shown (including 12-month commitment where applicable), subject to invoicing by
                      Finance.
                    </span>
                  </label>
                </div>
                <div className="flex flex-col gap-2 shrink-0">
                  <Button
                    variant="gold"
                    className="whitespace-nowrap"
                    disabled={!termsChecked || acceptingId === primaryContract.id}
                    onClick={() => void handleAcceptContract(primaryContract.id)}
                  >
                    {acceptingId === primaryContract.id ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Saving…
                      </>
                    ) : (
                      <>
                        Accept contract
                        <CheckCircle2 className="h-4 w-4 ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {showLicensingGate && primaryContract && (
            <Card className="border border-och-mint/35 bg-och-midnight/80 p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-start gap-3">
                  <GraduationCap className="h-6 w-6 text-och-mint shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-white">Complete licensing &amp; blueprint</p>
                    <p className="text-sm text-och-steel mt-1 max-w-xl">
                      Choose volume tier, billing cycle, seat count, and document mandated tracks / cohort intent. An
                      invoice is generated for Finance review.
                    </p>
                  </div>
                </div>
                <Link
                  href={`/dashboard/institution/contracts/${primaryContract.id}/complete`}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-och-mint px-4 py-2.5 text-sm font-semibold text-och-midnight hover:bg-och-mint/90 shrink-0"
                >
                  Configure contract
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </Card>
          )}

          {!showAcceptGate && !showLicensingGate && primaryContract && (
            <Card className="p-5 border border-och-steel/20">
              <div className="flex items-center gap-3 text-emerald-200">
                <CheckCircle2 className="h-6 w-6 shrink-0" />
                <div>
                  <p className="font-medium text-white">Licensing configured</p>
                  <p className="text-sm text-och-steel">
                    {primaryContract.organization?.name} —{' '}
                    <Badge variant="mint">{STATUS_LABEL[primaryContract.status] ?? primaryContract.status}</Badge>
                    {' · '}
                    {typeof primaryContract.per_student_rate === 'number'
                      ? `${formatMoneyUsd(primaryContract.per_student_rate)}/student/mo`
                      : 'Rate —'}
                    {' · Seats '}
                    {primaryContract.active_students ?? 0}/{primaryContract.student_seat_count ?? 0}
                    {' · '}
                    {primaryContract.billing_cycle ? BILLING_CYCLE_LABEL[primaryContract.billing_cycle as any] : 'Billing —'}
                  </p>
                </div>
              </div>
            </Card>
          )}

          {contracts.length === 0 && (
            <Card className="p-6 border border-dashed border-och-steel/30">
              <p className="text-och-steel text-sm mb-2">No institution contracts are linked to your organization yet.</p>
              <p className="text-xs text-och-steel/80">
                After Finance creates your agreement, it will appear here. If you just finished onboarding, refresh in
                a moment or contact your director.
              </p>
            </Card>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-och-steel">Contracts</span>
                <FileSignature className="h-4 w-4 text-och-gold" />
              </div>
              <p className="text-2xl font-bold text-white">{contracts.length}</p>
              <p className="text-xs text-och-steel mt-1">Institutional agreements</p>
              <Link
                href="/dashboard/institution/contracts"
                className="inline-flex items-center gap-1 text-sm text-och-mint mt-3 hover:underline"
              >
                Open contracts <ArrowRight className="h-3 w-3" />
              </Link>
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-och-steel">Students</span>
                <Users className="h-4 w-4 text-och-gold" />
              </div>
              <p className="text-2xl font-bold text-white">
                {primaryContract ? `${primaryContract.active_students ?? 0} / ${primaryContract.student_seat_count ?? 0}` : '—'}
              </p>
              <p className="text-xs text-och-steel mt-1">Active vs allocated seats</p>
              <Link
                href="/dashboard/institution/students"
                className="inline-flex items-center gap-1 text-sm text-och-mint mt-3 hover:underline"
              >
                Manage students <ArrowRight className="h-3 w-3" />
              </Link>
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-och-steel">Invoices</span>
                <GraduationCap className="h-4 w-4 text-och-gold" />
              </div>
              <p className="text-sm text-och-steel">Per tier × seats × billing cycle</p>
              <Link
                href="/dashboard/institution/contracts/invoices"
                className="inline-flex items-center gap-1 text-sm text-och-mint mt-3 hover:underline"
              >
                View invoices <ArrowRight className="h-3 w-3" />
              </Link>
            </Card>
          </div>

          {contracts.length > 0 && (
            <Card className="p-0 overflow-hidden border border-och-steel/20">
              <div className="px-5 py-3 border-b border-och-steel/15 bg-och-steel/5">
                <h2 className="text-sm font-semibold text-white">Your contracts</h2>
              </div>
              <ul className="divide-y divide-och-steel/10">
                {contracts.map((c) => (
                  <li key={c.id} className="px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div>
                      <p className="text-white font-medium">{c.organization?.name}</p>
                      <p className="text-xs text-och-steel">
                        {c.start_date} — {c.end_date} · {formatMoneyUsd(c.annual_amount)} · Seats {c.active_students ?? 0}/
                        {c.student_seat_count ?? 0}
                        {c.billing_cycle ? ` · ${BILLING_CYCLE_LABEL[c.billing_cycle as any]}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={needsAcceptance(c.status) ? 'gold' : 'mint'}>
                        {STATUS_LABEL[c.status] ?? c.status}
                      </Badge>
                      <Link
                        href={`/dashboard/institution/contracts/${c.id}/complete`}
                        className="text-xs font-semibold text-och-mint hover:underline"
                      >
                        Details
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
