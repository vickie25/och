/**
 * Contract Management Page
 * Manage institution and employer contracts
 */

'use client'

import { useState, useEffect } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { FinanceNavigation } from '@/components/navigation/FinanceNavigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
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
  organization_name: string
  type: 'institution' | 'employer'
  start_date: string
  end_date: string
  status: 'proposal' | 'negotiation' | 'signed' | 'active' | 'renewal' | 'terminated'
  total_value: number
  payment_terms: string
  auto_renew: boolean
  renewal_notice_days: number
  is_active: boolean
  days_until_expiry: number
  created_at: string
  updated_at: string
}

type TabType = 'all' | 'active' | 'expiring' | 'proposals'

export default function ContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [activeTab, setActiveTab] = useState<TabType>('all')
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    loadContracts()
  }, [])

  const loadContracts = async () => {
    try {
      setLoading(true)
      const response = await apiGateway.get('/finance/contracts/')
      setContracts(Array.isArray(response) ? response : response.results || [])
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
        return contract.status === 'active'
      case 'expiring':
        return contract.is_active && contract.days_until_expiry <= 30
      case 'proposals':
        return contract.status === 'proposal' || contract.status === 'negotiation'
      default:
        return true
    }
  })

  const stats = {
    total: contracts.length,
    active: contracts.filter(c => c.status === 'active').length,
    expiring: contracts.filter(c => c.is_active && c.days_until_expiry <= 30).length,
    proposals: contracts.filter(c => c.status === 'proposal' || c.status === 'negotiation').length,
    totalValue: contracts.reduce((sum, c) => sum + c.total_value, 0)
  }

  if (loading) {
    return (
      <RouteGuard>
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
    <RouteGuard>
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
                  ${stats.totalValue.toLocaleString()}
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
                          Value
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Duration
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Status
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
                            ${contract.total_value.toLocaleString()}
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
                            <div className="flex gap-2">
                              <Button variant="ghost" size="sm">
                                View
                              </Button>
                              <Button variant="ghost" size="sm">
                                Edit
                              </Button>
                            </div>
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

      {/* Create Contract Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-h3 font-semibold text-white mb-6">Create New Contract</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    Organization
                  </label>
                  <select className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint">
                    <option value="">Select organization...</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    Contract Type
                  </label>
                  <select className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint">
                    <option value="institution">Institution</option>
                    <option value="employer">Employer</option>
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
                    className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-och-steel mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Contract Value (USD)
                </label>
                <input
                  type="number"
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Payment Terms
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  placeholder="Net 30"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="auto_renew"
                  className="rounded border-och-steel/20 bg-och-steel/10 text-och-mint focus:ring-och-mint"
                />
                <label htmlFor="auto_renew" className="text-sm text-och-steel">
                  Auto-renew contract
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button className="flex-1 bg-och-mint hover:bg-och-mint/80">
                  Create Contract
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </RouteGuard>
  )
}