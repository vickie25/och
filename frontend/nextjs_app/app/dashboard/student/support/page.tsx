'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Input } from '@/components/ui/Input'
import { apiGateway } from '@/services/apiGateway'
import { LifeBuoy, Plus, X, Eye, Trash2, Paperclip } from 'lucide-react'
import toast from 'react-hot-toast'

interface TicketAttachment {
  id: number
  file_name: string
  file_path: string
  file_size: number | null
  mime_type: string
  created_at: string
}

interface TicketResponse {
  id: number
  message: string
  is_staff: boolean
  created_at: string
  created_by_name: string
}

interface TicketDetail {
  id: number
  subject: string
  description: string
  status: string
  priority: string
  problem_code: number | null
  problem_code_detail: { code: string; name: string } | null
  reporter_email: string
  reporter_name: string
  resolution_notes: string
  resolved_at: string | null
  created_at: string
  updated_at: string
  responses?: TicketResponse[]
  attachments?: TicketAttachment[]
}

interface TicketRow {
  id: number
  subject: string
  status: string
  priority: string
  problem_code: string
  problem_code_display: string | null
  created_at: string
  updated_at: string
}

export default function StudentSupportPage() {
  const [tickets, setTickets] = useState<TicketRow[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [viewTicket, setViewTicket] = useState<TicketDetail | null>(null)
  const [deleteId, setDeleteId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const [newTicket, setNewTicket] = useState({
    subject: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    problem_code: '',
    attachments: [] as File[],
  })

  const problemCodes = [
    { code: 'AUTH-001', name: 'Login / Access Issue' },
    { code: 'BILL-001', name: 'Billing or Payment' },
    { code: 'CURR-001', name: 'Curriculum or Content' },
    { code: 'MENT-001', name: 'Mentorship' },
    { code: 'TECH-001', name: 'Technical / Bug' },
    { code: 'ACCT-001', name: 'Account or Profile' },
    { code: 'PLAT-001', name: 'Platform General' },
  ]

  useEffect(() => {
    loadTickets()
  }, [])

  const loadTickets = async () => {
    setIsLoading(true)
    try {
      const data = await apiGateway.get<TicketRow[] | { results: TicketRow[] }>('/support/tickets/my-tickets/')
      setTickets(Array.isArray(data) ? data : data?.results || [])
    } catch (err) {
      toast.error('Failed to load tickets')
    } finally {
      setIsLoading(false)
    }
  }

  const openViewModal = async (id: number) => {
    try {
      const data = await apiGateway.get<TicketDetail>(`/support/tickets/${id}/`)
      setViewTicket(data)
    } catch {
      toast.error('Failed to load ticket details')
    }
  }

  const closeViewModal = () => setViewTicket(null)

  const handleDelete = async (id: number) => {
    if (!deleteId || deleteId !== id) return
    setIsSubmitting(true)
    try {
      await apiGateway.delete(`/support/tickets/${id}/`)
      toast.success('Ticket deleted')
      setDeleteId(null)
      closeViewModal()
      loadTickets()
    } catch (err: unknown) {
      toast.error((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to delete ticket')
    } finally {
      setIsSubmitting(false)
    }
  }

  const confirmDelete = (id: number) => {
    if (window.confirm('Are you sure you want to delete this ticket? This cannot be undone.')) {
      setDeleteId(id)
      handleDelete(id)
    }
  }

  const createTicket = async () => {
    if (!newTicket.subject || !newTicket.description) {
      toast.error('Subject and description are required')
      return
    }
    setIsSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('subject', newTicket.subject)
      formData.append('description', newTicket.description)
      formData.append('priority', newTicket.priority)
      if (newTicket.problem_code) formData.append('problem_code', newTicket.problem_code)
      newTicket.attachments.forEach((file, idx) => {
        formData.append(`attachment_${idx}`, file)
      })
      await apiGateway.post('/support/tickets/', formData)
      toast.success('Support ticket created successfully')
      setShowCreateModal(false)
      setNewTicket({ subject: '', description: '', priority: 'medium', problem_code: '', attachments: [] })
      loadTickets()
    } catch (err: unknown) {
      toast.error((err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Failed to create ticket')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'orange'
      case 'in_progress': return 'defender'
      case 'resolved': return 'mint'
      case 'closed': return 'outline'
      default: return 'outline'
    }
  }

  const formatBytes = (n: number | null) => {
    if (n == null) return '—'
    if (n < 1024) return `${n} B`
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
    return `${(n / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-bold text-och-defender flex items-center gap-3">
            <LifeBuoy className="w-10 h-10" />
            Support Center
          </h1>
          <p className="text-och-steel mt-2">View and manage your support tickets</p>
        </div>
        <Button variant="defender" onClick={() => setShowCreateModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Ticket
        </Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-och-steel/20">
                <th className="text-left p-3 text-och-steel text-sm font-semibold">#</th>
                <th className="text-left p-3 text-och-steel text-sm font-semibold">Subject</th>
                <th className="text-left p-3 text-och-steel text-sm font-semibold">Status</th>
                <th className="text-left p-3 text-och-steel text-sm font-semibold">Priority</th>
                <th className="text-left p-3 text-och-steel text-sm font-semibold">Category</th>
                <th className="text-left p-3 text-och-steel text-sm font-semibold">Created</th>
                <th className="text-left p-3 text-och-steel text-sm font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-och-steel">Loading...</td>
                </tr>
              ) : tickets.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-och-steel">No tickets yet</td>
                </tr>
              ) : (
                tickets.map((t) => (
                  <tr key={t.id} className="border-b border-och-steel/10 hover:bg-och-midnight/50">
                    <td className="p-3 text-white font-mono text-sm">#{t.id}</td>
                    <td className="p-3 text-white font-medium max-w-xs truncate">{t.subject}</td>
                    <td className="p-3">
                      <Badge variant={getStatusColor(t.status) as 'orange' | 'defender' | 'mint' | 'outline'}>{t.status.replace(/_/g, ' ')}</Badge>
                    </td>
                    <td className="p-3 text-och-steel text-sm">{t.priority}</td>
                    <td className="p-3 text-och-steel text-sm">{t.problem_code_display || '—'}</td>
                    <td className="p-3 text-och-steel text-sm">{new Date(t.created_at).toLocaleDateString()}</td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={() => openViewModal(t.id)}>
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        <Button variant="outline" size="sm" onClick={() => confirmDelete(t.id)} disabled={isSubmitting}>
                          <Trash2 className="w-4 h-4 mr-1" />
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* View modal – full case details */}
      {viewTicket && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={closeViewModal}>
          <div
            className="bg-och-midnight border border-och-steel/20 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-6 border-b border-och-steel/20 shrink-0">
              <h2 className="text-xl font-bold text-white">Ticket #{viewTicket.id} – {viewTicket.subject}</h2>
              <button onClick={closeViewModal} className="text-och-steel hover:text-white p-1">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto space-y-6">
              <div className="flex flex-wrap gap-2">
                <Badge variant={getStatusColor(viewTicket.status) as 'orange' | 'defender' | 'mint' | 'outline'}>{viewTicket.status.replace(/_/g, ' ')}</Badge>
                <span className="text-och-steel text-sm">Priority: {viewTicket.priority}</span>
                {viewTicket.problem_code_detail && (
                  <span className="text-och-steel text-sm">{viewTicket.problem_code_detail.code} – {viewTicket.problem_code_detail.name}</span>
                )}
              </div>
              <div>
                <h3 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-1">Description</h3>
                <p className="text-white whitespace-pre-wrap">{viewTicket.description}</p>
              </div>
              <div className="text-och-steel text-sm">
                Created {new Date(viewTicket.created_at).toLocaleString()}
                {viewTicket.updated_at && ` · Updated ${new Date(viewTicket.updated_at).toLocaleString()}`}
              </div>
              {viewTicket.resolved_at && (
                <div>
                  <h3 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-1">Resolution</h3>
                  <p className="text-white text-sm">{new Date(viewTicket.resolved_at).toLocaleString()}</p>
                  {viewTicket.resolution_notes && <p className="text-white whitespace-pre-wrap mt-1">{viewTicket.resolution_notes}</p>}
                </div>
              )}
              {Array.isArray(viewTicket.responses) && viewTicket.responses.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2">Conversation</h3>
                  <div className="space-y-3">
                    {viewTicket.responses.map((r) => (
                      <div
                        key={r.id}
                        className={`p-4 rounded-lg ${r.is_staff ? 'bg-och-defender/10 border border-och-defender/30' : 'bg-och-midnight/80'}`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white text-sm">{r.created_by_name || (r.is_staff ? 'Support' : 'You')}</span>
                          {r.is_staff && <Badge variant="defender" className="text-xs">Support</Badge>}
                          <span className="text-och-steel text-xs ml-auto">{new Date(r.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-white text-sm whitespace-pre-wrap">{r.message}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {Array.isArray(viewTicket.attachments) && viewTicket.attachments.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-och-steel uppercase tracking-wide mb-2 flex items-center gap-2">
                    <Paperclip className="w-4 h-4" />
                    Attachments
                  </h3>
                  <ul className="space-y-2">
                    {viewTicket.attachments.map((a) => (
                      <li key={a.id} className="flex items-center gap-2 text-sm text-white">
                        <Paperclip className="w-4 h-4 text-och-steel shrink-0" />
                        <span>{a.file_name}</span>
                        <span className="text-och-steel">({formatBytes(a.file_size)})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create ticket modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Create Support Ticket</h2>
                <button onClick={() => setShowCreateModal(false)} className="text-och-steel hover:text-white">
                  <X className="w-6 h-6" />
                </button>
              </div>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Subject *</label>
                  <Input
                    value={newTicket.subject}
                    onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
                    placeholder="Brief description of your issue"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Category</label>
                  <select
                    value={newTicket.problem_code}
                    onChange={(e) => setNewTicket({ ...newTicket, problem_code: e.target.value })}
                    className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                  >
                    <option value="">Select category</option>
                    {problemCodes.map((code) => (
                      <option key={code.code} value={code.code}>{code.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Priority</label>
                  <select
                    value={newTicket.priority}
                    onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value as 'low' | 'medium' | 'high' | 'critical' })}
                    className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Description *</label>
                  <textarea
                    value={newTicket.description}
                    onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                    placeholder="Provide detailed information about your issue..."
                    className="w-full px-4 py-3 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender resize-none"
                    rows={5}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-white mb-2">Attachments</label>
                  <input
                    type="file"
                    multiple
                    onChange={(e) => setNewTicket({ ...newTicket, attachments: Array.from(e.target.files || []) })}
                    className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-och-defender file:text-white hover:file:bg-och-defender/80"
                  />
                  {newTicket.attachments.length > 0 && (
                    <p className="text-xs text-och-mint mt-2">{newTicket.attachments.length} file(s) selected</p>
                  )}
                </div>
                <div className="flex gap-2 pt-4">
                  <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
                  <Button variant="defender" onClick={createTicket} disabled={isSubmitting}>
                    {isSubmitting ? 'Creating...' : 'Create Ticket'}
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}
