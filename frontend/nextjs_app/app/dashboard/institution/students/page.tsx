'use client'

import Link from 'next/link'
import { StudentManagement } from '@/app/dashboard/director/institutional-billing/components/student-management'

export default function InstitutionStudentsPage() {
  return (
    <div className="min-h-screen bg-och-midnight p-4 sm:p-6">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link href="/dashboard/institution" className="text-sm text-och-mint hover:underline">
              ← Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-och-gold mt-2">Students</h1>
            <p className="text-sm text-och-steel mt-1 max-w-2xl">
              Enroll and manage learners under your institution&apos;s active operational contracts. Licensing tier is
              set on your{' '}
              <Link href="/dashboard/institution/contracts" className="text-och-mint hover:underline">
                finance contract
              </Link>
              ; all students inherit that tier once provisioned.
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-och-steel/25 bg-och-steel/5 px-4 py-3 text-sm text-och-steel">
          If no students or contracts appear here, your director may still be linking the legacy institutional billing
          record to this organization — contact OCH operations if enrollment stays unavailable after your finance
          contract is active.
        </div>

        <StudentManagement />
      </div>
    </div>
  )
}
