'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { apiGateway } from '@/services/apiGateway'
import { ArrowLeft, Send, Mail, LogIn, Lock } from 'lucide-react'
import Link from 'next/link'

interface TicketResponse {
  id: number
  message: string
  is_staff: boolean
  created_by_name: string
  created_at: string
}

interface AuditLogEntry {
  id: number
  action: string
  actor_identifier: string
  resource_type: string
  resource_id: string | null
  result: string
  timestamp: string
  metadata?: { impersonation?: boolean; by_email?: string; by_name?: string }
}

interface TicketDetail {
  id: number
  subject: string
  description: string
  status: string
  priority: string
  problem_code: number | null
  problem_code_detail: { code: string; name: string } | null
  reporter_id: number | null
  reporter_email: string
  reporter_name: string
  assigned_to: number | null
  assigned_to_email: string | null
  resolution_notes: string
  resolved_at: string | null
  internal_notes: string
  created_at: string
  updated_at: string
  created_by: number | null
  responses?: TicketResponse[]
}

const STATUS_VARIANT: Record<string, 'mint' | 'orange' | 'gold' | 'steel' | 'defender'> = {
  open: 'orange',
  in_progress: 'defender',
  pending_customer: 'gold',
  resolved: 'mint',
  closed: 'steel',
}

const PRIORITY_VARIANT: Record<string, 'orange' | 'gold' | 'steel'> = {
  urgent: 'orange',
  high: 'orange',
  medium: 'gold',
  low: 'steel',
}

export default function SupportTicketDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params?.id as string
  const [ticket, setTicket] = useState<TicketDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [replyMessage, setReplyMessage] = useState('')
  const [sendCopyToEmail, setSendCopyToEmail] = useState(false)
  const [submittingReply, setSubmittingReply] = useState(false)
  const [userLogs, setUserLogs] = useState<AuditLogEntry[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [impersonating, setImpersonating] = useState(false)
  const [closeNotes, setCloseNotes] = useState('')
  const [closing, setClosing] = useState(false)

  const loadTicket = () => {
    if (!id) return
    apiGateway.get<TicketDetail>(`/support/tickets/${id}/`).then(setTicket).catch(() => setTicket(null))
  }

  useEffect(() => {
    if (!id) return
    let cancelled = false
    apiGateway
      .get<TicketDetail>(`/support/tickets/${id}/`)
      .then((data) => {
        if (!cancelled) setTicket(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response?.status === 404 ? 'Ticket not found.' : err?.message || 'Failed to load ticket')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [id])

  useEffect(() => {
    if (!ticket?.reporter_id) return
    setLogsLoading(true)
    apiGateway
      .get<AuditLogEntry[] | { results: AuditLogEntry[] }>(`/audit-logs/?user_id=${ticket.reporter_id}`)
      .then((data) => {
        const list = Array.isArray(data) ? data : (data?.results ?? [])
        setUserLogs(list)
      })
      .catch(() => setUserLogs([]))
      .finally(() => setLogsLoading(false))
  }, [ticket?.reporter_id])

  const handleCloseCase = async () => {
    if (!id || !ticket) return
    const notes = closeNotes.trim() || undefined
    if (!window.confirm('Close this ticket? This will set status to Closed.' + (notes ? ' Resolution notes will be saved.' : ''))) return
    setClosing(true)
    try {
      await apiGateway.patch(`/support/tickets/${id}/`, {
        status: 'closed',
        ...(notes && { resolution_notes: notes }),
      })
      loadTicket()
      setCloseNotes('')
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as Error)?.message
      setError(msg ? String(msg) : 'Failed to close ticket.')
    } finally {
      setClosing(false)
    }
  }

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!replyMessage.trim() || !id) return
    setSubmittingReply(true)
    try {
      await apiGateway.post(`/support/tickets/${id}/responses/`, {
        message: replyMessage.trim(),
        send_copy_to_email: sendCopyToEmail,
      })
      setReplyMessage('')
      loadTicket()
    } finally {
      setSubmittingReply(false)
    }
  }

  const handleImpersonate = async () => {
    if (!ticket?.reporter_id) return
    setImpersonating(true)
    setError(null)
    try {
      const res = await apiGateway.post<{
        access_token: string
        refresh_token: string
        user?: unknown
        impersonation_expires_at?: string
        impersonation_code?: string
      }>(`/support/impersonate/${ticket.reporter_id}/`)
      const code = res.impersonation_code
      const url = code
        ? `/auth/impersonate?code=${encodeURIComponent(code)}`
        : '/auth/impersonate'
      const win = window.open(url, 'impersonate', 'width=500,height=400')
      if (!win) {
        setError('Popup was blocked. Please allow popups for this site and try again.')
      }
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as Error)?.message
      setError(msg ? String(msg) : 'Impersonation failed.')
    } finally {
      setImpersonating(false)
    }
  }

  if (loading) {
    return (
      <RouteGuard requiredRoles={['support']}>
        <div className="w-full max-w-7xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
          <div className="animate-pulse text-och-steel">Loading ticket...</div>
        </div>
      </RouteGuard>
    )
  }

  if (error || !ticket) {
    return (
      <RouteGuard requiredRoles={['support']}>
        <div className="w-full max-w-7xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
          <div className="mb-4 p-4 bg-och-orange/10 border border-och-orange/30 rounded-lg text-och-orange">
            {error || 'Ticket not found.'}
          </div>
          <Button variant="outline" asChild>
            <Link href="/support/tickets">
              <ArrowLeft className="w-4 h-4 mr-2" aria-hidden />
              Back to tickets
            </Link>
          </Button>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard requiredRoles={['support']}>
      <div className="w-full max-w-7xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/support/tickets" className="flex items-center gap-2 text-och-steel hover:text-white">
              <ArrowLeft className="w-4 h-4" aria-hidden />
              Back to tickets
            </Link>
          </Button>
        </div>

        <Card className="bg-slate-800/50 border-slate-700 overflow-hidden">
          <div className="p-6 border-b border-och-steel/20">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-white mb-2">{ticket.subject}</h1>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={STATUS_VARIANT[ticket.status] ?? 'steel'}>
                    {ticket.status.replace(/_/g, ' ')}
                  </Badge>
                  <Badge variant={PRIORITY_VARIANT[ticket.priority] ?? 'steel'}>{ticket.priority}</Badge>
                  {ticket.problem_code_detail && (
                    <span className="text-och-steel text-sm">
                      {ticket.problem_code_detail.code} – {ticket.problem_code_detail.name}
                    </span>
                  )}
                </div>
              </div>
              <div className="text-sm text-och-steel">
                <div>#{ticket.id}</div>
                <div>Created {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '—'}</div>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-6">
            <section>
              <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Reporter</h2>
              <p className="text-white">
                {ticket.reporter_name || ticket.reporter_email || '—'}
                {ticket.reporter_email && (
                  <span className="text-och-steel ml-2">({ticket.reporter_email})</span>
                )}
              </p>
              {ticket.reporter_id && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={handleImpersonate}
                  disabled={impersonating}
                >
                  <LogIn className="w-4 h-4 mr-2" aria-hidden />
                  {impersonating ? 'Opening…' : 'Log in as this user'}
                </Button>
              )}
            </section>

            {ticket.assigned_to_email && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Assigned to</h2>
                <p className="text-white">{ticket.assigned_to_email}</p>
              </section>
            )}

            <section>
              <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Description</h2>
              <p className="text-white whitespace-pre-wrap">{ticket.description}</p>
            </section>

            {Array.isArray(ticket.responses) && ticket.responses.length > 0 && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Conversation</h2>
                <div className="space-y-3">
                  {ticket.responses.map((r) => (
                    <div
                      key={r.id}
                      className={`p-4 rounded-lg ${r.is_staff ? 'bg-och-defender/10 border border-och-defender/30' : 'bg-och-midnight/50'}`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-white text-sm">{r.created_by_name || (r.is_staff ? 'Support' : 'Customer')}</span>
                        {r.is_staff && <Badge variant="defender" className="text-xs">Support</Badge>}
                        <span className="text-och-steel text-xs ml-auto">{new Date(r.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-white text-sm whitespace-pre-wrap">{r.message}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {!['closed', 'resolved'].includes(ticket.status) && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Close case</h2>
                <p className="text-och-steel text-sm mb-2">Optionally add resolution notes, then close the ticket.</p>
                <textarea
                  value={closeNotes}
                  onChange={(e) => setCloseNotes(e.target.value)}
                  placeholder="Resolution notes (optional)"
                  className="w-full px-4 py-3 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender resize-none mb-2"
                  rows={2}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleCloseCase}
                  disabled={closing}
                  className="border-och-steel/40 text-och-steel hover:bg-och-midnight"
                >
                  <Lock className="w-4 h-4 mr-2" aria-hidden />
                  {closing ? 'Closing…' : 'Close case'}
                </Button>
              </section>
            )}

            {ticket.status !== 'closed' && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Reply</h2>
                <form onSubmit={handleReply} className="space-y-3">
                  <textarea
                    value={replyMessage}
                    onChange={(e) => setReplyMessage(e.target.value)}
                    placeholder="Type your reply..."
                    className="w-full px-4 py-3 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender resize-none"
                    rows={3}
                  />
                  <label className="flex items-center gap-2 text-och-steel text-sm cursor-pointer">
                    <input
                      type="checkbox"
                      checked={sendCopyToEmail}
                      onChange={(e) => setSendCopyToEmail(e.target.checked)}
                      className="rounded border-och-steel/30"
                    />
                    <Mail className="w-4 h-4" aria-hidden />
                    Send copy to reporter by email
                  </label>
                  <Button type="submit" size="sm" disabled={submittingReply || !replyMessage.trim()}>
                    <Send className="w-4 h-4 mr-2" aria-hidden />
                    {submittingReply ? 'Sending…' : 'Send reply'}
                  </Button>
                </form>
              </section>
            )}

            {ticket.reporter_id && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">User activity (reporter)</h2>
                {logsLoading ? (
                  <p className="text-och-steel text-sm">Loading activity…</p>
                ) : userLogs.length === 0 ? (
                  <p className="text-och-steel text-sm">No recent activity.</p>
                ) : (
                  <ul className="space-y-2 max-h-48 overflow-y-auto">
                    {userLogs.slice(0, 20).map((log) => (
                      <li key={log.id} className="text-sm flex flex-wrap gap-2 items-center">
                        <span className="text-och-steel">{new Date(log.timestamp).toLocaleString()}</span>
                        <Badge variant={log.result === 'success' ? 'mint' : 'orange'} className="text-xs">{log.action}</Badge>
                        {log.metadata?.impersonation && (
                          <span className="text-och-orange text-xs">
                            Support login by {log.metadata.by_name || log.metadata.by_email || log.actor_identifier}
                          </span>
                        )}
                        {!log.metadata?.impersonation && <span className="text-white">{log.actor_identifier}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )}

            {ticket.internal_notes && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Internal notes</h2>
                <p className="text-white whitespace-pre-wrap">{ticket.internal_notes}</p>
              </section>
            )}

            {(ticket.resolved_at || ticket.resolution_notes) && (
              <section>
                <h2 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Resolution</h2>
                {ticket.resolved_at && (
                  <p className="text-och-steel text-sm mb-2">
                    Resolved {new Date(ticket.resolved_at).toLocaleString()}
                  </p>
                )}
                {ticket.resolution_notes && (
                  <p className="text-white whitespace-pre-wrap">{ticket.resolution_notes}</p>
                )}
              </section>
            )}

            <section className="text-sm text-och-steel">
              <p>Last updated: {ticket.updated_at ? new Date(ticket.updated_at).toLocaleString() : '—'}</p>
            </section>
          </div>
        </Card>
      </div>
    </RouteGuard>
  )
}
