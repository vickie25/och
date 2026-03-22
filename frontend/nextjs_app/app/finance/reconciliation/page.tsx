'use client'

import { useState } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import financeService from '@/services/financeService'

export default function FinanceReconciliationPage() {
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')
  const [bankTotal, setBankTotal] = useState('')
  const [currency, setCurrency] = useState('USD')
  const [preview, setPreview] = useState<string | null>(null)
  const [result, setResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const onPreview = async () => {
    if (!start || !end) return
    setLoading(true)
    setPreview(null)
    try {
      const p = await financeService.previewReconciliation(start, end, currency)
      setPreview(`Book total: ${p.book_total} ${p.currency} (${p.payment_records_count} payment records in range)`)
    } catch (e: unknown) {
      const detail =
        e && typeof e === 'object' && 'response' in e
          ? JSON.stringify((e as { response?: unknown }).response)
          : e instanceof Error
            ? e.message
            : String(e)
      setPreview(`Preview failed: ${detail}. Ensure your user has the finance role (RBAC) or Django staff, and dates are valid.`)
    } finally {
      setLoading(false)
    }
  }

  const onRun = async () => {
    if (!start || !end || bankTotal === '') return
    setLoading(true)
    setResult(null)
    try {
      const r = await financeService.runReconciliation({
        period_start: start,
        period_end: end,
        bank_total: Number(bankTotal),
        currency,
        notes: 'UI reconciliation run',
      })
      setResult(`Saved run ${r.id}. Book ${r.book_total}, bank ${r.bank_total}, difference ${r.difference}`)
    } catch (e: unknown) {
      const detail = e instanceof Error ? e.message : String(e)
      setResult(`Run failed: ${detail}. Finance role or staff required.`)
    } finally {
      setLoading(false)
    }
  }

  const onRecognize = async () => {
    if (!start || !end) return
    setLoading(true)
    try {
      const r = await financeService.runRevenueRecognition(start, end, currency)
      setResult(`Revenue recognition: created ${r.created}, skipped ${r.skipped_existing}`)
    } catch {
      setResult('Recognition failed — admin role required.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight text-white px-4 py-8 max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold mb-2">Reconciliation & revenue recognition</h1>
        <p className="text-och-steel text-sm mb-6">
          Compare recorded payments (book) to a bank statement total for the period. Revenue recognition posts paid
          invoices into analytics streams.
        </p>

        <Card className="p-6 bg-och-midnight border border-och-steel/20 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="text-sm text-och-steel">
              Period start
              <input
                type="date"
                className="mt-1 w-full rounded bg-och-steel/10 border border-och-steel/30 px-3 py-2 text-white"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </label>
            <label className="text-sm text-och-steel">
              Period end
              <input
                type="date"
                className="mt-1 w-full rounded bg-och-steel/10 border border-och-steel/30 px-3 py-2 text-white"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </label>
            <label className="text-sm text-och-steel">
              Currency
              <input
                className="mt-1 w-full rounded bg-och-steel/10 border border-och-steel/30 px-3 py-2 text-white"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
              />
            </label>
            <label className="text-sm text-och-steel">
              Bank / processor total
              <input
                type="number"
                className="mt-1 w-full rounded bg-och-steel/10 border border-och-steel/30 px-3 py-2 text-white"
                value={bankTotal}
                onChange={(e) => setBankTotal(e.target.value)}
                placeholder="e.g. statement total"
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" disabled={loading} onClick={onPreview}>
              Preview book total
            </Button>
            <Button type="button" disabled={loading} onClick={onRun}>
              Save reconciliation run
            </Button>
            <Button type="button" variant="outline" disabled={loading} onClick={onRecognize}>
              Recognize revenue (invoices)
            </Button>
          </div>

          {preview && <p className="text-sm text-och-mint">{preview}</p>}
          {result && <p className="text-sm text-och-gold">{result}</p>}
        </Card>
      </div>
    </RouteGuard>
  )
}
