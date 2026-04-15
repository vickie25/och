'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { curriculumClient } from '@/services/curriculumClient'
import {
  BILLING_CYCLE_LABEL,
  formatUsd,
  type BillingCycleKey,
} from '@/lib/institutionContractCatalog'
import { Check, FileText } from 'lucide-react'
import { institutionalService } from '@/services/institutionalService'

const CYCLES: BillingCycleKey[] = ['monthly', 'quarterly', 'annual']

type Curriculum = {
  cohort_label?: string
  mandated_tracks?: string[]
  selected_modules?: string[]
  selected_module_ids?: string[]
  module_notes?: string
}

type ContractDetail = {
  id: string
  status: string
  start_date: string
  end_date: string
  contract_number?: string
  organization?: { id: number | string; name: string; contact_email?: string }
  student_seat_count: number
  per_student_rate: number
  billing_cycle: BillingCycleKey
}

type TrackOption = {
  code: string
  slug?: string
  name?: string
  title?: string
}

type ModuleOption = {
  id: string
  title: string
  track_key?: string
}

function trackLabel(t: TrackOption) {
  return t.title || t.name || t.code
}

export default function InstitutionCompleteContractPage() {
  const params = useParams()
  const router = useRouter()
  const contractId = typeof params.contractId === 'string' ? params.contractId : ''

  const [contract, setContract] = useState<ContractDetail | null>(null)
  const [cycle, setCycle] = useState<BillingCycleKey | null>(null)
  const [seatCount, setSeatCount] = useState<number>(0)

  const [cohortLabel, setCohortLabel] = useState('')
  const [moduleNotes, setModuleNotes] = useState('')

  const [availableTracks, setAvailableTracks] = useState<TrackOption[]>([])
  const [tracksLoading, setTracksLoading] = useState(false)
  const [selectedTrackCodes, setSelectedTrackCodes] = useState<string[]>([])
  const [selectedModuleIds, setSelectedModuleIds] = useState<string[]>([])
  const [modulesByTrack, setModulesByTrack] = useState<Record<string, ModuleOption[]>>({})

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [pendingTrackRefs, setPendingTrackRefs] = useState<string[]>([])

  const loadContract = useCallback(async () => {
    if (!contractId) return
    setLoading(true)
    setError(null)
    try {
      const c = (await institutionalService.getContract(contractId)) as ContractDetail
      setContract(c)
      setCycle(c.billing_cycle)
      setSeatCount(typeof c.student_seat_count === 'number' ? c.student_seat_count : 0)

      // Curriculum blueprint in institutional engine is handled via dedicated endpoints;
      // keep UI stable for now (best-effort no-op defaults).
      setCohortLabel('')
      setModuleNotes('')
      setPendingTrackRefs([])
      setSelectedModuleIds([])
    } catch (e: unknown) {
      setContract(null)
      setError(e instanceof Error ? e.message : 'Failed to load contract')
    } finally {
      setLoading(false)
    }
  }, [contractId])

  const loadTracks = useCallback(async () => {
    setTracksLoading(true)
    try {
      const tracks = await curriculumClient.getTracks()
      const normalized: TrackOption[] = (tracks || []).map((t: any) => ({
        code: String(t.code || ''),
        slug: typeof t.slug === 'string' ? t.slug : undefined,
        name: typeof t.name === 'string' ? t.name : undefined,
        title: typeof t.title === 'string' ? t.title : undefined,
      }))
      setAvailableTracks(normalized.filter((t) => t.code))
    } catch {
      setAvailableTracks([])
    } finally {
      setTracksLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadContract()
    void loadTracks()
  }, [loadContract, loadTracks])

  useEffect(() => {
    if (pendingTrackRefs.length === 0 || availableTracks.length === 0) return
    const refs = pendingTrackRefs.map((r) => r.toLowerCase().trim())
    const matched = availableTracks
      .filter((t) => {
        const c = t.code.toLowerCase()
        const s = (t.slug || '').toLowerCase()
        const n = (t.name || '').toLowerCase()
        const tt = (t.title || '').toLowerCase()
        return refs.some((r) => r === c || r === s || r === n || r === tt)
      })
      .map((t) => t.code)

    if (matched.length) {
      setSelectedTrackCodes((prev) => Array.from(new Set([...prev, ...matched])))
    }
    setPendingTrackRefs([])
  }, [pendingTrackRefs, availableTracks])

  useEffect(() => {
    if (selectedTrackCodes.length === 0) return
    const missing = selectedTrackCodes.filter((code) => !modulesByTrack[code])
    if (missing.length === 0) return

    let cancelled = false
    ;(async () => {
      const updates: Record<string, ModuleOption[]> = {}
      for (const code of missing) {
        try {
          const detail: any = await curriculumClient.getTrack(code)
          const modules = Array.isArray(detail?.modules) ? detail.modules : []
          updates[code] = modules.map((m: any) => ({
            id: String(m.id),
            title: String(m.title || 'Untitled module'),
            track_key: typeof m.track_key === 'string' ? m.track_key : code,
          }))
        } catch {
          updates[code] = []
        }
      }
      if (!cancelled) {
        setModulesByTrack((prev) => ({ ...prev, ...updates }))
      }
    })()

    return () => {
      cancelled = true
    }
  }, [selectedTrackCodes, modulesByTrack])

  const allSelectableModules = useMemo(() => {
    const list = selectedTrackCodes.flatMap((code) => modulesByTrack[code] || [])
    const seen = new Set<string>()
    const deduped: ModuleOption[] = []
    for (const m of list) {
      if (!seen.has(m.id)) {
        seen.add(m.id)
        deduped.push(m)
      }
    }
    return deduped
  }, [selectedTrackCodes, modulesByTrack])

  useEffect(() => {
    const availableIds = new Set(allSelectableModules.map((m) => m.id))
    if (availableIds.size === 0) {
      setSelectedModuleIds([])
      return
    }
    setSelectedModuleIds((prev) => prev.filter((id) => availableIds.has(id)))
  }, [allSelectableModules])

  const toggleTrack = (code: string) => {
    setSelectedTrackCodes((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]))
  }

  const toggleModule = (id: string) => {
    setSelectedModuleIds((prev) => (prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]))
  }

  const save = async () => {
    if (!contractId || !cycle || seatCount < 1) return
    setSaving(true)
    setError(null)

    try {
      await institutionalService.updateContractSeatsAndBilling(contractId, {
        student_seat_count: seatCount,
        billing_cycle: cycle,
      })
      await loadContract()
      router.push('/dashboard/institution/contracts/invoices')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Could not save')
    } finally {
      setSaving(false)
    }
  }

  const previewRate = typeof contract?.per_student_rate === 'number' ? contract.per_student_rate : null
  const previewMonthly = previewRate != null && seatCount >= 1 ? previewRate * seatCount : null
  const previewPeriod =
    previewMonthly != null
      ? cycle === 'monthly'
        ? previewMonthly
        : cycle === 'quarterly'
          ? previewMonthly * 3
          : previewMonthly * 12 * 0.98
      : null

  if (loading) {
    return (
      <div className="min-h-screen bg-och-midnight p-6 flex items-center justify-center text-och-steel text-sm">
        Loading...
      </div>
    )
  }

  if (error && !contract) {
    return (
      <div className="min-h-screen bg-och-midnight p-6 max-w-lg mx-auto">
        <p className="text-red-300 text-sm">{error}</p>
        <Link href="/dashboard/institution/contracts" className="text-och-mint text-sm mt-4 inline-block">
          Back
        </Link>
      </div>
    )
  }

  if (!contract || contract.type !== 'institution') {
    return (
      <div className="min-h-screen bg-och-midnight p-6">
        <p className="text-och-steel text-sm">Contract not found.</p>
        <Link href="/dashboard/institution/contracts" className="text-och-mint text-sm mt-4 inline-block">
          Contracts
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link href="/dashboard/institution/contracts" className="text-sm text-och-mint hover:underline">
              Contracts
            </Link>
            <h1 className="text-2xl font-bold text-och-gold mt-2">Licensing &amp; curriculum blueprint</h1>
            <p className="text-och-steel text-sm mt-1">{contract.organization_name}</p>
          </div>
          <Link
            href="/dashboard/institution/contracts/commercial-terms"
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
              <p className="text-white">{contract.start_date} - {contract.end_date}</p>
            </div>
            <div>
              <p className="text-xs text-och-steel">Seats (allocated / used)</p>
              <p className="text-white">
                {contract.student_seat_count ?? 0} licensed - {(contract as any).active_students ?? 0} active
              </p>
            </div>
            <div>
              <p className="text-xs text-och-steel">Indicative period charge</p>
              <p className="text-white">{previewPeriod != null ? formatUsd(previewPeriod) : '-'}</p>
            </div>
          </div>
        </Card>

        {error && (
          <div className="rounded-lg border border-och-orange/40 bg-och-orange/10 px-4 py-2 text-sm text-och-orange">
            {error}
          </div>
        )}

        <Card className="border border-och-steel/25 p-4 space-y-2">
          <h2 className="text-sm font-semibold text-white">Per-student rate</h2>
          <p className="text-xs text-och-steel">
            Your rate is automatically determined by licensed seat count (volume pricing). Current rate:{' '}
            <span className="text-white">{typeof contract.per_student_rate === 'number' ? formatUsd(contract.per_student_rate) : '—'}</span>{' '}
            <span className="text-och-steel">/ student / month</span>
          </p>
        </Card>

        <div>
          <h2 className="text-sm font-semibold text-white mb-3">Billing cycle</h2>
          <div className="flex flex-wrap gap-2">
            {CYCLES.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCycle(c)}
                className={`rounded-lg border px-4 py-2 text-sm ${
                  cycle === c
                    ? 'border-och-mint bg-och-mint/15 text-white'
                    : 'border-och-steel/30 text-och-steel hover:border-och-steel/50'
                }`}
              >
                {BILLING_CYCLE_LABEL[c]}
              </button>
            ))}
          </div>
        </div>

        <Card className="border border-och-steel/25 p-4 space-y-3">
          <div>
            <label className="text-xs text-och-steel block mb-1">Student seat count (contracted)</label>
            <input
              type="number"
              min={1}
              className="w-full max-w-xs rounded-md border border-och-steel/30 bg-och-midnight px-3 py-2 text-white text-sm"
              value={seatCount || ''}
              onChange={(e) => setSeatCount(parseInt(e.target.value, 10) || 0)}
            />
            <p className="text-xs text-och-steel mt-1">Seat changes mid-cycle are prorated and reflected on the next invoice.</p>
          </div>
        </Card>

        <Card className="border border-och-steel/25 p-4 space-y-4">
          <h2 className="text-sm font-semibold text-white">Curriculum blueprint (director-visible)</h2>

          <div>
            <label className="text-xs text-och-steel block mb-1">Cohort or intake label</label>
            <input
              type="text"
              className="w-full rounded-md border border-och-steel/30 bg-och-midnight px-3 py-2 text-white text-sm"
              placeholder="e.g. Fall 2025 Engineering"
              value={cohortLabel}
              onChange={(e) => setCohortLabel(e.target.value)}
            />
          </div>

          <div>
            <label className="text-xs text-och-steel block mb-2">Mandated tracks (select one or more)</label>
            {tracksLoading ? (
              <p className="text-xs text-och-steel">Loading tracks...</p>
            ) : availableTracks.length === 0 ? (
              <p className="text-xs text-och-orange">No tracks returned from OCH curriculum API.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 rounded-md border border-och-steel/20 p-3">
                {availableTracks.map((t) => {
                  const checked = selectedTrackCodes.includes(t.code)
                  return (
                    <label key={t.code} className="flex items-center gap-2 text-sm text-och-steel cursor-pointer">
                      <input
                        type="checkbox"
                        className="rounded border-och-steel/40"
                        checked={checked}
                        onChange={() => toggleTrack(t.code)}
                      />
                      <span className={checked ? 'text-white' : ''}>{trackLabel(t)}</span>
                    </label>
                  )
                })}
              </div>
            )}
          </div>

          <div>
            <label className="text-xs text-och-steel block mb-2">Modules from selected tracks (optional multi-select)</label>
            {selectedTrackCodes.length === 0 ? (
              <p className="text-xs text-och-steel">Select at least one track to load modules.</p>
            ) : allSelectableModules.length === 0 ? (
              <p className="text-xs text-och-steel">No modules available for selected tracks yet.</p>
            ) : (
              <div className="max-h-64 overflow-y-auto rounded-md border border-och-steel/20 p-3 space-y-2">
                {allSelectableModules.map((m) => {
                  const checked = selectedModuleIds.includes(m.id)
                  return (
                    <label key={m.id} className="flex items-center gap-2 text-sm text-och-steel cursor-pointer">
                      <input
                        type="checkbox"
                        className="rounded border-och-steel/40"
                        checked={checked}
                        onChange={() => toggleModule(m.id)}
                      />
                      <span className={checked ? 'text-white' : ''}>{m.title}</span>
                    </label>
                  )
                })}
              </div>
            )}
          </div>

          <div>
            <label className="text-xs text-och-steel block mb-1">Optional modules / notes</label>
            <textarea
              className="w-full min-h-[60px] rounded-md border border-och-steel/30 bg-och-midnight px-3 py-2 text-white text-sm"
              placeholder="Electives or department-specific requirements"
              value={moduleNotes}
              onChange={(e) => setModuleNotes(e.target.value)}
            />
          </div>
        </Card>

        <div className="flex flex-wrap gap-3">
          <Button variant="gold" disabled={!cycle || seatCount < 1 || saving} onClick={() => void save()}>
            {saving ? 'Saving...' : 'Save & view invoices'}
          </Button>
          <Link
            href="/dashboard/institution/students"
            className="inline-flex items-center rounded-lg border border-och-steel/35 px-4 py-2 text-sm text-och-mint hover:bg-och-defender/20"
          >
            Students (after activation)
          </Link>
        </div>
      </div>
    </div>
  )
}
