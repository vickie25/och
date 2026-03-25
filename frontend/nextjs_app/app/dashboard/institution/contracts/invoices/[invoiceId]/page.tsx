'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'

type PaymentMap = {
  id: string
  amount: string | number
  currency: string
  status: string
  payment_method: string
  paystack_reference?: string | null
  created_at: string
  allocated_amount: string | number
  allocation_status: 'fully_allocated' | 'partially_allocated' | 'not_allocated'
}

type InvoiceDetail = {
  id: string
  invoice_number: string
  organization_name?: string | null
  contract_id?: string | null
  total: string | number
  amount_paid?: string | number
  amount_remaining?: string | number
  payment_status?: 'unpaid' | 'partially_paid' | 'fully_paid'
  status: string
  due_date?: string | null
  paid_date?: string | null
  payments_mapped?: PaymentMap[]
}

function formatMoney(v: string | number, currency = 'USD') {
  const n = typeof v === 'string' ? parseFloat(v) : v
  if (Number.isNaN(n)) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 2 }).format(n)
}

export default function InstitutionInvoiceDetailPage() {
  const params = useParams()
  const invoiceId = typeof params.invoiceId === 'string' ? params.invoiceId : ''
  const [invoice, setInvoice] = useState<InvoiceDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!invoiceId) return
    setLoading(true)
    setError(null)
    try {
      const data = await apiGateway.get<InvoiceDetail>(`/finance/invoices/${invoiceId}/`)
      setInvoice(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load invoice')
      setInvoice(null)
    } finally {
      setLoading(false)
    }
  }, [invoiceId])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <Link href="/dashboard/institution/contracts/invoices" className="text-sm font-medium text-och-mint hover:underline">
            ← Invoices
          </Link>
          <h1 className="text-2xl font-bold text-och-gold mt-2">Invoice details</h1>
        </div>

        {loading ? (
          <Card className="p-6 text-och-steel">Loading…</Card>
        ) : error || !invoice ? (
          <Card className="p-6 text-red-300">{error ?? 'Invoice not found'}</Card>
        ) : (
          <>
            <Card className="p-5 border border-och-steel/20">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <p className="text-xs text-och-steel">Invoice #</p>
                  <p className="text-white font-mono">{invoice.invoice_number}</p>
                </div>
                <div>
                  <p className="text-xs text-och-steel">Contract</p>
                  {invoice.contract_id ? (
                    <Link className="text-och-mint hover:underline" href={`/dashboard/institution/contracts/${invoice.contract_id}/complete`}>
                      View full contract
                    </Link>
                  ) : (
                    <p className="text-och-steel">—</p>
                  )}
                </div>
                <div>
                  <p className="text-xs text-och-steel">Invoice status</p>
                  <Badge variant={invoice.status === 'paid' ? 'mint' : 'gold'}>{invoice.status}</Badge>
                </div>
                <div>
                  <p className="text-xs text-och-steel">Payment progress</p>
                  <p className="text-white">
                    {invoice.payment_status === 'fully_paid'
                      ? 'Fully paid'
                      : invoice.payment_status === 'partially_paid'
                        ? 'Partially paid'
                        : 'Not paid'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-och-steel">Paid / total</p>
                  <p className="text-white">
                    {formatMoney(invoice.amount_paid ?? 0)} / {formatMoney(invoice.total)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-och-steel">Remaining</p>
                  <p className="text-white">{formatMoney(invoice.amount_remaining ?? 0)}</p>
                </div>
              </div>
            </Card>

            <Card className="p-0 border border-och-steel/20 overflow-hidden">
              <div className="px-4 py-3 border-b border-och-steel/20 text-white font-semibold text-sm">
                Payments mapped to this invoice
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-och-steel/5 text-xs uppercase tracking-wide text-och-steel">
                    <tr>
                      <th className="py-3 px-4 text-left">Date</th>
                      <th className="py-3 px-4 text-left">Method</th>
                      <th className="py-3 px-4 text-left">Transaction status</th>
                      <th className="py-3 px-4 text-left">Amount</th>
                      <th className="py-3 px-4 text-left">Allocated</th>
                      <th className="py-3 px-4 text-left">Allocation state</th>
                      <th className="py-3 px-4 text-left">Reference</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-och-steel/10">
                    {(invoice.payments_mapped ?? []).length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-och-steel">
                          No payment transactions yet.
                        </td>
                      </tr>
                    ) : (
                      (invoice.payments_mapped ?? []).map((p) => (
                        <tr key={p.id}>
                          <td className="py-3 px-4 text-och-steel">{new Date(p.created_at).toLocaleString()}</td>
                          <td className="py-3 px-4 text-white">{p.payment_method}</td>
                          <td className="py-3 px-4 text-och-steel">{p.status}</td>
                          <td className="py-3 px-4 text-white">{formatMoney(p.amount, p.currency || 'USD')}</td>
                          <td className="py-3 px-4 text-white">{formatMoney(p.allocated_amount, p.currency || 'USD')}</td>
                          <td className="py-3 px-4 text-och-steel">{p.allocation_status.replace('_', ' ')}</td>
                          <td className="py-3 px-4 text-och-steel font-mono text-xs">{p.paystack_reference ?? '—'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
