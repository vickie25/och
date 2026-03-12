/**
 * Tax Management Page
 * Manage tax rates for multi-region compliance
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
  Calculator, 
  Plus,
  Globe,
  MapPin,
  Percent,
  Edit,
  Trash2,
  Search
} from 'lucide-react'

type TaxRate = {
  id: string
  country: string
  region: string
  rate: number
  type: 'VAT' | 'GST' | 'sales_tax'
  is_active: boolean
  effective_date: string
  created_at: string
}

export default function TaxPage() {
  const [taxRates, setTaxRates] = useState<TaxRate[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingTax, setEditingTax] = useState<TaxRate | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState<string>('all')
  const [filterActive, setFilterActive] = useState<string>('all')

  const [formData, setFormData] = useState({
    country: '',
    region: '',
    rate: '',
    type: 'VAT' as const,
    is_active: true,
    effective_date: new Date().toISOString().split('T')[0]
  })

  useEffect(() => {
    loadTaxRates()
  }, [])

  const loadTaxRates = async () => {
    try {
      setLoading(true)
      const response = await apiGateway.get('/finance/tax-rates/')
      setTaxRates(Array.isArray(response) ? response : response.results || [])
    } catch (error) {
      console.error('Failed to load tax rates:', error)
      setTaxRates([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const payload = {
        ...formData,
        rate: parseFloat(formData.rate)
      }

      if (editingTax) {
        await apiGateway.put(`/finance/tax-rates/${editingTax.id}/`, payload)
      } else {
        await apiGateway.post('/finance/tax-rates/', payload)
      }

      setShowCreateModal(false)
      setEditingTax(null)
      setFormData({
        country: '',
        region: '',
        rate: '',
        type: 'VAT',
        is_active: true,
        effective_date: new Date().toISOString().split('T')[0]
      })
      await loadTaxRates()
    } catch (error) {
      console.error('Failed to save tax rate:', error)
    }
  }

  const handleEdit = (taxRate: TaxRate) => {
    setEditingTax(taxRate)
    setFormData({
      country: taxRate.country,
      region: taxRate.region,
      rate: taxRate.rate.toString(),
      type: taxRate.type,
      is_active: taxRate.is_active,
      effective_date: taxRate.effective_date
    })
    setShowCreateModal(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this tax rate?')) return

    try {
      await apiGateway.delete(`/finance/tax-rates/${id}/`)
      await loadTaxRates()
    } catch (error) {
      console.error('Failed to delete tax rate:', error)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'VAT': return 'mint'
      case 'GST': return 'defender'
      case 'sales_tax': return 'gold'
      default: return 'steel'
    }
  }

  const filteredTaxRates = taxRates.filter(tax => {
    const matchesSearch = 
      tax.country.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tax.region.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesType = filterType === 'all' || tax.type === filterType
    const matchesActive = filterActive === 'all' || 
      (filterActive === 'active' && tax.is_active) ||
      (filterActive === 'inactive' && !tax.is_active)

    return matchesSearch && matchesType && matchesActive
  })

  const stats = {
    total: taxRates.length,
    active: taxRates.filter(t => t.is_active).length,
    countries: new Set(taxRates.map(t => t.country)).size,
    avgRate: taxRates.length > 0 ? 
      taxRates.reduce((sum, t) => sum + t.rate, 0) / taxRates.length : 0
  }

  if (loading) {
    return (
      <RouteGuard requiredRoles={['finance', 'admin']}>
        <div className="min-h-screen bg-och-midnight flex">
          <FinanceNavigation />
          <div className="flex-1 lg:ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
              <p className="text-och-steel text-sm">Loading tax rates...</p>
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
                  <h1 className="text-h1 font-bold text-white">Tax Management</h1>
                  <p className="mt-1 body-m text-och-steel">
                    Manage tax rates for multi-region compliance
                  </p>
                </div>
                <Button onClick={() => setShowCreateModal(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Tax Rate
                </Button>
              </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <Card className="p-4 bg-och-midnight border border-och-steel/20">
                <div className="flex items-center gap-3 mb-2">
                  <Calculator className="h-5 w-5 text-och-defender" />
                  <p className="font-medium text-white">Total Rates</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </Card>

              <Card className="p-4 bg-och-mint/10 border border-och-mint/30">
                <div className="flex items-center gap-3 mb-2">
                  <Globe className="h-5 w-5 text-och-mint" />
                  <p className="font-medium text-white">Active Rates</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.active}</p>
              </Card>

              <Card className="p-4 bg-och-defender/10 border border-och-defender/30">
                <div className="flex items-center gap-3 mb-2">
                  <MapPin className="h-5 w-5 text-och-defender" />
                  <p className="font-medium text-white">Countries</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.countries}</p>
              </Card>

              <Card className="p-4 bg-och-gold/10 border border-och-gold/30">
                <div className="flex items-center gap-3 mb-2">
                  <Percent className="h-5 w-5 text-och-gold" />
                  <p className="font-medium text-white">Avg Rate</p>
                </div>
                <p className="text-2xl font-bold text-white">{stats.avgRate.toFixed(1)}%</p>
              </Card>
            </div>

            {/* Filters */}
            <Card className="p-4 mb-6 bg-och-midnight border border-och-steel/20">
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-64">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-och-steel" />
                    <input
                      type="text"
                      placeholder="Search by country or region..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:ring-2 focus:ring-och-mint"
                    />
                  </div>
                </div>
                
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                >
                  <option value="all">All Types</option>
                  <option value="VAT">VAT</option>
                  <option value="GST">GST</option>
                  <option value="sales_tax">Sales Tax</option>
                </select>

                <select
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                  className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                >
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </Card>

            {/* Tax Rates Table */}
            <Card className="p-6 bg-och-midnight border border-och-steel/20">
              {filteredTaxRates.length === 0 ? (
                <div className="text-center py-12">
                  <Calculator className="h-12 w-12 mx-auto mb-4 text-och-steel" />
                  <p className="body-m text-och-steel mb-2">No tax rates found</p>
                  <p className="body-s text-och-steel/70">
                    {taxRates.length === 0 
                      ? 'Add your first tax rate to get started'
                      : 'Try adjusting your search or filters'
                    }
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-och-steel/20">
                    <thead className="bg-och-midnight/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Location
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Rate
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Effective Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                      {filteredTaxRates.map((taxRate) => (
                        <tr key={taxRate.id} className="hover:bg-och-steel/5">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-2">
                              <Globe className="h-4 w-4 text-och-steel" />
                              <div>
                                <p className="text-sm font-medium text-white">
                                  {taxRate.country}
                                </p>
                                {taxRate.region && (
                                  <p className="text-xs text-och-steel">
                                    {taxRate.region}
                                  </p>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={getTypeColor(taxRate.type)}>
                              {taxRate.type}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center gap-1">
                              <Percent className="h-3 w-3 text-och-steel" />
                              <span className="text-sm font-medium text-white">
                                {taxRate.rate}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={taxRate.is_active ? 'mint' : 'steel'}>
                              {taxRate.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                            {new Date(taxRate.effective_date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <div className="flex gap-2">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleEdit(taxRate)}
                              >
                                <Edit className="h-3 w-3" />
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => handleDelete(taxRate.id)}
                                className="text-och-orange hover:text-och-orange"
                              >
                                <Trash2 className="h-3 w-3" />
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

      {/* Create/Edit Tax Rate Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-md mx-4">
            <h3 className="text-h3 font-semibold text-white mb-6">
              {editingTax ? 'Edit Tax Rate' : 'Add Tax Rate'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Country Code (ISO 3166-1)
                </label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => setFormData({...formData, country: e.target.value.toUpperCase()})}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  placeholder="US, GB, KE, etc."
                  maxLength={2}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Region/State (Optional)
                </label>
                <input
                  type="text"
                  value={formData.region}
                  onChange={(e) => setFormData({...formData, region: e.target.value})}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  placeholder="California, Ontario, etc."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Tax Type
                </label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value as any})}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  required
                >
                  <option value="VAT">VAT</option>
                  <option value="GST">GST</option>
                  <option value="sales_tax">Sales Tax</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Tax Rate (%)
                </label>
                <input
                  type="number"
                  value={formData.rate}
                  onChange={(e) => setFormData({...formData, rate: e.target.value})}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  placeholder="0.00"
                  min="0"
                  max="100"
                  step="0.01"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Effective Date
                </label>
                <input
                  type="date"
                  value={formData.effective_date}
                  onChange={(e) => setFormData({...formData, effective_date: e.target.value})}
                  className="w-full px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  required
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                  className="rounded border-och-steel/20 bg-och-steel/10 text-och-mint focus:ring-och-mint"
                />
                <label htmlFor="is_active" className="text-sm text-och-steel">
                  Active
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingTax(null)
                    setFormData({
                      country: '',
                      region: '',
                      rate: '',
                      type: 'VAT',
                      is_active: true,
                      effective_date: new Date().toISOString().split('T')[0]
                    })
                  }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1 bg-och-mint hover:bg-och-mint/80">
                  {editingTax ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </RouteGuard>
  )
}