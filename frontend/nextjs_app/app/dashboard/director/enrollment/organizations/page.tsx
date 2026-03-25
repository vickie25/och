'use client'

import { useState, useEffect, useMemo } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { apiGateway } from '@/services/apiGateway'
import toast from 'react-hot-toast'

type OrgType = 'institution' | 'employer' | 'sponsor' | 'partner'

interface Organization {
  id: string
  name: string
  org_type?: OrgType
  contact_person_name?: string
  contact_email?: string
  contact_phone?: string
  member_count?: number
  enrollment_status?: 'active' | 'pending_contract_creation' | 'pending_invoice_payment'
  enrollment_status_label?: string
}

const ORG_TYPE_LABEL: Record<OrgType, string> = {
  institution: 'Institution',
  employer: 'Employer',
  sponsor: 'Sponsor',
  partner: 'Partner',
}

export default function OrganizationsPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [isUpdating, setIsUpdating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null)
  const [typeFilter, setTypeFilter] = useState<'all' | 'institution' | 'employer'>('all')
  const [formData, setFormData] = useState({
    name: '',
    org_type: 'institution' as 'institution' | 'employer',
    contact_person_name: '',
    contact_email: '',
    contact_phone: '',
  })
  const [editFormData, setEditFormData] = useState({
    name: '',
    org_type: 'institution' as OrgType,
    contact_person_name: '',
    contact_email: '',
    contact_phone: '',
  })

  const getStatusClasses = (status?: Organization['enrollment_status']) => {
    switch (status) {
      case 'active':
        return 'bg-och-mint/20 text-och-mint border border-och-mint/40'
      case 'pending_invoice_payment':
        return 'bg-och-gold/20 text-och-gold border border-och-gold/40'
      case 'pending_contract_creation':
      default:
        return 'bg-och-orange/20 text-och-orange border border-och-orange/40'
    }
  }

  const loadOrganizations = async () => {
    setIsLoading(true)
    try {
      const data = (await apiGateway.get('/orgs/')) as any
      const orgsList = data?.results || data?.data || data || []
      setOrganizations(orgsList)
    } catch {
      toast.error('Failed to load organizations')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadOrganizations()
  }, [])

  const filteredOrgs = useMemo(() => {
    if (typeFilter === 'all') return organizations
    if (typeFilter === 'institution') {
      return organizations.filter((o) => o.org_type === 'institution')
    }
    // employer tab: employer + legacy sponsor rows used like employers
    return organizations.filter((o) => o.org_type === 'employer' || o.org_type === 'sponsor')
  }, [organizations, typeFilter])

  const handleCreateOrganization = async () => {
    if (!formData.name || !formData.contact_person_name || !formData.contact_email) {
      toast.error('Organization name, contact person name, and contact email are required')
      return
    }

    setIsCreating(true)
    try {
      await apiGateway.post('/orgs/', {
        name: formData.name.trim(),
        org_type: formData.org_type,
        status: 'active',
        contact_person_name: formData.contact_person_name.trim(),
        contact_email: formData.contact_email.trim(),
        contact_phone: formData.contact_phone?.trim() || undefined,
      })

      toast.success('Organization created successfully')
      setShowCreateModal(false)
      setFormData({
        name: '',
        org_type: 'institution',
        contact_person_name: '',
        contact_email: '',
        contact_phone: '',
      })
      await loadOrganizations()
    } catch (err: any) {
      toast.error(err?.response?.data?.error || err?.message || 'Failed to create organization')
    } finally {
      setIsCreating(false)
    }
  }

  const handleEditClick = (org: Organization) => {
    setSelectedOrg(org)
    setEditFormData({
      name: org.name,
      org_type: (org.org_type as OrgType) || 'employer',
      contact_person_name: org.contact_person_name || '',
      contact_email: org.contact_email || '',
      contact_phone: org.contact_phone || '',
    })
    setShowEditModal(true)
  }

  const handleUpdateOrganization = async () => {
    if (!selectedOrg || !editFormData.name || !editFormData.contact_person_name || !editFormData.contact_email) {
      toast.error('Organization name, contact person name, and contact email are required')
      return
    }

    setIsUpdating(true)
    try {
      await apiGateway.patch(`/orgs/${selectedOrg.id}/`, {
        name: editFormData.name.trim(),
        org_type: editFormData.org_type,
        contact_person_name: editFormData.contact_person_name.trim(),
        contact_email: editFormData.contact_email.trim(),
        contact_phone: editFormData.contact_phone?.trim() || undefined,
      })

      toast.success('Organization updated successfully')
      setShowEditModal(false)
      setSelectedOrg(null)
      await loadOrganizations()
    } catch (err: any) {
      toast.error(err?.response?.data?.error || err?.message || 'Failed to update organization')
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDeleteClick = (org: Organization) => {
    setSelectedOrg(org)
    setShowDeleteModal(true)
  }

  const handleDeleteOrganization = async () => {
    if (!selectedOrg) return

    setIsDeleting(true)
    try {
      await apiGateway.delete(`/orgs/${selectedOrg.id}/`)
      toast.success('Organization deleted successfully')
      setShowDeleteModal(false)
      setSelectedOrg(null)
      await loadOrganizations()
    } catch (err: any) {
      toast.error(err?.response?.data?.error || err?.message || 'Failed to delete organization')
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <RouteGuard>
      <div className="w-full max-w-[1600px]">
        <div className="mb-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between mb-4">
            <div>
              <h1 className="text-4xl font-bold mb-2 text-och-defender">Organizations</h1>
              <p className="text-och-steel max-w-2xl">
                Create and manage <strong className="text-white">institutions</strong> and{' '}
                <strong className="text-white">employers</strong>. Finance uses these records when creating
                institution or employer contracts.
              </p>
            </div>
            <Button variant="defender" size="sm" onClick={() => setShowCreateModal(true)}>
              + Add organization
            </Button>
          </div>

          <div className="flex flex-wrap gap-2 border-b border-och-steel/20 pb-2">
            {(
              [
                { key: 'all', label: `All (${organizations.length})` },
                { key: 'institution', label: 'Institutions' },
                { key: 'employer', label: 'Employers' },
              ] as const
            ).map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setTypeFilter(tab.key)}
                className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  typeFilter === tab.key
                    ? 'bg-och-defender/30 text-white border border-och-defender/50'
                    : 'text-och-steel hover:text-white border border-transparent'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <Card>
          <div className="p-6">
            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-och-defender mx-auto mb-4"></div>
                <p className="text-och-steel">Loading...</p>
              </div>
            ) : filteredOrgs.length === 0 ? (
              <div className="text-center py-12 text-och-steel">
                No organizations match this filter.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px]">
                  <thead>
                    <tr className="border-b border-och-steel/20">
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Name</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Type</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Enrollment</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Contact</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Email</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Phone</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Members</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-och-steel">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredOrgs.map((org) => (
                      <tr key={org.id} className="border-b border-och-steel/10 hover:bg-och-midnight/30">
                        <td className="py-3 px-4 text-white">{org.name}</td>
                        <td className="py-3 px-4 text-och-steel text-sm">
                          {org.org_type ? ORG_TYPE_LABEL[org.org_type] : '—'}
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${getStatusClasses(org.enrollment_status)}`}
                          >
                            {org.enrollment_status_label || 'Pending contract creation'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-och-steel">{org.contact_person_name || '—'}</td>
                        <td className="py-3 px-4 text-och-steel">{org.contact_email || '—'}</td>
                        <td className="py-3 px-4 text-och-steel">{org.contact_phone || '—'}</td>
                        <td className="py-3 px-4 text-och-steel">{org.member_count ?? 0}</td>
                        <td className="py-3 px-4">
                          <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={() => handleEditClick(org)}>
                              Edit
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteClick(org)}
                              className="text-och-orange border-och-orange/50 hover:bg-och-orange/20"
                            >
                              Delete
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </Card>

        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-lg">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">Create organization</h2>
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="text-och-steel hover:text-white"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Organization type *</label>
                    <select
                      value={formData.org_type}
                      onChange={(e) =>
                        setFormData({ ...formData, org_type: e.target.value as 'institution' | 'employer' })
                      }
                      className="w-full rounded-md border border-och-steel/30 bg-och-midnight px-3 py-2 text-sm text-white"
                    >
                      <option value="institution">Institution</option>
                      <option value="employer">Employer</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Organization name *</label>
                    <Input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g. University or company name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Contact person *</label>
                    <Input
                      type="text"
                      value={formData.contact_person_name}
                      onChange={(e) => setFormData({ ...formData, contact_person_name: e.target.value })}
                      placeholder="Full name"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Contact email *</label>
                    <Input
                      type="email"
                      value={formData.contact_email}
                      onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                      placeholder="contact@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Contact phone</label>
                    <Input
                      type="tel"
                      value={formData.contact_phone}
                      onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                      placeholder="+254…"
                    />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button variant="outline" onClick={() => setShowCreateModal(false)} disabled={isCreating}>
                      Cancel
                    </Button>
                    <Button variant="defender" onClick={handleCreateOrganization} disabled={isCreating}>
                      {isCreating ? 'Creating...' : 'Create'}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {showEditModal && selectedOrg && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-lg">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-white">Edit organization</h2>
                  <button
                    type="button"
                    onClick={() => {
                      setShowEditModal(false)
                      setSelectedOrg(null)
                    }}
                    className="text-och-steel hover:text-white"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Organization type *</label>
                    <select
                      value={editFormData.org_type}
                      onChange={(e) => setEditFormData({ ...editFormData, org_type: e.target.value as OrgType })}
                      className="w-full rounded-md border border-och-steel/30 bg-och-midnight px-3 py-2 text-sm text-white"
                    >
                      <option value="institution">Institution</option>
                      <option value="employer">Employer</option>
                      <option value="sponsor">Sponsor (legacy)</option>
                      <option value="partner">Partner</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Organization name *</label>
                    <Input
                      type="text"
                      value={editFormData.name}
                      onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Contact person *</label>
                    <Input
                      type="text"
                      value={editFormData.contact_person_name}
                      onChange={(e) => setEditFormData({ ...editFormData, contact_person_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Contact email *</label>
                    <Input
                      type="email"
                      value={editFormData.contact_email}
                      onChange={(e) => setEditFormData({ ...editFormData, contact_email: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white mb-2">Contact phone</label>
                    <Input
                      type="tel"
                      value={editFormData.contact_phone}
                      onChange={(e) => setEditFormData({ ...editFormData, contact_phone: e.target.value })}
                    />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button
                      variant="outline"
                      onClick={() => {
                        setShowEditModal(false)
                        setSelectedOrg(null)
                      }}
                      disabled={isUpdating}
                    >
                      Cancel
                    </Button>
                    <Button variant="defender" onClick={handleUpdateOrganization} disabled={isUpdating}>
                      {isUpdating ? 'Saving...' : 'Save'}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {showDeleteModal && selectedOrg && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-md">
              <div className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Delete organization</h3>
                <p className="text-och-steel mb-6">
                  Delete <span className="text-white font-medium">{selectedOrg.name}</span>? This cannot be undone.
                </p>
                <div className="flex gap-2 justify-end">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowDeleteModal(false)
                      setSelectedOrg(null)
                    }}
                    disabled={isDeleting}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="outline"
                    onClick={handleDeleteOrganization}
                    disabled={isDeleting}
                    className="bg-och-orange/20 text-och-orange border-och-orange/50 hover:bg-och-orange/30"
                  >
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </RouteGuard>
  )
}
