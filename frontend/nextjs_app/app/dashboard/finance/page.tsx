/**
 * Financial Dashboard
 * Personal wallet, invoices, and student subscription for the logged-in user.
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
  /** OCH student subscription (same source as /dashboard/student/subscription) */
  subscription: {
    plan_name: string
    plan_display_name: string
    tier: string
    status: string
    billing_interval: string
    current_period_start: string | null
    current_period_end: string | null
    price_monthly_kes: number
  } | null
}

export default function FinancialDashboardPage() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('30d')

  useEffect(() => {
    loadDashboardData()
  }, [timeRange])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const response = await apiGateway.get(`/finance/dashboard/?range=${encodeURIComponent(timeRange)}`)
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

  const formatKes = (amount: number | undefined | null) =>
    `KSh ${Number(amount || 0).toLocaleString()}`

  const invoiceHealth = (dashboardData?.invoices.overdue || 0) > 0 ? 'Attention' : 'Good'
  const walletHealth = (dashboardData?.wallet.balance || 0) > 0 ? 'Funded' : 'Low'
  const creditHealth = (dashboardData?.credits.active_balance || 0) > 0 ? 'Available' : 'Empty'
  const cashFlowHealth =
    (dashboardData?.recent_transactions || []).filter((t) => t.type === 'credit').length >=
    (dashboardData?.recent_transactions || []).filter((t) => t.type === 'debit').length
      ? 'Positive'
      : 'Negative'

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
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight flex">
        <FinanceNavigation />
        <div className="flex-1 lg:ml-64">
          <div className="px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
              <div className="flex justify-between items-center">
                <div>
                  <h1 className="text-h1 font-bold text-white">Finance Dashboard</h1>
                </div>
                <div className="flex gap-2">
                  <select
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                    className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  >
                    <option value="7d">7 days</option>
                    <option value="30d">30 days</option>
                    <option value="90d">90 days</option>
                    <option value="1y">1 year</option>
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
                    <p className="text-sm font-medium text-och-steel mb-1">Wallet</p>
                    <p className="text-2xl font-bold text-white">
                      {formatKes(dashboardData?.wallet.balance)}
                    </p>
                    <p className="text-xs text-och-steel mt-1">KES</p>
                  </div>
                  <Wallet className="h-8 w-8 text-och-mint" />
                </div>
              </Card>

              <Card className="p-6 bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/40">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-och-steel mb-1">Credits</p>
                    <p className="text-2xl font-bold text-white">
                      {formatKes(dashboardData?.credits.active_balance)}
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
                    <p className="text-xs text-och-steel mt-1">{invoiceHealth}</p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-och-orange" />
                </div>
              </Card>
            </div>

            {/* OCH subscription — same plan/renewal as student subscription page */}
            <Card className="p-6 mb-8 bg-gradient-to-br from-och-mint/15 to-transparent border border-och-mint/30">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-lg bg-och-mint/20">
                    <CreditCard className="h-8 w-8 text-och-mint" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-och-steel mb-1">Subscription</p>
                    {dashboardData?.subscription ? (
                      <>
                        <p className="text-2xl font-bold text-white">
                          {dashboardData.subscription.plan_display_name}
                        </p>
                        <p className="text-xs text-och-steel mt-1 font-mono">{dashboardData.subscription.plan_name}</p>
                        <div className="flex flex-wrap gap-2 mt-3">
                          <Badge variant="mint">{dashboardData.subscription.status}</Badge>
                          <Badge variant="steel">{dashboardData.subscription.billing_interval}</Badge>
                          <Badge variant="outline" className="border-och-steel/40 text-och-steel">
                            {dashboardData.subscription.tier}
                          </Badge>
                        </div>
                      </>
                    ) : (
                      <p className="text-och-steel">No active subscription for this login.</p>
                    )}
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 lg:text-right">
                  {dashboardData?.subscription ? (
                    <>
                      <div>
                        <p className="text-sm text-och-steel">Next renewal</p>
                        <p className="text-lg font-semibold text-white">
                          {dashboardData.subscription.current_period_end
                            ? new Date(dashboardData.subscription.current_period_end).toLocaleDateString()
                            : '—'}
                        </p>
                        <p className="text-xs text-och-steel mt-1">
                          {formatKes(dashboardData.subscription.price_monthly_kes)} / month
                        </p>
                      </div>
                      <Link href="/dashboard/student/subscription">
                        <Button variant="mint" size="sm">
                          Manage subscription
                        </Button>
                      </Link>
                    </>
                  ) : (
                    <Link href="/dashboard/student/subscription">
                      <Button variant="outline" size="sm">
                        View plans
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            </Card>

            {/* Quick Actions */}
            <Card className="p-6 mb-8 bg-och-midnight border border-och-steel/20">
              <h2 className="text-h2 font-semibold text-white mb-4">Actions</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Link href="/dashboard/finance/wallet">
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-2">
                    <Wallet className="h-6 w-6" />
                    <span className="text-sm">Wallet</span>
                  </Button>
                </Link>
                
                <Link href="/dashboard/finance/billing">
                  <Button variant="outline" className="w-full h-20 flex flex-col gap-2">
                    <FileText className="h-6 w-6" />
                    <span className="text-sm">Invoices</span>
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
                    <span className="text-sm">Tax</span>
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
                            {transaction.type === 'credit' ? '+' : '-'}{formatKes(transaction.amount)}
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

              {/* Health */}
              <Card className="p-6 bg-och-midnight border border-och-steel/20">
                <h2 className="text-h2 font-semibold text-white mb-4">Health</h2>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-och-savanna-green" />
                      <span className="text-white">Wallet Status</span>
                    </div>
                    <Badge variant={walletHealth === 'Funded' ? 'mint' : 'gold'}>{walletHealth}</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-och-defender" />
                      <span className="text-white">Invoice Status</span>
                    </div>
                    <Badge variant={dashboardData?.invoices.overdue ? 'orange' : 'mint'}>{invoiceHealth}</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-5 w-5 text-och-gold" />
                      <span className="text-white">Credit Utilization</span>
                    </div>
                    <Badge variant={creditHealth === 'Available' ? 'gold' : 'steel'}>{creditHealth}</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-och-steel/10 rounded-lg">
                    <div className="flex items-center gap-3">
                      <TrendingUp className="h-5 w-5 text-och-mint" />
                      <span className="text-white">Cash Flow</span>
                    </div>
                    <Badge variant={cashFlowHealth === 'Positive' ? 'mint' : 'orange'}>{cashFlowHealth}</Badge>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </RouteGuard>
  )
}