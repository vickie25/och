'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'

type InvoiceRow = {
  id: string
  invoice_number: string
  organization_name?: string | null
  contract_id?: string | null
  type: string
  total: string | number
  payment_status?: 'unpaid' | 'partially_paid' | 'fully_paid'
  amount_paid?: string | number
  amount_remaining?: string | number
  status: string
  due_date?: string | null
  paid_date?: string | null
  created_at: string
  pdf_url?: string | null
}

function parseList(data: unknown): InvoiceRow[] {
  if (Array.isArray(data)) return data as InvoiceRow[]
  if (
    data &&
    typeof data === 'object' &&
    'results' in data &&
    Array.isArray((data as { results: unknown }).results)
  ) {
    return (data as { results: InvoiceRow[] }).results
  }
  return []
}

function formatMoney(v: string | number) {
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(n)
}

export default function InstitutionInvoicesPage() {
  const [rows, setRows] = useState<InvoiceRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await apiGateway.get<unknown>('/finance/invoices/')
      const list = parseList(data).filter((r) => r.type === 'institution')
      setRows(list)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to load invoices'
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
            href="/dashboard/institution/contracts"
            className="text-sm font-medium text-och-mint hover:text-och-mint/80 mb-2 inline-block"
          >
            ← Contract overview
          </Link>
          <h1 className="text-2xl font-bold text-och-gold">Invoices</h1>
          <p className="text-sm text-och-steel mt-1">
            Institution license invoices (per tier × seats × billing period). Net 30 unless otherwise stated on the
            invoice.
          </p>
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
                  <th className="py-3 px-4 text-left">Invoice #</th>
                  <th className="py-3 px-4 text-left">Organization</th>
                  <th className="py-3 px-4 text-left">Contract</th>
                  <th className="py-3 px-4 text-left">Amount</th>
                  <th className="py-3 px-4 text-left">Payment</th>
                  <th className="py-3 px-4 text-left">Status</th>
                  <th className="py-3 px-4 text-left">Due</th>
                  <th className="py-3 px-4 text-left">Paid</th>
                  <th className="py-3 px-4 text-left">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-och-steel/15">
                {loading ? (
                  <tr>
                    <td colSpan={9} className="py-10 px-4 text-center text-och-steel">
                      Loading invoices…
                    </td>
                  </tr>
                ) : rows.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-10 px-4 text-center text-och-steel">
                      No institution invoices yet. Complete licensing on your contract to generate billing.
                    </td>
                  </tr>
                ) : (
                  rows.map((inv) => (
                    <tr key={inv.id} className="hover:bg-och-steel/10">
                      <td className="py-3 px-4 text-white font-mono text-xs">{inv.invoice_number}</td>
                      <td className="py-3 px-4 text-och-steel">{inv.organization_name ?? '—'}</td>
                      <td className="py-3 px-4 text-och-steel">
                        {inv.contract_id ? (
                          <Link className="text-och-mint hover:underline" href={`/dashboard/institution/contracts/${inv.contract_id}/complete`}>
                            View contract
                          </Link>
                        ) : (
                          '—'
                        )}
                      </td>
                      <td className="py-3 px-4 text-white">{formatMoney(inv.total)}</td>
                      <td className="py-3 px-4 text-xs">
                        <div className="text-white">
                          {inv.payment_status === 'fully_paid'
                            ? 'Fully paid'
                            : inv.payment_status === 'partially_paid'
                              ? 'Partially paid'
                              : 'Not paid'}
                        </div>
                        <div className="text-och-steel">
                          {formatMoney(inv.amount_paid ?? 0)} / {formatMoney(inv.total)}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant={
                            inv.status === 'paid'
                              ? 'mint'
                              : inv.status === 'sent' || inv.status === 'draft'
                                ? 'gold'
                                : 'steel'
                          }
                        >
                          {inv.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        {inv.due_date ? new Date(inv.due_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        {inv.paid_date ? new Date(inv.paid_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        <Link className="text-och-mint hover:underline" href={`/dashboard/institution/contracts/invoices/${inv.id}`}>
                          Details
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
