/**
 * Financial Dashboard
 * Comprehensive overview of all financial operations
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
  DollarSign, 
  Wallet,
  FileText,
  CreditCard,
  TrendingUp,
  TrendingDown,
  Users,
  Building2,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowUpRight,
  ArrowDownLeft
} from 'lucide-react'
import Link from 'next/link'

type DashboardData = {
  wallet: {
    balance: number
    currency: string
    last_transaction_at: string | null
  }
  credits: {
    active_balance: number
    total_credits: number
  }
  invoices: {
    pending: number
    overdue: number
    total: number
  }
  recent_transactions: Array<{
    id: string
    type: 'credit' | 'debit'
    amount: number
    description: string
    created_at: string
  }>
}

export default function FinancialDashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('30d')

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const response = await apiGateway.get('/finance/dashboard/')
      setDashboardData(response)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTransactionIcon = (type: string) => {
    return type === 'credit' ? 
      <ArrowUpRight className="h-4 w-4 text-och-savanna-green" /> :
      <ArrowDownLeft className="h-4 w-4 text-och-orange" />
  }

  if (loading) {
    return (
      <RouteGuard>
        <div className="min-h-screen bg-och-midnight flex">
          <FinanceNavigation />
          <div className="flex-1 lg:ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
              <p className="text-och-steel text-sm">Loading dashboard...</p>
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
                  <h1 className="text-h1 font-bold text-white">Financial Dashboard</h1>
                  <p className="mt-1 body-m text-och-steel">
                    Comprehensive overview of all financial operations
                  </p>
                </div>
                <div className="flex gap-2">
                  <select
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                    className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  >
                    <option value="7d">Last 7 days</option>
                    <option value="30d">Last 30 days</option>
                    <option value="90d">Last 90 days</option>
                    <option value="1y">Last year</option>
                  </select>
                  <Button onClick={loadDashboardData}>
                    Refresh
                  </Button>
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card className="p-6 bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-och-steel mb-1">Wallet Balance</p>
                    <p className="text-2xl font-bold text-white">
                      ${dashboardData?.wallet.balance?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-xs text-och-steel mt-1">
                      {dashboardData?.wallet.currency || 'USD'}
                    </p>
                  </div>
                  <Wallet className="h-8 w-8 text-och-mint" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/40">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-och-steel mb-1">Active Credits</p>
                    <p className="text-2xl font-bold text-white">
                      ${dashboardData?.credits.active_balance?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-xs text-och-steel mt-1">
                      {dashboardData?.credits.total_credits || 0} credits
                    </p>
                  </div>
                  <CreditCard className="h-8 w-8 text-och-defender" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/40">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-och-steel mb-1">Pending Invoices</p>
                    <p className="text-2xl font-bold text-white">
                      {dashboardData?.invoices.pending || 0}
                    </p>
                    <p className="text-xs text-och-steel mt-1">
                      {dashboardData?.invoices.total || 0} total
                    </p>
                  </div>
                  <FileText className="h-8 w-8 text-och-gold" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-och-orange/20 to-och-orange/5 border-och-orange/40">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-och-steel mb-1">Overdue Invoices</p>
                    <p className="text-2xl font-bold text-white">
                      {dashboardData?.invoices.overdue || 0}
                    </p>
                    <p className="text-xs text-och-steel mt-1">
                      Requires attention
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-och-orange" />
                </div>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="p-6 mb-8 bg-och-midnight border border-och-steel/20">
              <h2 className="text-h2 font-semibold text-white mb-4">Quick Actions</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href="/dashboard/finance/wallet">
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-2">
                    <Wallet className="h-6 w-6" />
                    <span className="text-sm">Manage Wallet</span>
                  </Button>
                </Link>
                
                <Link href="/dashboard/finance/billing">
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-2">
                    <FileText className="h-6 w-6" />
                    <span className="text-sm">View Invoices</span>
                  </Button>
                </Link>
                
                <Link href="/dashboard/finance/contracts">
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-2">
                    <Building2 className="h-6 w-6" />
                    <span className="text-sm">Contracts</span>
                  </Button>
                </Link>
                
                <Link href="/dashboard/finance/tax">
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-2">
                    <DollarSign className="h-6 w-6" />
                    <span className="text-sm">Tax Rates</span>
                  </Button>
                </Link>
              </div>
            </Card>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Recent Transactions */}
              <Card className="p-6 bg-och-midnight border border-och-steel/20">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-h2 font-semibold text-white">Recent Transactions</h2>
                  <Link href="/dashboard/finance/wallet">
                    <Button variant="ghost" size="sm">
                      View All
                    </Button>
                  </Link>
                </div>
                
                {!dashboardData?.recent_transactions?.length ? (
                  <div className="text-center py-8">
                    <Clock className="h-12 w-12 mx-auto mb-2 text-och-steel" />
                    <p className="body-m text-och-steel">No recent transactions</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {dashboardData.recent_transactions.slice(0, 5).map((transaction) => (
                      <div 
                        key={transaction.id}
                        className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg border border-och-steel/20"
                      >
                        <div className="flex items-center gap-3">
                          {getTransactionIcon(transaction.type)}
                          <div>
                            <p className="text-white font-medium text-sm">
                              {transaction.description}
                            </p>
                            <p className="text-xs text-och-steel">
                              {new Date(transaction.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-medium text-sm ${
                            transaction.type === 'credit' ? 'text-och-savanna-green' : 'text-och-orange'
                          }`}>
                            {transaction.type === 'credit' ? '+' : '-'}${Number(transaction.amount || 0).toFixed(2)}
                          </p>
                          <Badge variant={transaction.type === 'credit' ? 'mint' : 'orange'} className="text-xs">
                            {transaction.type}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* Financial Health */}
              <Card className="p-6 bg-och-midnight border border-och-steel/20">
                <h2 className="text-h2 font-semibold text-white mb-4">Financial Health</h2>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-och-savanna-green" />
                      <span className="text-white">Wallet Status</span>
                    </div>
                    <Badge variant="mint">Healthy</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-och-defender" />
                      <span className="text-white">Invoice Status</span>
                    </div>
                    <Badge variant={dashboardData?.invoices.overdue ? 'orange' : 'mint'}>
                      {dashboardData?.invoices.overdue ? 'Attention Needed' : 'Good'}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-5 w-5 text-och-gold" />
                      <span className="text-white">Credit Utilization</span>
                    </div>
                    <Badge variant="gold">Optimal</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <TrendingUp className="h-5 w-5 text-och-mint" />
                      <span className="text-white">Cash Flow</span>
                    </div>
                    <Badge variant="mint">Positive</Badge>
                  </div>
                </div>
              </Card>
            </div>

            {/* System Status */}
            <Card className="p-6 mt-8 bg-och-midnight border border-och-steel/20">
              <h2 className="text-h2 font-semibold text-white mb-4">System Status</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center gap-3 p-3 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                  <CheckCircle className="h-5 w-5 text-och-savanna-green" />
                  <div>
                    <p className="text-white font-medium">Payment Gateway</p>
                    <p className="text-xs text-och-steel">All systems operational</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                  <CheckCircle className="h-5 w-5 text-och-savanna-green" />
                  <div>
                    <p className="text-white font-medium">Billing Engine</p>
                    <p className="text-xs text-och-steel">Processing normally</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                  <CheckCircle className="h-5 w-5 text-och-savanna-green" />
                  <div>
                    <p className="text-white font-medium">Tax Calculation</p>
                    <p className="text-xs text-och-steel">Up to date</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </RouteGuard>
  )
}