'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { Button } from '@/components/ui/Button'

const API_BASE = process.env.NEXT_PUBLIC_DJANGO_API_URL;

export default function PayInvoicePage() {
  const params = useParams()
  const id = params?.id as string
  const [invoice, setInvoice] = useState<{
    id: string
    organization_name: string
    contact_person_name: string
    invoice_number: string
    line_items: Array<{ student_name?: string; plan_name?: string; amount_kes: number }>
    total_amount_kes: number
    currency: string
    status: string
    payment_link: string | null
    created_at: string | null
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    fetch(`${API_BASE}/api/v1/billing/org-enrollment-invoices/${id}/`, {
      credentials: 'omit',
    })
      .then((res) => {
        if (!res.ok) throw new Error('Invoice not found')
        return res.json()
      })
      .then((data) => {
        setInvoice(data)
        setError(null)
      })
      .catch((e) => {
        setError(e.message || 'Failed to load invoice')
        setInvoice(null)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <p className="text-slate-400">Loading invoice…</p>
      </div>
    )
  }

  if (error || !invoice) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="text-center text-red-400">
          <p>{error || 'Invoice not found'}</p>
        </div>
      </div>
    )
  }

  if (invoice.status === 'paid') {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full rounded-lg border border-slate-700 bg-slate-900/50 p-6 text-center">
          <h1 className="text-xl font-semibold text-white mb-2">Invoice already paid</h1>
          <p className="text-slate-400">This invoice has been settled. Thank you.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full rounded-lg border border-slate-700 bg-slate-900/50 p-6">
        <h1 className="text-xl font-semibold text-white mb-1">Invoice {invoice.invoice_number || invoice.id}</h1>
        <p className="text-slate-400 text-sm mb-4">{invoice.organization_name}</p>
        <ul className="space-y-2 mb-4 text-sm">
          {invoice.line_items?.map((item, i) => (
            <li key={i} className="flex justify-between text-slate-300">
              <span>{item.student_name || '—'} {item.plan_name ? `(${item.plan_name})` : ''}</span>
              <span>{invoice.currency} {(item.amount_kes || 0).toLocaleString()}</span>
            </li>
          ))}
        </ul>
        <div className="flex justify-between font-semibold text-white border-t border-slate-700 pt-4 mb-6">
          <span>Total</span>
          <span>{invoice.currency} {(invoice.total_amount_kes || 0).toLocaleString()}</span>
        </div>
        {invoice.payment_link ? (
          <Button
            variant="defender"
            className="w-full"
            onClick={() => window.location.href = invoice.payment_link!}
          >
            Pay with Paystack
          </Button>
        ) : (
          <p className="text-slate-400 text-sm">Payment link is not available. Please contact support.</p>
        )}
      </div>
    </div>
  )
}
