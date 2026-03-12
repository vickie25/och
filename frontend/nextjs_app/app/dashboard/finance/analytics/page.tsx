/**
 * Financial Analytics Dashboard
 * Comprehensive revenue, customer, and performance analytics
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
  TrendingUp, 
  TrendingDown,
  DollarSign,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart,
  Activity,
  Calendar,
  Download,
  RefreshCw
} from 'lucide-react'

type AnalyticsData = {
  period: {
    start_date: string
    end_date: string
    days: number
  }
  revenue: {
    total_revenue: number
    revenue_by_type: Array<{
      type: string
      total: number
      count: number
    }>
    payment_success_rate: number
    total_invoices: number
    total_payments: number
    successful_payments: number
  }
  growth: {
    new_customers: number
    churned_customers: number
    active_customers_start: number
    active_customers_end: number
    growth_rate: number
    churn_rate: number
  }
  revenue_streams: Array<{
    stream_type: string
    total: number
    count: number
  }>
  payment_success: {
    success_rate: number
    total_payments: number
    successful_payments: number
    failed_payments: number
  }
  dunning_recovery: {
    recovery_rate: number
    total_sequences: number
    total_amount: number
    recovered_amount: number
  }
}

type CustomerMetrics = {
  top_customers: Array<{
    customer_id: string
    customer_type: string
    total_revenue: number
    monthly_recurring_revenue: number
    lifetime_value: number
    months_active: number
  }>
  churn_analysis: {
    churned_last_30_days: number
    cohort_data: Array<{
      cohort_month: string
      initial_customers: number
      retention_data: Array<{
        month: number
        active_customers: number
        retention_rate: number
      }>
    }>
  }
}

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [customerMetrics, setCustomerMetrics] = useState<CustomerMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('30')
  const [activeTab, setActiveTab] = useState<'overview' | 'revenue' | 'customers' | 'performance'>('overview')

  useEffect(() => {
    loadAnalyticsData()
  }, [timeRange])

  const loadAnalyticsData = async () => {
    try {
      setLoading(true)
      const [analyticsRes, customerRes] = await Promise.all([
        apiGateway.get(`/finance/analytics/revenue_dashboard/?days=${timeRange}`),
        apiGateway.get('/finance/analytics/customer_metrics/')
      ])
      
      setAnalyticsData(analyticsRes)
      setCustomerMetrics(customerRes)
    } catch (error) {
      console.error('Failed to load analytics data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  const getStatusColor = (value: number, threshold: number, reverse = false) => {
    const isGood = reverse ? value < threshold : value >= threshold
    return isGood ? 'text-och-savanna-green' : 'text-och-orange'
  }

  const getStatusIcon = (value: number, threshold: number, reverse = false) => {
    const isGood = reverse ? value < threshold : value >= threshold
    return isGood ? <CheckCircle className="h-4 w-4 text-och-savanna-green" /> : <AlertTriangle className="h-4 w-4 text-och-orange" />
  }

  if (loading) {
    return (
      <RouteGuard requiredRoles={['finance', 'admin']}>
        <div className="min-h-screen bg-och-midnight flex">
          <FinanceNavigation />
          <div className="flex-1 lg:ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
              <p className="text-och-steel text-sm">Loading analytics...</p>
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
                  <h1 className="text-h1 font-bold text-white">Financial Analytics</h1>
                  <p className="mt-1 body-m text-och-steel">
                    Comprehensive revenue, customer, and performance analytics
                  </p>
                </div>
                <div className="flex gap-2">
                  <select
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                    className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                  >
                    <option value="7">Last 7 days</option>
                    <option value="30">Last 30 days</option>
                    <option value="90">Last 90 days</option>
                    <option value="365">Last year</option>
                  </select>
                  <Button onClick={loadAnalyticsData} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                  <Button>
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-och-steel/20 mb-8">
              <nav className="-mb-px flex space-x-8">
                {[
                  { key: 'overview', label: 'Overview', icon: BarChart3 },
                  { key: 'revenue', label: 'Revenue Streams', icon: DollarSign },
                  { key: 'customers', label: 'Customer Analytics', icon: Users },
                  { key: 'performance', label: 'Performance', icon: Activity }
                ].map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key as any)}
                      className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium body-s flex items-center gap-2 ${
                        activeTab === tab.key
                          ? 'border-och-defender text-och-mint'
                          : 'border-transparent text-och-steel hover:text-white hover:border-och-steel/30'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {tab.label}
                    </button>
                  )
                })}
              </nav>
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && analyticsData && (
              <div className="space-y-8">
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card className="p-6 bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm font-medium text-och-steel mb-1">Total Revenue</p>
                        <p className="text-2xl font-bold text-white">
                          {formatCurrency(analyticsData.revenue.total_revenue)}
                        </p>
                        <p className="text-xs text-och-steel mt-1">
                          {analyticsData.period.days} days
                        </p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-och-mint" />
                    </div>
                  </Card>

                  <Card className="p-6 bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/40">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm font-medium text-och-steel mb-1">Payment Success</p>
                        <p className="text-2xl font-bold text-white">
                          {formatPercentage(analyticsData.payment_success.success_rate)}
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                          {getStatusIcon(analyticsData.payment_success.success_rate, 95)}
                          <p className={`text-xs ${getStatusColor(analyticsData.payment_success.success_rate, 95)}`}>
                            Target: 95%
                          </p>
                        </div>
                      </div>
                      <Target className="h-8 w-8 text-och-defender" />
                    </div>
                  </Card>

                  <Card className="p-6 bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/40">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm font-medium text-och-steel mb-1">Customer Growth</p>
                        <p className="text-2xl font-bold text-white">
                          {formatPercentage(analyticsData.growth.growth_rate)}
                        </p>
                        <p className="text-xs text-och-steel mt-1">
                          +{analyticsData.growth.new_customers} new customers
                        </p>
                      </div>
                      <Users className="h-8 w-8 text-och-gold" />
                    </div>
                  </Card>

                  <Card className="p-6 bg-gradient-to-br from-och-orange/20 to-och-orange/5 border-och-orange/40">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <p className="text-sm font-medium text-och-steel mb-1">Dunning Recovery</p>
                        <p className="text-2xl font-bold text-white">
                          {formatPercentage(analyticsData.dunning_recovery.recovery_rate)}
                        </p>
                        <div className="flex items-center gap-1 mt-1">
                          {getStatusIcon(analyticsData.dunning_recovery.recovery_rate, 80)}
                          <p className={`text-xs ${getStatusColor(analyticsData.dunning_recovery.recovery_rate, 80)}`}>
                            Target: 80%
                          </p>
                        </div>
                      </div>
                      <Activity className="h-8 w-8 text-och-orange" />
                    </div>
                  </Card>
                </div>

                {/* Revenue Breakdown */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-4">Revenue by Type</h3>
                    <div className="space-y-4">
                      {analyticsData.revenue.revenue_by_type.map((item) => (
                        <div key={item.type} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-och-mint rounded-full"></div>
                            <span className="text-white capitalize">{item.type.replace('_', ' ')}</span>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-medium">{formatCurrency(item.total)}</p>
                            <p className="text-xs text-och-steel">{item.count} invoices</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>

                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-4">Revenue Streams</h3>
                    <div className="space-y-4">
                      {analyticsData.revenue_streams.map((stream) => (
                        <div key={stream.stream_type} className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-och-defender rounded-full"></div>
                            <span className="text-white capitalize">{stream.stream_type}</span>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-medium">{formatCurrency(stream.total)}</p>
                            <p className="text-xs text-och-steel">{stream.count} transactions</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {/* Customer Analytics Tab */}
            {activeTab === 'customers' && customerMetrics && (
              <div className="space-y-8">
                {/* Top Customers */}
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-4">Top Customers by Revenue</h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-och-steel/20">
                      <thead className="bg-och-midnight/50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Customer
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Total Revenue
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            MRR
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Lifetime Value
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Active Months
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                        {customerMetrics.top_customers.map((customer, index) => (
                          <tr key={customer.customer_id}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-3">
                                <div className="w-8 h-8 bg-och-mint/20 rounded-full flex items-center justify-center">
                                  <span className="text-och-mint font-medium text-sm">#{index + 1}</span>
                                </div>
                                <span className="text-white text-sm">{customer.customer_id.slice(0, 8)}...</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <Badge variant={customer.customer_type === 'user' ? 'mint' : 'defender'}>
                                {customer.customer_type}
                              </Badge>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-white font-medium">
                              {formatCurrency(customer.total_revenue)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                              {formatCurrency(customer.monthly_recurring_revenue)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                              {formatCurrency(customer.lifetime_value)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                              {customer.months_active} months
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>

                {/* Churn Analysis */}
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-4">Churn Analysis</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm font-medium text-och-steel mb-2">Churned Customers (Last 30 Days)</p>
                      <p className="text-3xl font-bold text-och-orange">
                        {customerMetrics.churn_analysis.churned_last_30_days}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-och-steel mb-2">Cohort Retention</p>
                      <p className="text-sm text-och-steel">
                        Tracking {customerMetrics.churn_analysis.cohort_data.length} cohorts
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Performance Tab */}
            {activeTab === 'performance' && analyticsData && (
              <div className="space-y-8">
                {/* Success Criteria Monitoring */}
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-6">Success Criteria Monitoring</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(analyticsData.payment_success.success_rate, 95)}
                          <div>
                            <p className="text-white font-medium">Payment Success Rate</p>
                            <p className="text-xs text-och-steel">Target: >95%</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-bold ${getStatusColor(analyticsData.payment_success.success_rate, 95)}`}>
                            {formatPercentage(analyticsData.payment_success.success_rate)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(analyticsData.dunning_recovery.recovery_rate, 80)}
                          <div>
                            <p className="text-white font-medium">Dunning Recovery Rate</p>
                            <p className="text-xs text-och-steel">Target: >80%</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-bold ${getStatusColor(analyticsData.dunning_recovery.recovery_rate, 80)}`}>
                            {formatPercentage(analyticsData.dunning_recovery.recovery_rate)}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(analyticsData.growth.churn_rate, 5, true)}
                          <div>
                            <p className="text-white font-medium">Churn Rate</p>
                            <p className="text-xs text-och-steel">Target: <5%</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-bold ${getStatusColor(analyticsData.growth.churn_rate, 5, true)}`}>
                            {formatPercentage(analyticsData.growth.churn_rate)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="p-4 bg-och-steel/10 rounded-lg">
                        <p className="text-white font-medium mb-2">Invoice Processing</p>
                        <p className="text-2xl font-bold text-och-mint">
                          {analyticsData.revenue.total_invoices}
                        </p>
                        <p className="text-xs text-och-steel">Total invoices processed</p>
                      </div>

                      <div className="p-4 bg-och-steel/10 rounded-lg">
                        <p className="text-white font-medium mb-2">Revenue Streams Active</p>
                        <p className="text-2xl font-bold text-och-defender">
                          {analyticsData.revenue_streams.length}
                        </p>
                        <p className="text-xs text-och-steel">Out of 4 target streams</p>
                      </div>

                      <div className="p-4 bg-och-steel/10 rounded-lg">
                        <p className="text-white font-medium mb-2">Customer Growth</p>
                        <p className="text-2xl font-bold text-och-gold">
                          +{analyticsData.growth.new_customers}
                        </p>
                        <p className="text-xs text-och-steel">New customers this period</p>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* System Health */}
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-4">System Health</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-3 p-4 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                      <CheckCircle className="h-6 w-6 text-och-savanna-green" />
                      <div>
                        <p className="text-white font-medium">Financial Operations</p>
                        <p className="text-xs text-och-steel">All systems operational</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                      <CheckCircle className="h-6 w-6 text-och-savanna-green" />
                      <div>
                        <p className="text-white font-medium">Payment Processing</p>
                        <p className="text-xs text-och-steel">Gateway healthy</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                      <CheckCircle className="h-6 w-6 text-och-savanna-green" />
                      <div>
                        <p className="text-white font-medium">Compliance</p>
                        <p className="text-xs text-och-steel">Audit trail active</p>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </RouteGuard>
  )
}