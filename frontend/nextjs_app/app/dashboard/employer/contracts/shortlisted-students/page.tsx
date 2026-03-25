'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { marketplaceClient, type JobApplication } from '@/services/marketplaceClient'

export default function ShortlistedStudentsPage() {
  const [applications, setApplications] = useState<JobApplication[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        setLoading(true)
        setError(null)
        const res = await marketplaceClient.getAllApplications()
        const list = Array.isArray(res?.results) ? res.results : []
        if (!cancelled) {
          const placed = list.filter(
            (a) => a.status === 'accepted' || a.status === 'interview' || a.status === 'shortlisted'
          )
          setApplications(placed)
        }
      } catch (e: unknown) {
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : 'Could not load applications'
          setError(msg)
          setApplications([])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-screen bg-och-midnight p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <Link
            href="/dashboard/employer/contracts"
            className="text-sm font-medium text-och-mint hover:text-och-mint/80 mb-2 inline-block"
          >
            ← Contracts
          </Link>
          <h1 className="text-2xl font-bold text-och-gold">Shortlisted students</h1>
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
                  <th className="py-3 px-4 text-left">Candidate</th>
                  <th className="py-3 px-4 text-left">Role</th>
                  <th className="py-3 px-4 text-left">Status</th>
                  <th className="py-3 px-4 text-left">Match</th>
                  <th className="py-3 px-4 text-left">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-och-steel/15">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-10 px-4 text-center text-och-steel">
                      Loading…
                    </td>
                  </tr>
                ) : applications.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-10 px-4 text-center text-och-steel">
                      No entries yet. Use{' '}
                      <Link href="/dashboard/employer/jobs" className="text-och-mint hover:underline">
                        Jobs
                      </Link>{' '}
                      and{' '}
                      <Link href="/dashboard/employer/marketplace" className="text-och-mint hover:underline">
                        Marketplace
                      </Link>
                      .
                    </td>
                  </tr>
                ) : (
                  applications.map((a) => (
                    <tr key={a.id} className="hover:bg-och-steel/10">
                      <td className="py-3 px-4 text-white">
                        {a.applicant_name || a.applicant_email || '—'}
                      </td>
                      <td className="py-3 px-4 text-och-steel">{a.job_posting?.title ?? '—'}</td>
                      <td className="py-3 px-4">
                        <Badge variant="gold">{a.status.replace('_', ' ')}</Badge>
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        {a.match_score != null ? `${Number(a.match_score).toFixed(0)}%` : '—'}
                      </td>
                      <td className="py-3 px-4 text-och-steel">
                        {a.updated_at ? new Date(a.updated_at).toLocaleDateString() : '—'}
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
