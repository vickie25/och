'use client'

import { useEffect, useState } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import financeService, { type CohortManagerFinanceSummary } from '@/services/financeService'
import { apiGateway } from '@/services/apiGateway'

type CohortRow = { id: string; name: string }

export default function DirectorCohortFinancePage() {
  const [cohorts, setCohorts] = useState<CohortRow[]>([])
  const [cohortId, setCohortId] = useState('')
  const [data, setData] = useState<CohortManagerFinanceSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await apiGateway.get('/cohorts/')
        const list = Array.isArray(res) ? res : res?.results || []
        if (!cancelled) {
          setCohorts(list.map((c: { id: string; name: string }) => ({ id: c.id, name: c.name })))
        }
      } catch {
        if (!cancelled) setCohorts([])
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const load = async () => {
    if (!cohortId) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const d = await financeService.getCohortManagerFinance(cohortId)
      setData(d)
    } catch {
      setError('Unable to load cohort finance (check coordinator access or cohort id).')
    } finally {
      setLoading(false)
    }
  }

  return (
    <RouteGuard requiredRoles={['program_director', 'admin']}>
      <div className="min-h-screen bg-och-midnight text-white px-4 py-8 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">Cohort finance</h1>
        <p className="text-och-steel text-sm mb-6">
          Enrollment mix, seat configuration, and cohort payment totals for coordinators and program directors.
        </p>

        <Card className="p-6 bg-och-midnight border border-och-steel/20 space-y-4 mb-6">
          <div className="flex flex-wrap gap-3 items-end">
            <label className="text-sm text-och-steel flex-1 min-w-[200px]">
              Cohort
              <select
                className="mt-1 w-full rounded bg-och-steel/10 border border-och-steel/30 px-3 py-2 text-white"
                value={cohortId}
                onChange={(e) => setCohortId(e.target.value)}
              >
                <option value="">Select cohort…</option>
                {cohorts.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <Button type="button" onClick={load} disabled={loading || !cohortId}>
              {loading ? 'Loading…' : 'Load'}
            </Button>
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </Card>

        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="p-4 border border-och-steel/20 bg-och-midnight/80">
              <h2 className="font-semibold text-och-mint mb-2">{data.cohort_name}</h2>
              <p className="text-sm text-och-steel">Status: {data.status}</p>
              <p className="text-sm text-och-steel">Seat cap: {data.seat_cap}</p>
              <p className="text-sm text-och-steel">Enrollments: {data.enrollment_total}</p>
            </Card>
            <Card className="p-4 border border-och-steel/20 bg-och-midnight/80">
              <h2 className="font-semibold text-och-mint mb-2">Payments</h2>
              <p className="text-lg text-white">
                {data.cohort_payment_revenue.toLocaleString()} {data.cohort_payment_currency}
              </p>
              <p className="text-sm text-och-steel">Completed payments: {data.completed_payments_count}</p>
            </Card>
            <Card className="p-4 border border-och-steel/20 bg-och-midnight/80 md:col-span-2">
              <h2 className="font-semibold text-och-mint mb-2">Seat mix</h2>
              <pre className="text-xs text-och-steel overflow-x-auto">
                {JSON.stringify(data.enrollment_by_seat_type, null, 2)}
              </pre>
              <h3 className="text-sm font-medium text-white mt-4 mb-1">Seat pool config</h3>
              <pre className="text-xs text-och-steel overflow-x-auto">
                {JSON.stringify(data.seat_pool_config, null, 2)}
              </pre>
            </Card>
          </div>
        )}
      </div>
    </RouteGuard>
  )
}
