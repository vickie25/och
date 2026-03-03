'use client'

import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { CardContent } from '@/components/ui/card-enhanced'
import { Badge } from '@/components/ui/Badge'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { apiGateway } from '@/services/apiGateway'
import { Hash } from 'lucide-react'

interface ProblemCodeItem {
  id: number
  code: string
  name: string
  description: string
  category: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const CATEGORY_LABELS: Record<string, string> = {
  auth: 'Authentication & Access',
  billing: 'Billing & Payments',
  curriculum: 'Curriculum & Learning',
  mentorship: 'Mentorship',
  technical: 'Technical / Bug',
  account: 'Account & Profile',
  platform: 'Platform General',
  other: 'Other',
}

export default function SupportProblemCodesPage() {
  const [codes, setCodes] = useState<ProblemCodeItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    apiGateway
      .get<ProblemCodeItem[] | { results: ProblemCodeItem[] }>('/support/problem-codes/')
      .then((data) => {
        if (!cancelled) {
          const list = Array.isArray(data) ? data : (data?.results ?? [])
          setCodes(list)
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err?.message || 'Failed to load problem codes')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) {
    return (
      <RouteGuard requiredRoles={['support']}>
        <div className="w-full max-w-7xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
          <div className="animate-pulse text-och-steel">Loading problem codes...</div>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard requiredRoles={['support']}>
      <div className="w-full max-w-7xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">Problem codes</h1>
          <p className="text-sm text-slate-400">
            Use these codes when creating or updating tickets for reporting and SLA tracking.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-och-orange/10 border border-och-orange/30 rounded-lg text-och-orange">
            {error}
          </div>
        )}

        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="p-6">
            {codes.length === 0 ? (
              <div className="py-8 text-center text-och-steel">
                <Hash className="w-12 h-12 mx-auto mb-3 opacity-50" aria-hidden />
                <p>No problem codes defined yet.</p>
                <p className="text-sm mt-1">Directors or admins can add codes via the backend or seed data.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-och-steel/20">
                      <th className="text-left p-3 text-och-steel text-sm font-semibold">Code</th>
                      <th className="text-left p-3 text-och-steel text-sm font-semibold">Name</th>
                      <th className="text-left p-3 text-och-steel text-sm font-semibold">Category</th>
                      <th className="text-left p-3 text-och-steel text-sm font-semibold">Description</th>
                      <th className="text-left p-3 text-och-steel text-sm font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {codes.map((c) => (
                      <tr key={c.id} className="border-b border-och-steel/10 hover:bg-och-midnight/50">
                        <td className="p-3 font-mono text-och-defender font-medium">{c.code}</td>
                        <td className="p-3 text-white">{c.name}</td>
                        <td className="p-3 text-och-steel text-sm">
                          {CATEGORY_LABELS[c.category] ?? c.category}
                        </td>
                        <td className="p-3 text-slate-400 text-sm max-w-xs truncate">
                          {c.description || '—'}
                        </td>
                        <td className="p-3">
                          <Badge variant={c.is_active ? 'mint' : 'steel'}>
                            {c.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </RouteGuard>
  )
}
