'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'

type PaymentRow = {
  id: string
  invoice_number?: string | null
  amount: string | number
  currency: string
  status: string
  payment_method?: string | null
  paystack_reference?: string | null
  created_at: string
}

function parseList(data: unknown): PaymentRow[] {
  if (Array.isArray(data)) return data as PaymentRow[]
  if (
    data &&
    typeof data === 'object' &&
    'results' in data &&
    Array.isArray((data as { results: unknown }).results)
  ) {
    return (data as { results: PaymentRow[] }).results
  }
  return []
}

function formatMoney(v: string | number, currency: string) {
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (Number.isNaN(n)) return '—'
  const cur = (currency || 'KES').toUpperCase()
  try {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: cur === 'KSH' ? 'KES' : cur,
      maximumFractionDigits: 0,
    }).format(n)
  } catch {
    return `${cur} ${n.toLocaleString()}`
  }
}

export default function EmployerPaymentsPage() {
  const [rows, setRows] = useState<PaymentRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiGateway.get<unknown>('/finance/payments/')
      setRows(parseList(data))
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load payments'
      setError(msg)
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <Link
            href="/dashboard/employer/contracts"
            className="text-sm font-medium text-och-mint hover:text-och-mint/80 mb-2 inline-block"
          >
            ← Contract overview
          </Link>
          <h1 className="text-2xl font-bold text-och-gold">Payments</h1>
        </div>

        {error && (
          <div className="rounded-lg border border-och-orange/40 bg-och-orange/10 px-4 py-3 text-sm text-och-orange">
            {error}
          </div>
        )}

        <Card className="border border-och-steel/20 p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-och-steel/30 text-xs uppercase tracking-wide text-och-steel bg-och-steel/5">
                <tr>
                  <th className="py-3 px-4 text-left">Invoice</th>
                  <th className="py-3 px-4 text-left">Amount</th>
                  <th className="py-3 px-4 text-left">Status</th>
                  <th className="py-3 px-4 text-left">Method</th>
                  <th className="py-3 px-4 text-left">Reference</th>
                  <th className="py-3 px-4 text-left">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-och-steel/15">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-10 px-4 text-center text-och-steel">
                      Loading payments…
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-10 px-4 text-center text-och-steel">
                      No payments recorded yet. They will appear here after you pay an invoice.
                    </td>
                  </tr>
                ) : (
                  rows.map((p) => (
                    <tr key={p.id} className="hover:bg-och-steel/10">
                      <td className="py-3 px-4 text-white font-mono text-xs">{p.invoice_number ?? '—'}</td>
                      <td className="py-3 px-4 text-white">{formatMoney(p.amount, p.currency)}</td>
                      <td className="py-3 px-4">
                        <Badge variant={p.status === 'completed' || p.status === 'success' ? 'mint' : 'gold'}>
                          {p.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-och-steel">{p.payment_method ?? '—'}</td>
                      <td className="py-3 px-4 text-och-steel font-mono text-xs">
                        {p.paystack_reference ?? '—'}
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        {p.created_at ? new Date(p.created_at).toLocaleString() : '—'}
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
