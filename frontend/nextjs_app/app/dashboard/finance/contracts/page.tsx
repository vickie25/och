/**
 * Contract Management Page
 * Manage institution and employer contracts
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { FinanceNavigation } from '@/components/navigation/FinanceNavigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { ApiError } from '@/utils/fetcher'
import { Menu, MenuItem, IconButton } from '@mui/material'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import toast from 'react-hot-toast'
import { 
  FileText, 
  Plus,
  Calendar,
  DollarSign,
  Building2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users
} from 'lucide-react'

type Contract = {
  id: string
  organization?: number
  organization_name: string
  type: 'institution' | 'employer'
  start_date: string
  end_date: string
  status:
    | 'proposal'
    | 'negotiation'
    | 'signed'
    | 'pending_payments'
    | 'active'
    | 'renewal'
    | 'terminated'
  total_value: number
  payment_terms: string
  auto_renew: boolean
  renewal_notice_days: number
  seat_cap: number
  seats_used?: number
  is_active: boolean
  email_sent?: boolean
  days_until_expiry: number
  created_at: string
  updated_at: string
}

type OrgOption = {
  id: number
  name: string
  org_type?: string
  enrollment_status?: 'active' | 'pending_contract_creation' | 'pending_invoice_payment'
  enrollment_status_label?: string
}

type TabType = 'all' | 'active' | 'expiring' | 'proposals'

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [activeTab, setActiveTab] = useState<TabType>('all')
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [organizations, setOrganizations] = useState<OrgOption[]>([])
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createForm, setCreateForm] = useState({
    organizationId: '' as string,
    type: 'institution' as 'institution' | 'employer',
    start_date: '',
    end_date: '',
    seat_cap: 50,
    auto_renew: false,
    renewal_notice_days: 60,
  })
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null)
  const [actionMenuContractId, setActionMenuContractId] = useState<string | null>(null)
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null)
  const [showViewModal, setShowViewModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showInviteTemplateModal, setShowInviteTemplateModal] = useState(false)
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({
    type: 'institution' as 'institution' | 'employer',
    start_date: '',
    end_date: '',
    seat_cap: 50,
    auto_renew: false,
    renewal_notice_days: 60,
  })

  useEffect(() => {
    loadContracts()
  }, [])

  useEffect(() => {
    if (!showCreateModal) return
    const loadOrgs = async () => {
      try {
        const res = await apiGateway.get('/orgs/') as any
        const list = Array.isArray(res) ? res : res?.results || res?.data || []
        setOrganizations(
          list.map((o: {
            id: number
            name: string
            org_type?: string
            enrollment_status?: OrgOption['enrollment_status']
            enrollment_status_label?: string
          }) => ({
            id: o.id,
            name: o.name,
            org_type: o.org_type,
            enrollment_status: o.enrollment_status,
            enrollment_status_label: o.enrollment_status_label,
          }))
        )
      } catch {
        setOrganizations([])
      }
    }
    loadOrgs()
  }, [showCreateModal])

  useEffect(() => {
    if (!showCreateModal) return
    if (createForm.type !== 'institution') return
    if (!createForm.organizationId) return
    const selectedId = Number(createForm.organizationId)
    const stillValid = organizations.some(
      (org) => org.id === selectedId && org.enrollment_status === 'pending_contract_creation'
    )
    if (!stillValid) {
      setCreateForm((prev) => ({ ...prev, organizationId: '' }))
    }
  }, [showCreateModal, createForm.type, createForm.organizationId, organizations])

  const loadContracts = async () => {
    try {
      setLoading(true)
      const response = await apiGateway.get('/finance/contracts/')
      const raw = Array.isArray(response) ? response : response.results || []
      setContracts(
        (raw as Contract[]).map((c) => ({
          ...c,
          seat_cap: typeof c.seat_cap === 'number' ? c.seat_cap : 0,
          seats_used: typeof c.seats_used === 'number' ? c.seats_used : 0,
        }))
      )
    } catch (error) {
      console.error('Failed to load contracts:', error)
      setContracts([])
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'mint'
      case 'signed': return 'defender'
      case 'proposal': return 'gold'
      case 'negotiation': return 'orange'
      case 'pending_payments': return 'gold'
      case 'renewal': return 'steel'
      case 'terminated': return 'orange'
      default: return 'steel'
    }
  }

  const getTypeIcon = (type: string) => {
    return type === 'institution' ? 
      <Building2 className="h-4 w-4" /> : 
      <Users className="h-4 w-4" />
  }

  const filteredContracts = contracts.filter(contract => {
    switch (activeTab) {
      case 'active':
        return contract.is_active
      case 'expiring':
        return contract.is_active && contract.days_until_expiry <= 30
      case 'proposals':
        return (
          contract.status === 'proposal' ||
          contract.status === 'negotiation' ||
          contract.status === 'pending_payments'
        )
      default:
        return true
    }
  })

  const stats = {
    total: contracts.length,
    active: contracts.filter(c => c.is_active).length,
    expiring: contracts.filter(c => c.is_active && c.days_until_expiry <= 30).length,
    proposals: contracts.filter(
      c =>
        c.status === 'proposal' ||
        c.status === 'negotiation' ||
        c.status === 'pending_payments'
    ).length,
    totalValue: contracts.reduce((sum, c) => sum + c.total_value, 0)
  }

  const selectableOrganizations = useMemo(() => {
    if (createForm.type === 'institution') {
      return organizations.filter(
        (org) =>
          org.org_type === 'institution' &&
          org.enrollment_status === 'pending_contract_creation'
      )
    }
    // Employer contracts: org rows typed as employer or legacy sponsor (not generic institution rows)
    return organizations.filter(
      (org) => org.org_type === 'employer' || org.org_type === 'sponsor'
    )
  }, [organizations, createForm.type])

  const handleCreateContract = async () => {
    setCreateError(null)
    const orgId = parseInt(createForm.organizationId, 10)
    if (!orgId) {
      setCreateError(
        createForm.type === 'institution'
          ? 'Please select an organization.'
          : 'Please select an employer or sponsor organization.'
      )
      return
    }
    if (!createForm.start_date || !createForm.end_date) {
      setCreateError('Start and end dates are required.')
      return
    }
    if (!createForm.seat_cap || createForm.seat_cap < 1) {
      setCreateError('Allocate at least one seat (seat cap) for this contract.')
      return
    }
    setCreateSubmitting(true)
    try {
      const created = await apiGateway.post('/finance/contracts/', {
        organization: orgId,
        type: createForm.type,
        start_date: createForm.start_date,
        end_date: createForm.end_date,
        seat_cap: createForm.seat_cap,
        auto_renew: createForm.auto_renew,
        renewal_notice_days: createForm.renewal_notice_days || 60,
      })
      const notifications = (created as any)?.notifications
      if (notifications) {
        const emailSent = Boolean(notifications.email_sent)
        const smsSent = Boolean(notifications.sms_sent)
        const smsProvider = notifications.sms_provider || 'textsms'
        if (emailSent && smsSent) {
          toast.success('Contract created. Email and SMS sent.')
        } else if (emailSent && !smsSent) {
          toast.success(
            `Contract created. Email sent, SMS not sent (${smsProvider}). Check TextSMS credentials in .env.`
          )
        } else {
          toast.success('Contract created. Notification delivery pending.')
        }
      } else {
        toast.success('Contract created successfully.')
      }
      setShowCreateModal(false)
      setCreateForm({
        organizationId: '',
        type: 'institution',
        start_date: '',
        end_date: '',
        seat_cap: 50,
        auto_renew: false,
        renewal_notice_days: 60,
      })
      await loadContracts()
    } catch (e: unknown) {
      let msg = 'Failed to create contract.'
      if (e instanceof ApiError) {
        const d = e.data?.detail
        msg =
          typeof d === 'string'
            ? d
            : Array.isArray(d) && d.length
              ? String(d[0])
              : e.message || msg
      } else if (e && typeof e === 'object' && 'message' in e) {
        msg = String((e as { message?: string }).message)
      }
      setCreateError(msg)
    } finally {
      setCreateSubmitting(false)
    }
  }

  const calculateEndDateFromStart = (startDate: string): string => {
    if (!startDate) return ''
    const date = new Date(`${startDate}T00:00:00`)
    // 12-month contract term from start date
    date.setFullYear(date.getFullYear() + 1)
    return date.toISOString().slice(0, 10)
  }

  const handleOpenActionMenu = (event: React.MouseEvent<HTMLElement>, contract: Contract) => {
    setActionMenuAnchor(event.currentTarget)
    setActionMenuContractId(contract.id)
    setSelectedContract(contract)
  }

  const handleCloseActionMenu = () => {
    setActionMenuAnchor(null)
    setActionMenuContractId(null)
  }

  const openViewModal = () => {
    if (!selectedContract) return
    setShowViewModal(true)
    handleCloseActionMenu()
  }

  const openEditModal = () => {
    if (!selectedContract) return
    setEditError(null)
    setEditForm({
      type: selectedContract.type,
      start_date: selectedContract.start_date,
      end_date: selectedContract.end_date,
      seat_cap: selectedContract.seat_cap ?? 50,
      auto_renew: selectedContract.auto_renew,
      renewal_notice_days: selectedContract.renewal_notice_days,
    })
    setShowEditModal(true)
    handleCloseActionMenu()
  }

  const openDeleteModal = () => {
    if (!selectedContract) return
    setDeleteError(null)
    setShowDeleteModal(true)
    handleCloseActionMenu()
  }

  const openInviteTemplateModal = () => {
    if (!selectedContract) return
    setShowInviteTemplateModal(true)
    handleCloseActionMenu()
  }

  const buildInviteTemplate = (contract: Contract): string => {
    const origin =
      typeof window !== 'undefined' && window.location?.origin
        ? window.location.origin
        : (process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000')
    const onboardingPath =
      contract.type === 'employer' ? '/onboarding/employer' : '/onboarding/institution'
    const header = `Hello ${contract.organization_name},\n\n`
    const contractInfo =
      `A ${contract.type} contract has been created for your organization in OCH.\n\n` +
      `Contract information:\n` +
      `- Organization: ${contract.organization_name}\n` +
      `- Contract type: ${contract.type}\n` +
      `- Start date: ${new Date(contract.start_date).toLocaleDateString()}\n` +
      `- End date: ${new Date(contract.end_date).toLocaleDateString()}\n` +
      `- Seat allocation (cap): ${contract.seat_cap ?? '—'}\n` +
      `- Minimum commitment: 12 months\n\n` +
      `Onboarding link:\n` +
      `${origin}${onboardingPath}?organization=${contract.organization ?? ''}&contract=${contract.id}\n\n` +
      `From this onboarding flow you can:\n` +
      `1) Accept terms and conditions\n` +
      `2) Choose preferred tier and billing cycle\n` +
      `3) Receive invoice and complete payment\n` +
      `4) Join organization portal and add students\n\n`

    const institutionBody =
      `University and educational institution licensing follows a contract-based model with mandatory 12-month minimum commitment, per-student licensing pricing, and custom billing cycles. Institutions can also purchase dedicated cohort seats in bulk through their contract.\n\n` +
      `Per-student licensing tiers:\n` +
      `- 1-50 students: $15/student/month ($180/year)\n` +
      `- 51-200 students: $12/student/month ($144/year)\n` +
      `- 201-500 students: $9/student/month ($108/year)\n` +
      `- 500+ students: $7/student/month ($84/year)\n\n` +
      `Billing cycles:\n` +
      `- Monthly, Quarterly, Annual (Net 30)\n`

    const employerBody =
      `Employers pay a monthly retainer fee to access the talent pipeline and recruit from OCH graduates. Employers can also sponsor private cohorts for their employees.\n\n` +
      `Monthly retainer tiers:\n` +
      `- Starter: $500/month (up to 5 candidates/quarter)\n` +
      `- Growth: $1,500/month (up to 15 candidates/quarter)\n` +
      `- Enterprise: $3,500/month (unlimited pipeline)\n\n` +
      `Placement fee tiers:\n` +
      `- Starter: $2,000 per successful placement\n` +
      `- Growth: $1,500 per successful placement\n` +
      `- Enterprise: $1,000 per successful placement\n`

    const footer = `\nRegards,\nOCH Finance Team`
    return header + contractInfo + (contract.type === 'institution' ? institutionBody : employerBody) + footer
  }

  const handleUpdateContract = async () => {
    if (!selectedContract) return
    if (!editForm.start_date || !editForm.end_date) {
      setEditError('Start and end dates are required.')
      return
    }
    if (!editForm.seat_cap || editForm.seat_cap < 1) {
      setEditError('Seat cap must be at least 1.')
      return
    }
    setEditSubmitting(true)
    setEditError(null)
    try {
      await apiGateway.patch(`/finance/contracts/${selectedContract.id}/`, {
        type: editForm.type,
        start_date: editForm.start_date,
        end_date: editForm.end_date,
        seat_cap: editForm.seat_cap,
        auto_renew: editForm.auto_renew,
        renewal_notice_days: editForm.renewal_notice_days || 60,
      })
      setShowEditModal(false)
      await loadContracts()
    } catch (e: unknown) {
      let msg = 'Failed to update contract.'
      if (e instanceof ApiError) {
        const d = e.data?.detail
        msg = typeof d === 'string' ? d : e.message || msg
      } else if (e && typeof e === 'object' && 'message' in e) {
        msg = String((e as { message?: string }).message)
      }
      setEditError(msg)
    } finally {
      setEditSubmitting(false)
    }
  }

  const handleDeleteContract = async () => {
    if (!selectedContract) return
    setDeleteSubmitting(true)
    setDeleteError(null)
    try {
      await apiGateway.delete(`/finance/contracts/${selectedContract.id}/`)
      setShowDeleteModal(false)
      setSelectedContract(null)
      await loadContracts()
    } catch (e: unknown) {
      let msg = 'Failed to delete contract.'
      if (e instanceof ApiError) {
        const d = e.data?.detail
        msg = typeof d === 'string' ? d : e.message || msg
      } else if (e && typeof e === 'object' && 'message' in e) {
        msg = String((e as { message?: string }).message)
      }
      setDeleteError(msg)
    } finally {
      setDeleteSubmitting(false)
    }
  }

  if (loading) {
    return (
      <RouteGuard requiredRoles={['finance', 'admin']}>
        <div className="min-h-screen bg-och-midnight flex">
          <FinanceNavigation />
          <div className="flex-1 lg:ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
              <p className="text-och-steel text-sm">Loading contracts...</p>
            </div>
          </div>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight flex">
        <FinanceNavigation />
        <div className="flex-1 lg:ml-64">
          <div className="px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-h1 font-bold text-white">Contract Management</h1>
                  <p className="mt-1 body-m text-och-steel">
                    Manage institution and employer agreements
                  </p>
                </div>
                <Button onClick={() => setShowCreateModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  New Contract
                </Button>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
              <Card className="p-4 bg-och-midnight border border-och-steel/20">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="h-5 w-5 text-och-defender" />
                  <p className="font-medium text-white">Total Contracts</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </Card>

              <Card className="p-4 bg-och-mint/10 border border-och-mint/30">
                <div className="flex items-center gap-3 mb-2">
                  <CheckCircle className="h-5 w-5 text-och-mint" />
                  <p className="font-medium text-white">Active</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.active}</p>
              </Card>

              <Card className="p-4 bg-och-orange/10 border border-och-orange/30">
                <div className="flex items-center gap-3 mb-2">
                  <AlertTriangle className="h-5 w-5 text-och-orange" />
                  <p className="font-medium text-white">Expiring Soon</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.expiring}</p>
              </Card>

              <Card className="p-4 bg-och-gold/10 border border-och-gold/30">
                <div className="flex items-center gap-3 mb-2">
                  <Clock className="h-5 w-5 text-och-gold" />
                  <p className="font-medium text-white">Proposals</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.proposals}</p>
              </Card>

              <Card className="p-4 bg-och-defender/10 border border-och-defender/30">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign className="h-5 w-5 text-och-defender" />
                  <p className="font-medium text-white">Total Value</p>
                </div>
                <p className="text-2xl font-bold text-white">
                  KSh {stats.totalValue.toLocaleString()}
                </p>
              </Card>
            </div>

            {/* Tabs */}
            <div className="border-b border-och-steel/20 mb-6">
              <nav className="-mb-px flex space-x-8">
                {[
                  { key: 'all', label: 'All Contracts', count: stats.total },
                  { key: 'active', label: 'Active', count: stats.active },
                  { key: 'expiring', label: 'Expiring Soon', count: stats.expiring },
                  { key: 'proposals', label: 'Proposals', count: stats.proposals }
                ].map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key as TabType)}
                    className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium body-s flex items-center gap-2 ${
                      activeTab === tab.key
                        ? 'border-och-defender text-och-mint'
                        : 'border-transparent text-och-steel hover:text-white hover:border-och-steel/30'
                    }`}
                  >
                    {tab.label}
                    <Badge variant="steel" className="text-xs">
                      {tab.count}
                    </Badge>
                  </button>
                ))}
              </nav>
            </div>

            {/* Contracts List */}
            <Card className="p-6 bg-och-midnight border border-och-steel/20">
              {filteredContracts.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-och-steel" />
                  <p className="body-m text-och-steel mb-2">No contracts found</p>
                  <p className="body-s text-och-steel/70">
                    {activeTab === 'all' 
                      ? 'Create your first contract to get started'
                      : `No contracts match the ${activeTab} filter`
                    }
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-och-steel/20">
                    <thead className="bg-och-midnight/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Organization
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Seats
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Value
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Duration
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Email Sent
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Expiry
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                      {filteredContracts.map((contract) => (
                        <tr key={contract.id} className="hover:bg-och-steel/5">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-3">
                              {getTypeIcon(contract.type)}
                              <div>
                                <p className="text-sm font-medium text-white">
                                  {contract.organization_name}
                                </p>
                                <p className="text-xs text-och-steel">
                                  {contract.payment_terms}
                                </p>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={contract.type === 'institution' ? 'defender' : 'mint'}>
                              {contract.type}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                            <span className="text-och-steel">{contract.seats_used ?? 0}</span>
                            <span className="text-och-steel"> / </span>
                            {contract.seat_cap ?? 0}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                            KSh {contract.total_value.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(contract.start_date).toLocaleDateString()} - {new Date(contract.end_date).toLocaleDateString()}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={getStatusColor(contract.status)}>
                              {contract.status}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={contract.email_sent ? 'mint' : 'orange'}>
                              {contract.email_sent ? 'true' : 'false'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                            {contract.is_active ? (
                              <div className={`flex items-center gap-1 ${
                                contract.days_until_expiry <= 30 ? 'text-och-orange' : 'text-och-steel'
                              }`}>
                                <AlertTriangle className={`h-3 w-3 ${
                                  contract.days_until_expiry <= 30 ? 'text-och-orange' : 'text-och-steel'
                                }`} />
                                {contract.days_until_expiry} days
                              </div>
                            ) : (
                              <span className="text-och-steel">Inactive</span>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <IconButton
                              onClick={(e) => handleOpenActionMenu(e, contract)}
                              sx={{ color: '#94A3B8' }}
                              aria-label="contract actions"
                            >
                              <MoreVertIcon />
                            </IconButton>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>

      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={handleCloseActionMenu}
        PaperProps={{
          sx: {
            backgroundColor: '#0A0E1A',
            color: '#E2E8F0',
            border: '1px solid rgba(148,163,184,0.2)',
          }
        }}
      >
        <MenuItem onClick={openViewModal}>View</MenuItem>
        <MenuItem onClick={openInviteTemplateModal}>View Invite Template</MenuItem>
        <MenuItem onClick={openEditModal}>Edit</MenuItem>
        <MenuItem
          onClick={openDeleteModal}
          sx={{ color: '#F97316' }}
        >
          Delete
        </MenuItem>
      </Menu>

      {showViewModal && selectedContract && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-xl mx-4">
            <h3 className="text-h3 font-semibold text-white mb-5">Contract Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-och-steel">Organization</span><span className="text-white">{selectedContract.organization_name}</span></div>
              <div className="flex justify-between"><span className="text-och-steel">Seat cap</span><span className="text-white">{selectedContract.seat_cap ?? '—'} ({selectedContract.seats_used ?? 0} used)</span></div>
              <div className="flex justify-between"><span className="text-och-steel">Type</span><span className="text-white">{selectedContract.type}</span></div>
              <div className="flex justify-between"><span className="text-och-steel">Status</span><span className="text-white">{selectedContract.status}</span></div>
              <div className="flex justify-between"><span className="text-och-steel">Start</span><span className="text-white">{new Date(selectedContract.start_date).toLocaleDateString()}</span></div>
              <div className="flex justify-between"><span className="text-och-steel">End</span><span className="text-white">{new Date(selectedContract.end_date).toLocaleDateString()}</span></div>
              <div className="flex justify-between"><span className="text-och-steel">Value</span><span className="text-white">KSh {selectedContract.total_value.toLocaleString()}</span></div>
            </div>
            <div className="mt-6 flex justify-end">
              <Button variant="outline" onClick={() => setShowViewModal(false)}>Close</Button>
            </div>
          </Card>
        </div>
      )}

      {showInviteTemplateModal && selectedContract && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-h3 font-semibold text-white mb-4">Invite Email Template</h3>
            <p className="text-xs text-och-steel mb-3">
              Preview template for {selectedContract.organization_name} ({selectedContract.type})
            </p>
            <pre className="whitespace-pre-wrap text-sm text-och-steel bg-och-steel/10 border border-och-steel/20 rounded-lg p-4">
              {buildInviteTemplate(selectedContract)}
            </pre>
            <div className="mt-6 flex justify-end">
              <Button variant="outline" onClick={() => setShowInviteTemplateModal(false)}>Close</Button>
            </div>
          </Card>
        </div>
      )}

      {showEditModal && selectedContract && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-xl mx-4">
            <h3 className="text-h3 font-semibold text-white mb-5">Edit Contract</h3>
            {editError && <p className="text-sm text-och-orange mb-4">{editError}</p>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">Type</label>
                <select
                  value={editForm.type}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, type: e.target.value as 'institution' | 'employer' }))}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                >
                  <option value="institution" className="bg-white text-och-midnight">Institution</option>
                  <option value="employer" className="bg-white text-och-midnight">Employer</option>
                </select>
              </div>
              <div className="flex items-end pb-2">
                <label className="inline-flex items-center gap-2 text-sm text-och-steel">
                  <input
                    type="checkbox"
                    checked={editForm.auto_renew}
                    onChange={(e) => setEditForm((prev) => ({ ...prev, auto_renew: e.target.checked }))}
                  />
                  Auto-renew
                </label>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-och-steel mb-2">Seat cap</label>
                <input
                  type="number"
                  min={1}
                  value={editForm.seat_cap}
                  onChange={(e) =>
                    setEditForm((prev) => ({ ...prev, seat_cap: Math.max(1, parseInt(e.target.value, 10) || 1) }))
                  }
                  className="w-full max-w-xs px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                />
                <p className="text-xs text-och-steel mt-1">Institution: enrolled students cap. Employer: placements/pipeline cap.</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">Start Date</label>
                <input
                  type="date"
                  value={editForm.start_date}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, start_date: e.target.value }))}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">End Date</label>
                <input
                  type="date"
                  value={editForm.end_date}
                  onChange={(e) => setEditForm((prev) => ({ ...prev, end_date: e.target.value }))}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                />
              </div>
            </div>
            <div className="mt-6 flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setShowEditModal(false)} disabled={editSubmitting}>Cancel</Button>
              <Button className="flex-1 bg-och-mint hover:bg-och-mint/80" onClick={() => void handleUpdateContract()} disabled={editSubmitting}>
                {editSubmitting ? 'Saving…' : 'Save Changes'}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {showDeleteModal && selectedContract && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-xl mx-4">
            <h3 className="text-h3 font-semibold text-white mb-4">Delete Contract</h3>
            <p className="text-sm text-och-steel mb-2">
              You are deleting the contract for <span className="text-white font-medium">{selectedContract.organization_name}</span>.
            </p>
            <p className="text-sm text-och-steel mb-4">
              This removes the contract record from finance lists and breaks future reporting continuity tied to this contract.
              Historical invoices/payments that reference it may no longer be linked in contract views.
            </p>
            {deleteError && <p className="text-sm text-och-orange mb-4">{deleteError}</p>}
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setShowDeleteModal(false)} disabled={deleteSubmitting}>
                Cancel
              </Button>
              <Button
                className="flex-1 bg-och-orange hover:bg-och-orange/80"
                onClick={() => void handleDeleteContract()}
                disabled={deleteSubmitting}
              >
                {deleteSubmitting ? 'Deleting…' : 'Delete Contract'}
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Create Contract Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-h3 font-semibold text-white mb-6">Create New Contract</h3>
            <div className="space-y-4">
              {createError && (
                <p className="text-sm text-och-orange">{createError}</p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    {createForm.type === 'institution' ? 'Organization' : 'Employer / sponsor'}
                  </label>
                  <select
                    value={createForm.organizationId}
                    onChange={(e) =>
                      setCreateForm((prev) => ({ ...prev, organizationId: e.target.value }))
                    }
                    className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  >
                    <option value="" className="bg-white text-och-midnight">
                      {createForm.type === 'institution'
                        ? 'Select organization...'
                        : 'Select employer or sponsor...'}
                    </option>
                    {selectableOrganizations.map((org) => (
                      <option key={org.id} value={String(org.id)} className="bg-white text-och-midnight">
                        {org.name}
                        {org.org_type ? ` (${org.org_type})` : ''}
                        {createForm.type === 'institution' && org.enrollment_status_label
                          ? ` - ${org.enrollment_status_label}`
                          : ''}
                      </option>
                    ))}
                  </select>
                  {createForm.type === 'institution' && selectableOrganizations.length === 0 && (
                    <p className="mt-2 text-xs text-och-steel">
                      No organizations are currently in pending contract creation.
                    </p>
                  )}
                  {createForm.type === 'employer' && selectableOrganizations.length === 0 && (
                    <p className="mt-2 text-xs text-och-steel">
                      No organizations with type Employer or Sponsor found. Add them under Organizations first.
                    </p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    Contract Type
                  </label>
                  <select
                    value={createForm.type}
                    onChange={(e) =>
                      setCreateForm((prev) => ({
                        ...prev,
                        type: e.target.value as 'institution' | 'employer',
                        organizationId: '',
                      }))
                    }
                    className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  >
                    <option value="institution" className="bg-white text-och-midnight">Institution</option>
                    <option value="employer" className="bg-white text-och-midnight">Employer</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={createForm.start_date}
                    onChange={(e) =>
                      setCreateForm((prev) => ({
                        ...prev,
                        start_date: e.target.value,
                        end_date: calculateEndDateFromStart(e.target.value),
                      }))
                    }
                    className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    value={createForm.end_date}
                    onChange={(e) =>
                      setCreateForm((prev) => ({ ...prev, end_date: e.target.value }))
                    }
                    className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Seat cap (allocation)
                </label>
                <input
                  type="number"
                  min={1}
                  value={createForm.seat_cap}
                  onChange={(e) =>
                    setCreateForm((prev) => ({
                      ...prev,
                      seat_cap: Math.max(1, parseInt(e.target.value, 10) || 1),
                    }))
                  }
                  className="w-full max-w-xs px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                />
                <p className="mt-2 text-xs text-och-steel">
                  {createForm.type === 'institution'
                    ? 'Maximum concurrent students this institution may enroll under the contract.'
                    : 'Maximum placements or pipeline actions the employer may use under this contract.'}
                </p>
              </div>

              <div className="rounded-lg border border-och-steel/20 bg-och-steel/10 p-3 text-sm text-och-steel">
                {createForm.type === 'institution'
                  ? 'Contract details and onboarding instructions will be emailed to the organization contact.'
                  : 'Contract details will be emailed to the employer or sponsor contact on file.'}
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="auto_renew"
                  checked={createForm.auto_renew}
                  onChange={(e) =>
                    setCreateForm((prev) => ({ ...prev, auto_renew: e.target.checked }))
                  }
                  className="rounded border-och-steel/20 bg-och-steel/10 text-och-mint focus:ring-och-mint"
                />
                <label htmlFor="auto_renew" className="text-sm text-och-steel">
                  Auto-renew contract
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCreateModal(false)
                    setCreateError(null)
                  }}
                  className="flex-1"
                  disabled={createSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1 bg-och-mint hover:bg-och-mint/80"
                  onClick={() => void handleCreateContract()}
                  disabled={createSubmitting}
                >
                  {createSubmitting ? 'Creating…' : 'Create Contract'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </RouteGuard>
  )
}