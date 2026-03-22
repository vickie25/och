/**
 * Mentor Payout Management Page
 * Manage mentor compensation and payouts
 */

'use client'

import { useState, useEffect } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { financeService, type MentorPayout } from '@/services/financeService'
import { 
  Users, 
  DollarSign,
  Calendar,
  CheckCircle,
  Clock,
  XCircle,
  Filter,
  Download,
  Search
} from 'lucide-react'

type TabType = 'all' | 'pending' | 'approved' | 'paid'

export default function MentorPayoutsPage() {
  const [payouts, setPayouts] = useState<MentorPayout[]>([])
  const [activeTab, setActiveTab] = useState<TabType>('all')
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPeriod, setSelectedPeriod] = useState('all')

  useEffect(() => {
    loadPayouts()
  }, [])

  const loadPayouts = async () => {
    try {
      setLoading(true)
      const data = await financeService.getMentorPayouts()
      setPayouts(data)
    } catch (error) {
      console.error('Failed to load mentor payouts:', error)
      setPayouts([])
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id: string) => {
    try {
      await financeService.approvePayout(id)
      await loadPayouts()
    } catch (error) {
      console.error('Failed to approve payout:', error)
    }
  }

  const handleMarkPaid = async (id: string) => {
    try {
      await financeService.markPayoutPaid(id)
      await loadPayouts()
    } catch (error) {
      console.error('Failed to mark payout as paid:', error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid': return 'mint'
      case 'approved': return 'defender'
      case 'pending': return 'gold'
      case 'rejected': return 'orange'
      default: return 'steel'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'paid': return <CheckCircle className="h-4 w-4" />
      case 'approved': return <CheckCircle className="h-4 w-4" />
      case 'pending': return <Clock className="h-4 w-4" />
      case 'rejected': return <XCircle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const filteredPayouts = payouts.filter(payout => {
    const matchesTab = activeTab === 'all' || payout.status === activeTab
    const matchesSearch = 
      payout.mentor_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payout.mentor_email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (payout.cohort_name || '').toLowerCase().includes(searchTerm.toLowerCase())
    
    return matchesTab && matchesSearch
  })

  const stats = {
    total: payouts.length,
    pending: payouts.filter(p => p.status === 'pending').length,
    approved: payouts.filter(p => p.status === 'approved').length,
    paid: payouts.filter(p => p.status === 'paid').length,
    totalAmount: payouts.reduce((sum, p) => sum + p.amount, 0),
    pendingAmount: payouts.filter(p => p.status === 'pending').reduce((sum, p) => sum + p.amount, 0)
  }

  if (loading) {
    return (
      <RouteGuard requiredRoles={['finance', 'admin']}>
        <div className="min-h-screen bg-och-midnight flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
            <p className="text-och-steel text-sm">Loading payouts...</p>
          </div>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-h1 font-bold text-white">Mentor Payouts</h1>
                <p className="mt-1 body-m text-och-steel">
                  Manage mentor compensation and payouts
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Button>
                  Generate Payouts
                </Button>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <Card className="p-4 bg-och-midnight border border-och-steel/20">
              <div className="flex items-center gap-3 mb-2">
                <Users className="h-5 w-5 text-och-defender" />
                <p className="font-medium text-white">Total Payouts</p>
              </div>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
              <p className="text-sm text-och-steel">
                ${stats.totalAmount.toLocaleString()}
              </p>
            </Card>

            <Card className="p-4 bg-och-gold/10 border border-och-gold/30">
              <div className="flex items-center gap-3 mb-2">
                <Clock className="h-5 w-5 text-och-gold" />
                <p className="font-medium text-white">Pending</p>
              </div>
              <p className="text-2xl font-bold text-white">{stats.pending}</p>
              <p className="text-sm text-och-steel">
                ${stats.pendingAmount.toLocaleString()}
              </p>
            </Card>

            <Card className="p-4 bg-och-defender/10 border border-och-defender/30">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="h-5 w-5 text-och-defender" />
                <p className="font-medium text-white">Approved</p>
              </div>
              <p className="text-2xl font-bold text-white">{stats.approved}</p>
            </Card>

            <Card className="p-4 bg-och-mint/10 border border-och-mint/30">
              <div className="flex items-center gap-3 mb-2">
                <DollarSign className="h-5 w-5 text-och-mint" />
                <p className="font-medium text-white">Paid</p>
              </div>
              <p className="text-2xl font-bold text-white">{stats.paid}</p>
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
                    placeholder="Search mentors..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:ring-2 focus:ring-och-mint"
                  />
                </div>
              </div>

              <select
                value={selectedPeriod}
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
              >
                <option value="all">All Periods</option>
                <option value="current">Current Month</option>
                <option value="last">Last Month</option>
                <option value="quarter">This Quarter</option>
              </select>
            </div>
          </Card>

          {/* Tabs */}
          <div className="border-b border-och-steel/20 mb-6">
            <nav className="-mb-px flex space-x-8">
              {[
                { key: 'all', label: 'All Payouts', count: stats.total },
                { key: 'pending', label: 'Pending', count: stats.pending },
                { key: 'approved', label: 'Approved', count: stats.approved },
                { key: 'paid', label: 'Paid', count: stats.paid },
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

          {/* Payouts Table */}
          <Card className="p-6 bg-och-midnight border border-och-steel/20">
            {filteredPayouts.length === 0 ? (
              <div className="text-center py-12">
                <Users className="h-12 w-12 mx-auto mb-4 text-och-steel" />
                <p className="body-m text-och-steel mb-2">No payouts found</p>
                <p className="body-s text-och-steel/70">
                  {payouts.length === 0
                    ? 'Generate payouts to get started'
                    : `No payouts match the ${activeTab} filter`}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-och-steel/20">
                  <thead className="bg-och-midnight/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Mentor
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Cohort
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Mode
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Period
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Amount
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Method
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Created
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                    {filteredPayouts.map((payout) => (
                      <tr key={payout.id} className="hover:bg-och-steel/5">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-3">
                            <Users className="h-4 w-4 text-och-steel" />
                            <div>
                              <p className="text-sm font-medium text-white">
                                {payout.mentor_name}
                              </p>
                              <p className="text-xs text-och-steel">
                                {payout.mentor_email}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel max-w-[160px] truncate">
                          {payout.cohort_name || '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="steel" className="capitalize">
                            {payout.compensation_mode || 'paid'}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {new Date(payout.period_start).toLocaleDateString()} -{' '}
                            {new Date(payout.period_end).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">
                          ${payout.amount.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant="steel">
                            {payout.payout_method.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            {getStatusIcon(payout.status)}
                            <Badge variant={getStatusColor(payout.status)}>
                              {payout.status}
                            </Badge>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                          {new Date(payout.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex gap-2">
                            {payout.status === 'pending' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleApprove(payout.id)}
                                className="text-och-mint hover:text-och-mint"
                              >
                                Approve
                              </Button>
                            )}
                            {payout.status === 'approved' && (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleMarkPaid(payout.id)}
                                className="text-och-savanna-green hover:text-och-savanna-green"
                              >
                                Mark Paid
                              </Button>
                            )}
                            <Button variant="ghost" size="sm">
                              View
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
    </RouteGuard>
  )
}