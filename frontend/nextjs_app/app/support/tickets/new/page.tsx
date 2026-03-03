'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { apiGateway } from '@/services/apiGateway'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

interface ProblemCodeItem {
  id: number
  code: string
  name: string
}

export default function NewSupportTicketPage() {
  const router = useRouter()
  const [problemCodes, setProblemCodes] = useState<ProblemCodeItem[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [form, setForm] = useState({
    subject: '',
    description: '',
    priority: 'medium',
    problem_code: '',
    reporter_email: '',
    reporter_name: '',
  })

  useEffect(() => {
    let cancelled = false
    apiGateway
      .get<ProblemCodeItem[] | { results: ProblemCodeItem[] }>('/support/problem-codes/')
      .then((data) => {
        if (!cancelled) {
          const list = Array.isArray(data) ? data : (data?.results ?? [])
          setProblemCodes(list)
        }
      })
      .catch(() => {
        if (!cancelled) setProblemCodes([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload: Record<string, string> = {
        subject: form.subject.trim(),
        description: form.description.trim(),
        priority: form.priority,
      }
      if (form.problem_code) payload.problem_code = form.problem_code
      if (form.reporter_email) payload.reporter_email = form.reporter_email.trim()
      if (form.reporter_name) payload.reporter_name = form.reporter_name.trim()
      const created = await apiGateway.post<{ id: number }>('/support/tickets/', payload)
      router.push(`/support/tickets/${created.id}`)
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'response' in err
        ? (err as { response?: { data?: { detail?: string; subject?: string[]; description?: string[] } } }).response?.data?.detail
          || (err as { response?: { data?: unknown } }).response?.data
        : 'Failed to create ticket'
      setError(Array.isArray(message) ? message.join(' ') : String(message))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <RouteGuard requiredRoles={['support']}>
      <div className="w-full max-w-3xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
        <div className="mb-6">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/support/tickets" className="flex items-center gap-2 text-och-steel hover:text-white">
              <ArrowLeft className="w-4 h-4" aria-hidden />
              Back to tickets
            </Link>
          </Button>
        </div>

        <Card className="bg-slate-800/50 border-slate-700">
          <div className="p-6 border-b border-och-steel/20">
            <h1 className="text-2xl font-bold text-white">New ticket</h1>
            <p className="text-och-steel text-sm mt-1">Create a support ticket.</p>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="p-3 bg-och-orange/10 border border-och-orange/30 rounded-lg text-och-orange text-sm">
                {error}
              </div>
            )}
            <div>
              <label htmlFor="subject" className="block text-sm font-medium text-white mb-1">Subject *</label>
              <input
                id="subject"
                type="text"
                required
                value={form.subject}
                onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                placeholder="Brief description"
              />
            </div>
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-white mb-1">Description *</label>
              <textarea
                id="description"
                required
                rows={5}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender resize-y"
                placeholder="Details of the issue"
              />
            </div>
            <div>
              <label htmlFor="priority" className="block text-sm font-medium text-white mb-1">Priority</label>
              <select
                id="priority"
                value={form.priority}
                onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <label htmlFor="problem_code" className="block text-sm font-medium text-white mb-1">Problem code</label>
              <select
                id="problem_code"
                value={form.problem_code}
                onChange={(e) => setForm((f) => ({ ...f, problem_code: e.target.value }))}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
              >
                <option value="">Select code</option>
                {loading ? (
                  <option disabled>Loading…</option>
                ) : (
                  problemCodes.map((pc) => (
                    <option key={pc.id} value={pc.code}>{pc.code} – {pc.name}</option>
                  ))
                )}
              </select>
            </div>
            <div>
              <label htmlFor="reporter_name" className="block text-sm font-medium text-white mb-1">Reporter name (optional)</label>
              <input
                id="reporter_name"
                type="text"
                value={form.reporter_name}
                onChange={(e) => setForm((f) => ({ ...f, reporter_name: e.target.value }))}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                placeholder="Customer name"
              />
            </div>
            <div>
              <label htmlFor="reporter_email" className="block text-sm font-medium text-white mb-1">Reporter email (optional)</label>
              <input
                id="reporter_email"
                type="email"
                value={form.reporter_email}
                onChange={(e) => setForm((f) => ({ ...f, reporter_email: e.target.value }))}
                className="w-full px-4 py-2 bg-och-midnight border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                placeholder="customer@example.com"
              />
            </div>
            <div className="flex gap-3 pt-2">
              <Button type="submit" disabled={submitting}>
                {submitting ? 'Creating…' : 'Create ticket'}
              </Button>
              <Button type="button" variant="outline" asChild>
                <Link href="/support/tickets">Cancel</Link>
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </RouteGuard>
  )
}
