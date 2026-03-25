'use client'

import Link from 'next/link'
import { CommercialTermsPrintDocument } from '@/components/employer/CommercialTermsPrintDocument'
import { Printer } from 'lucide-react'

export default function EmployerCommercialTermsPage() {
  return (
    <div className="min-h-screen bg-och-midnight print:bg-white print:p-8">
      <div className="max-w-3xl mx-auto p-6 print:max-w-none print:p-0">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 print:hidden">
          <Link href="/dashboard/employer/contracts" className="text-sm font-medium text-och-mint hover:underline">
            ← Contracts
          </Link>
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-lg bg-och-gold px-4 py-2 text-xs font-semibold text-och-midnight hover:bg-och-gold/90"
          >
            <Printer className="h-4 w-4" />
            Print / save as PDF
          </button>
        </div>
        <p className="text-xs text-och-steel mb-6 print:hidden">
          Use your browser print dialog and choose &quot;Save as PDF&quot; to download this reference.
        </p>
        <CommercialTermsPrintDocument />
      </div>
    </div>
  )
}
