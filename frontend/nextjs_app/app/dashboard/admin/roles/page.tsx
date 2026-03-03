'use client'

import { useState, useEffect, useMemo } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { AdminLayout } from '@/components/admin/AdminLayout'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { djangoClient, type RoleWithPermissions, type Permission } from '@/services/djangoClient'
import { apiGateway } from '@/services/apiGateway'

export default function RolesPage() {
  const [activeTab, setActiveTab] = useState<'list' | 'permissions'>('list')
  // RBAC: manage roles and permissions (admin only)
  const [apiRoles, setApiRoles] = useState<RoleWithPermissions[]>([])
  const [apiPermissions, setApiPermissions] = useState<Permission[]>([])
  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(null)
  const [permissionIdsForRole, setPermissionIdsForRole] = useState<number[]>([])
  const [rbacLoading, setRbacLoading] = useState(false)
  const [rbacSaving, setRbacSaving] = useState(false)
  const [rbacError, setRbacError] = useState<string | null>(null)
  const [rbacSuccess, setRbacSuccess] = useState<string | null>(null)
  const [showAddRoleModal, setShowAddRoleModal] = useState(false)
  const [showEditRoleModal, setShowEditRoleModal] = useState(false)
  const [showDeleteRoleModal, setShowDeleteRoleModal] = useState(false)
  const [roleToEdit, setRoleToEdit] = useState<RoleWithPermissions | null>(null)
  const [roleToDelete, setRoleToDelete] = useState<RoleWithPermissions | null>(null)
  const [newRoleForm, setNewRoleForm] = useState({ name: '', display_name: '', description: '' })
  const [editRoleForm, setEditRoleForm] = useState({ display_name: '', description: '' })
  const [isCreatingRole, setIsCreatingRole] = useState(false)
  const [isUpdatingRole, setIsUpdatingRole] = useState(false)
  const [isDeletingRole, setIsDeletingRole] = useState(false)

  const permissionsByResource = useMemo(() => {
    const map = new Map<string, Permission[]>()
    for (const p of apiPermissions) {
      const key = p.resource_type
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(p)
    }
    const sorted = Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]))
    return Object.fromEntries(sorted)
  }, [apiPermissions])

  useEffect(() => {
    loadRbacData()
  }, [])

  useEffect(() => {
    if (selectedRoleId != null) {
      const role = apiRoles.find((r) => r.id === selectedRoleId)
      const perms = role?.permissions ?? []
      setPermissionIdsForRole(Array.isArray(perms) ? perms.map((p: { id: number }) => p.id) : [])
    } else {
      setPermissionIdsForRole([])
    }
  }, [selectedRoleId, apiRoles])

  const loadRbacData = async () => {
    setRbacError(null)
    setRbacLoading(true)
    try {
      const [rolesData, permsData] = await Promise.all([
        djangoClient.roles.listRoles(),
        djangoClient.permissions.listPermissions(),
      ])
      setApiRoles(rolesData)
      setApiPermissions(permsData)
      if (selectedRoleId == null && rolesData.length > 0) {
        setSelectedRoleId(rolesData[0].id)
      }
    } catch (err: any) {
      setRbacError(err?.message || 'Failed to load roles and permissions')
      setApiRoles([])
      setApiPermissions([])
    } finally {
      setRbacLoading(false)
    }
  }

  const saveRolePermissions = async () => {
    if (selectedRoleId == null) return
    setRbacError(null)
    setRbacSuccess(null)
    setRbacSaving(true)
    try {
      await djangoClient.roles.updateRole(selectedRoleId, { permission_ids: permissionIdsForRole })
      setRbacSuccess('Permissions saved.')
      const updated = await djangoClient.roles.getRole(selectedRoleId)
      setApiRoles((prev) => prev.map((r) => (r.id === selectedRoleId ? updated : r)))
      const nextPerms = updated?.permissions ?? []
      setPermissionIdsForRole(Array.isArray(nextPerms) ? nextPerms.map((p: { id: number }) => p.id) : [])
    } catch (err: any) {
      setRbacError(err?.message || 'Failed to save permissions')
    } finally {
      setRbacSaving(false)
    }
  }

  const togglePermission = (permId: number) => {
    setPermissionIdsForRole((prev) =>
      prev.includes(permId) ? prev.filter((id) => id !== permId) : [...prev, permId]
    )
  }

  const clearSectionPermissions = (permIds: number[]) => {
    setPermissionIdsForRole((prev) => prev.filter((id) => !permIds.includes(id)))
  }

  const selectSectionPermissions = (permIds: number[]) => {
    setPermissionIdsForRole((prev) => [...new Set([...prev, ...permIds])])
  }

  const handleCreateRole = async () => {
    if (!newRoleForm.name || !newRoleForm.display_name) {
      alert('Role name and display name are required')
      return
    }
    
    setIsCreatingRole(true)
    setRbacError(null)
    try {
      await apiGateway.post('/roles/', {
        name: newRoleForm.name.toLowerCase().replace(/\s+/g, '_'),
        display_name: newRoleForm.display_name,
        description: newRoleForm.description || undefined,
      })
      setRbacSuccess('Role created successfully')
      setShowAddRoleModal(false)
      setNewRoleForm({ name: '', display_name: '', description: '' })
      await loadRbacData()
    } catch (err: any) {
      const errorMsg = err?.response?.data?.name?.[0] || err?.response?.data?.detail || err?.message || 'Failed to create role'
      setRbacError(errorMsg)
    } finally {
      setIsCreatingRole(false)
    }
  }

  const handleEditRole = async () => {
    if (!roleToEdit || !editRoleForm.display_name) {
      alert('Display name is required')
      return
    }
    
    setIsUpdatingRole(true)
    setRbacError(null)
    try {
      await apiGateway.patch(`/roles/${roleToEdit.id}/`, {
        display_name: editRoleForm.display_name,
        description: editRoleForm.description || undefined,
      })
      setRbacSuccess('Role updated successfully')
      setShowEditRoleModal(false)
      setRoleToEdit(null)
      setEditRoleForm({ display_name: '', description: '' })
      await loadRbacData()
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to update role'
      setRbacError(errorMsg)
    } finally {
      setIsUpdatingRole(false)
    }
  }

  const handleDeleteRole = async () => {
    if (!roleToDelete) return
    
    setIsDeletingRole(true)
    setRbacError(null)
    try {
      await apiGateway.delete(`/roles/${roleToDelete.id}/`)
      setRbacSuccess('Role deleted successfully')
      setShowDeleteRoleModal(false)
      setRoleToDelete(null)
      await loadRbacData()
    } catch (err: any) {
      const errorMsg = err?.response?.data?.detail || err?.message || 'Failed to delete role'
      setRbacError(errorMsg)
    } finally {
      setIsDeletingRole(false)
    }
  }

  return (
    <RouteGuard>
      <AdminLayout>
        <div className="max-w-7xl mx-auto">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2 text-och-gold">Roles Management</h1>
              <p className="text-och-steel">Manage roles and assign permissions</p>
            </div>
            <Button
              variant="defender"
              size="sm"
              onClick={() => setShowAddRoleModal(true)}
            >
              + Add Role
            </Button>
          </div>

          {/* Tabs */}
          <div className="mb-6 border-b border-och-steel/20">
            <div className="flex gap-4">
              <button
                onClick={() => setActiveTab('list')}
                className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                  activeTab === 'list'
                    ? 'border-och-gold text-och-gold'
                    : 'border-transparent text-och-steel hover:text-white'
                }`}
              >
                Roles List
              </button>
              <button
                onClick={() => setActiveTab('permissions')}
                className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                  activeTab === 'permissions'
                    ? 'border-och-gold text-och-gold'
                    : 'border-transparent text-och-steel hover:text-white'
                }`}
              >
                Manage Permissions
              </button>
            </div>
          </div>

          {/* Main Content - Roles Management */}
          <div className="space-y-6">
            {/* Roles List Tab */}
            {activeTab === 'list' && (
              <Card>
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-white mb-4">All Roles</h2>
                  {rbacError && (
                    <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                      {rbacError}
                    </div>
                  )}
                  {rbacSuccess && (
                    <div className="mb-4 p-3 rounded-lg bg-och-mint/10 border border-och-mint/30 text-och-mint text-sm">
                      {rbacSuccess}
                    </div>
                  )}
                  {rbacLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-och-mint"></div>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-och-steel/20">
                            <th className="text-left p-3 text-och-steel text-sm font-semibold">Name</th>
                            <th className="text-left p-3 text-och-steel text-sm font-semibold">Display Name</th>
                            <th className="text-left p-3 text-och-steel text-sm font-semibold">Description</th>
                            <th className="text-left p-3 text-och-steel text-sm font-semibold">Permissions</th>
                            <th className="text-left p-3 text-och-steel text-sm font-semibold">System Role</th>
                            <th className="text-left p-3 text-och-steel text-sm font-semibold">Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {apiRoles.map((role) => (
                            <tr key={role.id} className="border-b border-och-steel/10 hover:bg-och-midnight/50">
                              <td className="p-3 text-white font-mono text-sm">{role.name}</td>
                              <td className="p-3 text-white">{role.display_name}</td>
                              <td className="p-3 text-och-steel text-sm">{role.description || '—'}</td>
                              <td className="p-3 text-och-steel text-sm">{role.permissions?.length || 0}</td>
                              <td className="p-3">
                                {role.is_system_role ? (
                                  <Badge variant="mint">System</Badge>
                                ) : (
                                  <Badge variant="outline">Custom</Badge>
                                )}
                              </td>
                              <td className="p-3">
                                <div className="flex gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setRoleToEdit(role)
                                      setEditRoleForm({
                                        display_name: role.display_name,
                                        description: role.description || '',
                                      })
                                      setShowEditRoleModal(true)
                                    }}
                                  >
                                    Edit
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setRoleToDelete(role)
                                      setShowDeleteRoleModal(true)
                                    }}
                                    className="text-och-orange border-och-orange/50 hover:bg-och-orange/10"
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
            )}

            {/* Permissions Tab */}
            {activeTab === 'permissions' && (
              <>
              <Card>
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-white mb-2">Manage Roles & Permissions</h2>
                  <p className="text-och-steel text-sm mb-6">
                    Assign permissions to each role. Changes apply immediately; users get access based on their role&apos;s permissions.
                  </p>
                  {rbacError && (
                    <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                      {rbacError}
                    </div>
                  )}
                  {rbacSuccess && (
                    <div className="mb-4 p-3 rounded-lg bg-och-mint/10 border border-och-mint/30 text-och-mint text-sm">
                      {rbacSuccess}
                    </div>
                  )}
                  {!rbacLoading && apiPermissions.length === 0 && apiRoles.length > 0 && (
                    <div className="mb-4 p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm">
                      <p className="font-medium">No permissions in the database.</p>
                      <p className="mt-1">Run the backend seed to create permissions and assign them to roles:</p>
                      <code className="mt-2 block p-2 bg-och-midnight rounded text-xs">python manage.py seed_roles_permissions</code>
                      <p className="mt-2 text-och-steel">Run this in the backend container or from <code>backend/django_app</code>.</p>
                    </div>
                  )}
                  {!rbacLoading && selectedRoleId != null && permissionIdsForRole.length === 0 && apiPermissions.length > 0 && (
                    <div className="mb-4 p-3 rounded-lg bg-och-steel/20 border border-och-steel/30 text-och-steel text-sm">
                      This role has no permissions assigned. Select permissions below and click Save, or run the backend seed to assign defaults: <code className="text-xs">python manage.py seed_roles_permissions</code>
                    </div>
                  )}
                  {rbacLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-och-mint"></div>
                    </div>
                  ) : (
                    <>
                      <div className="mb-6">
                        <label className="block text-sm font-medium text-och-steel mb-2">Select role</label>
                        <select
                          value={selectedRoleId ?? ''}
                          onChange={(e) => setSelectedRoleId(e.target.value ? Number(e.target.value) : null)}
                          className="w-full max-w-xs bg-och-midnight border border-och-steel/30 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-och-gold focus:border-transparent"
                        >
                          <option value="">— Select role —</option>
                          {apiRoles.map((r) => (
                            <option key={r.id} value={r.id}>
                              {r.display_name} ({r.name})
                            </option>
                          ))}
                        </select>
                      </div>
                      {selectedRoleId != null && (
                        <>
                          <div className="mb-4 flex flex-wrap gap-2 items-center justify-between">
                            <span className="text-och-steel text-sm">
                              {permissionIdsForRole.length} permission(s) selected
                            </span>
                            <Button
                              onClick={saveRolePermissions}
                              disabled={rbacSaving}
                            >
                              {rbacSaving ? 'Saving…' : 'Save permissions'}
                            </Button>
                          </div>
                          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                            {Object.entries(permissionsByResource).map(([resource, perms]) => {
                              const permIds = perms.map((p) => p.id)
                              const selectedInSection = permIds.filter((id) => permissionIdsForRole.includes(id)).length
                              return (
                              <div
                                key={resource}
                                className="p-4 rounded-lg border border-och-steel/20 bg-och-midnight/50"
                              >
                                <div className="flex items-center justify-between mb-3">
                                  <h4 className="text-white font-semibold capitalize">{resource.replace(/_/g, ' ')}</h4>
                                  <div className="flex items-center gap-2">
                                    {selectedInSection < perms.length && (
                                      <button
                                        type="button"
                                        onClick={() => selectSectionPermissions(permIds)}
                                        className="text-xs text-och-steel hover:text-och-mint transition-colors"
                                      >
                                        Select all
                                      </button>
                                    )}
                                    {selectedInSection > 0 && (
                                      <button
                                        type="button"
                                        onClick={() => clearSectionPermissions(permIds)}
                                        className="text-xs text-och-steel hover:text-och-orange transition-colors"
                                      >
                                        Deselect all
                                      </button>
                                    )}
                                  </div>
                                </div>
                                <ul className="space-y-2">
                                  {perms.map((p) => (
                                    <li key={p.id} className="flex items-center gap-2">
                                      <input
                                        type="checkbox"
                                        id={`perm-${p.id}`}
                                        checked={permissionIdsForRole.includes(p.id)}
                                        onChange={() => togglePermission(p.id)}
                                        className="h-4 w-4 rounded border-och-steel/50 bg-och-midnight text-och-gold focus:ring-och-gold"
                                      />
                                      <label htmlFor={`perm-${p.id}`} className="text-sm text-och-steel cursor-pointer">
                                        {p.action}
                                      </label>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )})}
                          </div>
                        </>
                      )}
                    </>
                  )}
                </div>
              </Card>

              <Card>
                <div className="p-6">
                  <h2 className="text-2xl font-bold text-white mb-4">RBAC Overview</h2>
                  <p className="text-och-steel text-sm mb-6">
                    Authorization is governed by RBAC. Roles define permissions that grant access to resources and actions.
                  </p>
                  
                  <div className="space-y-4">
                    <div className="p-4 bg-och-midnight/50 rounded-lg border border-och-steel/20">
                      <h3 className="text-white font-semibold mb-2">RBAC Mechanism</h3>
                      <p className="text-och-steel text-sm mb-3">
                        Users are assigned roles, and roles have associated permissions. Access is granted based on role membership.
                      </p>
                      <div className="flex items-center gap-2">
                        <Badge variant="mint">Active</Badge>
                        <span className="text-white text-sm">RBAC is enforced at the API Gateway</span>
                      </div>
                    </div>

                    <div className="p-4 bg-och-midnight/50 rounded-lg border border-och-steel/20">
                      <h3 className="text-white font-semibold mb-2">Role and Scope Granularity</h3>
                      <p className="text-och-steel text-sm mb-3">
                        Policies are evaluated based on attributes like cohort_id, track_key, org_id, and consent_scopes[].
                      </p>
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="mint">Yes</Badge>
                          <span className="text-white text-sm">Cohort-scoped roles (cohort_id)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="mint">Yes</Badge>
                          <span className="text-white text-sm">Track-scoped roles (track_key)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="mint">Yes</Badge>
                          <span className="text-white text-sm">Organization-scoped roles (org_id)</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="mint">Yes</Badge>
                          <span className="text-white text-sm">Consent-based access (consent_scopes[])</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 bg-och-midnight/50 rounded-lg border border-och-steel/20">
                      <h3 className="text-white font-semibold mb-2">Example: Program Director Access</h3>
                      <p className="text-och-steel text-sm mb-2">
                        A Program Director can list cohort portfolios only if the user's cohort_id matches the request's cohort_id.
                      </p>
                      <div className="bg-och-midnight p-3 rounded text-xs font-mono text-och-steel">
                        IF user.role == 'program_director'<br />
                        AND user.cohort_id == request.cohort_id<br />
                        THEN allow LIST portfolios
                      </div>
                    </div>
                  </div>
                </div>
              </Card>
              </>
            )}
          </div>

          {/* Edit Role Modal */}
          {showEditRoleModal && roleToEdit && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-white">Edit Role</h2>
                    <button onClick={() => !isUpdatingRole && setShowEditRoleModal(false)} disabled={isUpdatingRole} className="text-och-steel hover:text-white">
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                  </div>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">Role Name (internal)</label>
                      <input type="text" value={roleToEdit.name} disabled className="w-full px-4 py-2 bg-och-midnight/30 border border-och-steel/20 rounded-lg text-och-steel cursor-not-allowed" />
                      <p className="text-xs text-och-steel mt-1">Role name cannot be changed</p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">Display Name *</label>
                      <input type="text" value={editRoleForm.display_name} onChange={(e) => setEditRoleForm({ ...editRoleForm, display_name: e.target.value })} className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-gold" />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">Description (optional)</label>
                      <textarea value={editRoleForm.description} onChange={(e) => setEditRoleForm({ ...editRoleForm, description: e.target.value })} rows={3} className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-gold" />
                    </div>
                  </div>
                  <div className="flex gap-2 justify-end mt-6">
                    <Button variant="outline" onClick={() => !isUpdatingRole && setShowEditRoleModal(false)} disabled={isUpdatingRole}>Cancel</Button>
                    <Button variant="defender" onClick={handleEditRole} disabled={isUpdatingRole || !editRoleForm.display_name}>{isUpdatingRole ? 'Updating...' : 'Update Role'}</Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Delete Role Modal */}
          {showDeleteRoleModal && roleToDelete && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Delete Role</h3>
                  <p className="text-och-steel mb-6">Are you sure you want to delete the role <span className="text-white font-medium">{roleToDelete.display_name}</span>? This action cannot be undone.</p>
                  <div className="flex gap-2 justify-end">
                    <Button variant="outline" onClick={() => { setShowDeleteRoleModal(false); setRoleToDelete(null); }} disabled={isDeletingRole}>Cancel</Button>
                    <Button variant="outline" onClick={handleDeleteRole} disabled={isDeletingRole} className="bg-och-orange/20 text-och-orange border-och-orange/50 hover:bg-och-orange/30">{isDeletingRole ? 'Deleting...' : 'Delete'}</Button>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Add Role Modal */}
          {showAddRoleModal && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
              <Card className="w-full max-w-md">
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-white">Add New Role</h2>
                    <button
                      onClick={() => !isCreatingRole && setShowAddRoleModal(false)}
                      disabled={isCreatingRole}
                      className="text-och-steel hover:text-white"
                    >
                      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Role Name (internal) *
                      </label>
                      <input
                        type="text"
                        value={newRoleForm.name}
                        onChange={(e) => setNewRoleForm({ ...newRoleForm, name: e.target.value })}
                        placeholder="e.g., content_manager"
                        className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-gold"
                      />
                      <p className="text-xs text-och-steel mt-1">Lowercase, use underscores instead of spaces</p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Display Name *
                      </label>
                      <input
                        type="text"
                        value={newRoleForm.display_name}
                        onChange={(e) => setNewRoleForm({ ...newRoleForm, display_name: e.target.value })}
                        placeholder="e.g., Content Manager"
                        className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-gold"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-white mb-2">
                        Description (optional)
                      </label>
                      <textarea
                        value={newRoleForm.description}
                        onChange={(e) => setNewRoleForm({ ...newRoleForm, description: e.target.value })}
                        placeholder="Describe the role's purpose and responsibilities"
                        rows={3}
                        className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-gold"
                      />
                    </div>
                  </div>
                  
                  <div className="flex gap-2 justify-end mt-6">
                    <Button
                      variant="outline"
                      onClick={() => !isCreatingRole && setShowAddRoleModal(false)}
                      disabled={isCreatingRole}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="defender"
                      onClick={handleCreateRole}
                      disabled={isCreatingRole || !newRoleForm.name || !newRoleForm.display_name}
                    >
                      {isCreatingRole ? 'Creating...' : 'Create Role'}
                    </Button>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </div>
      </AdminLayout>
    </RouteGuard>
  )
}
