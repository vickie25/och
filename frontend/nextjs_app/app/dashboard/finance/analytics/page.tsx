/**
 * Financial Analytics Dashboard
 * OCH student subscriptions (KES / Paystack) aligned with finance dashboard;
 * legacy invoice + automation metrics retained with clear labels.
 */

'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { FinanceNavigation } from '@/components/navigation/FinanceNavigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import {
  TrendingUp,
  DollarSign,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Activity,
  RefreshCw,
  CreditCard,
} from 'lucide-react'

type SubscriptionAnalytics = {
  currency: string
  active_subscribers: number
  trial_subscribers: number
  paying_subscribers: number
  past_due_subscribers: number
  canceled_total: number
  mrr_kes: number
  arr_kes_approx: number
  new_subscriptions_in_period: number
  canceled_subscriptions_in_period: number
  subscription_churn_rate_period_pct: number
  paystack_completed_revenue_kes_period: number
  paystack_completed_transactions_period: number
  paystack_completed_payments: Array<{
    id: string
    amount: number
    currency: string
    created_at: string
    processed_at: string | null
    user_email: string
    gateway_transaction_id: string
  }>
  plan_distribution: Array<{
    plan_id: string
    plan_name: string
    plan_display_name: string
    tier: string
    paying_subscribers: number
    mrr_kes: number
  }>
}

type StreamRevenueDetail = {
  period: { start_date: string; end_date: string; days: number }
  stream: string
  revenue: {
    stream: string
    total_revenue: number
    revenue_by_type: Array<{ type: string; total: number; count: number }>
    payment_success_rate: number
    total_invoices: number
    total_payments: number
    successful_payments: number
  }
  data_freshness?: { calculated_at: string; cadence: string }
}

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
  subscriptions?: SubscriptionAnalytics
  data_freshness?: {
    calculated_at: string
    cadence: string
    note?: string
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
  subscription_payment_leaders?: Array<{
    email: string
    total_revenue_kes: number
    payments: number
  }>
  subscription_payment_currency?: string
}

const defaultSubscriptions = (): SubscriptionAnalytics => ({
  currency: 'KES',
  active_subscribers: 0,
  trial_subscribers: 0,
  paying_subscribers: 0,
  past_due_subscribers: 0,
  canceled_total: 0,
  mrr_kes: 0,
  arr_kes_approx: 0,
  new_subscriptions_in_period: 0,
  canceled_subscriptions_in_period: 0,
  subscription_churn_rate_period_pct: 0,
  paystack_completed_revenue_kes_period: 0,
  paystack_completed_transactions_period: 0,
  paystack_completed_payments: [],
  plan_distribution: [],
})

const REVENUE_STREAM_FILTERS: { key: string; label: string }[] = [
  { key: 'subscription', label: 'A · Subscriptions' },
  { key: 'institution', label: 'B · Institutions' },
  { key: 'employer', label: 'C · Employers' },
  { key: 'cohort', label: 'D · Cohorts' },
  { key: 'contract', label: 'Marketplace / contracts' },
]

export default function AnalyticsPage() {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null)
  const [customerMetrics, setCustomerMetrics] = useState<CustomerMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('30')
  const [activeTab, setActiveTab] = useState<'overview' | 'revenue' | 'customers' | 'performance'>('overview')
  const [streamDetail, setStreamDetail] = useState<StreamRevenueDetail | null>(null)
  const [streamLoading, setStreamLoading] = useState(false)
  const [selectedStreamKey, setSelectedStreamKey] = useState<string>('subscription')

  const loadAnalyticsData = useCallback(async () => {
    try {
      setLoading(true)
      const [analyticsRes, customerRes] = await Promise.all([
        apiGateway.get(`/finance/analytics/revenue_dashboard/?days=${timeRange}`),
        apiGateway.get('/finance/analytics/customer_metrics/'),
      ])

      setAnalyticsData(analyticsRes)
      setCustomerMetrics(customerRes)
    } catch (error) {
      console.error('Failed to load analytics data:', error)
    } finally {
      setLoading(false)
    }
  }, [timeRange])

  useEffect(() => {
    void loadAnalyticsData()
  }, [loadAnalyticsData])

  useEffect(() => {
    const id = window.setInterval(() => {
      void loadAnalyticsData()
    }, 5 * 60 * 1000)
    return () => window.clearInterval(id)
  }, [loadAnalyticsData])

  const loadStreamDetail = useCallback(
    async (stream: string) => {
      try {
        setStreamLoading(true)
        const res = (await apiGateway.get(
          `/finance/analytics/revenue_by_stream/?days=${timeRange}&stream=${encodeURIComponent(stream)}`
        )) as StreamRevenueDetail
        setStreamDetail(res)
      } catch (e) {
        console.error('Stream detail failed', e)
        setStreamDetail(null)
      } finally {
        setStreamLoading(false)
      }
    },
    [timeRange]
  )

  const selectRevenueStream = (key: string) => {
    setSelectedStreamKey(key)
    void loadStreamDetail(key)
  }

  useEffect(() => {
    if (activeTab !== 'revenue') return
    void loadStreamDetail(selectedStreamKey)
    // Intentionally omit selectedStreamKey: stream changes use selectRevenueStream() only
  }, [activeTab, timeRange, loadStreamDetail])

  /** Legacy finance invoice / wallet amounts (historically USD in UI). */
  const formatInvoiceCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatKes = (amount: number) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
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
    return isGood ? (
      <CheckCircle className="h-4 w-4 text-och-savanna-green" />
    ) : (
      <AlertTriangle className="h-4 w-4 text-och-orange" />
    )
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

  const sub = analyticsData?.subscriptions ?? defaultSubscriptions()
  const leaders = customerMetrics?.subscription_payment_leaders ?? []

  return (
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight flex">
        <FinanceNavigation />
        <div className="flex-1 lg:ml-64">
          <div className="px-4 sm:px-6 lg:px-8 py-8">
            <div className="mb-8">
              <div className="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center">
                <div>
                  <h1 className="text-h1 font-bold text-white">Financial Analytics</h1>
                  <p className="mt-1 body-m text-och-steel max-w-2xl">
                    OCH student subscriptions (KES, Paystack) and legacy invoice metrics. Manage plans on{' '}
                    <Link href="/finance/subscriptions" className="text-och-mint hover:underline">
                      Subscriptions
                    </Link>
                    {' · '}
                    <Link href="/dashboard/finance" className="text-och-mint hover:underline">
                      Finance overview
                    </Link>
                    .
                  </p>
                  {analyticsData?.data_freshness && (
                    <p className="mt-2 text-xs text-och-steel/80">
                      Last computed: {new Date(analyticsData.data_freshness.calculated_at).toLocaleString()} ·{' '}
                      {analyticsData.data_freshness.note ?? 'Auto-refresh at most every 5 minutes in this view.'}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 flex-wrap">
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
                </div>
              </div>
            </div>

            <div className="border-b border-och-steel/20 mb-8">
              <nav className="-mb-px flex space-x-8 overflow-x-auto">
                {[
                  { key: 'overview', label: 'Overview', icon: BarChart3 },
                  { key: 'revenue', label: 'Revenue Streams', icon: DollarSign },
                  { key: 'customers', label: 'Customer Analytics', icon: Users },
                  { key: 'performance', label: 'Performance', icon: Activity },
                ].map((tab) => {
                  const Icon = tab.icon
                  return (
                    <button
                      key={tab.key}
                      type="button"
                      onClick={() => setActiveTab(tab.key as typeof activeTab)}
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

            {activeTab === 'overview' && analyticsData && (
              <div className="space-y-8">
                <div>
                  <h2 className="text-lg font-semibold text-white mb-4">OCH student subscriptions</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card className="p-6 bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Paystack revenue (period)</p>
                          <p className="text-2xl font-bold text-white">{formatKes(sub.paystack_completed_revenue_kes_period)}</p>
                          <p className="text-xs text-och-steel mt-1">
                            {sub.paystack_completed_transactions_period} completed · {analyticsData.period.days} days
                          </p>
                        </div>
                        <CreditCard className="h-8 w-8 text-och-mint" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/40">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">MRR (run-rate)</p>
                          <p className="text-2xl font-bold text-white">{formatKes(sub.mrr_kes)}</p>
                          <p className="text-xs text-och-steel mt-1">ARR ≈ {formatKes(sub.arr_kes_approx)}</p>
                        </div>
                        <TrendingUp className="h-8 w-8 text-och-defender" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-gradient-to-br from-och-gold/20 to-och-gold/5 border-och-gold/40">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Paying subscribers</p>
                          <p className="text-2xl font-bold text-white">{sub.paying_subscribers}</p>
                          <p className="text-xs text-och-steel mt-1">
                            Active {sub.active_subscribers} · Trial {sub.trial_subscribers}
                            {sub.past_due_subscribers > 0 ? ` · Past due ${sub.past_due_subscribers}` : ''}
                          </p>
                        </div>
                        <Users className="h-8 w-8 text-och-gold" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-gradient-to-br from-och-orange/20 to-och-orange/5 border-och-orange/40">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Movement (period)</p>
                          <p className="text-2xl font-bold text-white">
                            +{sub.new_subscriptions_in_period} / −{sub.canceled_subscriptions_in_period}
                          </p>
                          <p className="text-xs text-och-steel mt-1">
                            New vs canceled · Churn {formatPercentage(sub.subscription_churn_rate_period_pct)}
                          </p>
                        </div>
                        <Activity className="h-8 w-8 text-och-orange" />
                      </div>
                    </Card>
                  </div>

                  <Card className="p-6 mt-6 bg-och-midnight border border-och-mint/25">
                    <h3 className="text-h3 font-semibold text-white mb-1">Completed Paystack payments</h3>
                    <p className="text-sm text-och-steel mb-4">
                      Same window as the summary above ({analyticsData.period.days} days). Up to 200 rows.
                    </p>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-och-steel/20 text-sm">
                        <thead className="bg-och-midnight/50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-och-steel uppercase">Date</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-och-steel uppercase">User</th>
                            <th className="px-3 py-2 text-right text-xs font-medium text-och-steel uppercase">Amount</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-och-steel uppercase">Reference</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-och-steel/20">
                          {(sub.paystack_completed_payments ?? []).length === 0 ? (
                            <tr>
                              <td colSpan={4} className="px-3 py-6 text-och-steel">
                                No completed payments in this period.
                              </td>
                            </tr>
                          ) : (
                            (sub.paystack_completed_payments ?? []).map((p) => (
                              <tr key={p.id}>
                                <td className="px-3 py-2 text-och-steel whitespace-nowrap">
                                  {new Date(p.created_at).toLocaleString()}
                                </td>
                                <td className="px-3 py-2 text-white max-w-[200px] truncate" title={p.user_email}>
                                  {p.user_email || '—'}
                                </td>
                                <td className="px-3 py-2 text-right text-white font-medium">
                                  {formatKes(p.amount)}
                                </td>
                                <td className="px-3 py-2 text-och-steel font-mono text-xs max-w-[180px] truncate" title={p.gateway_transaction_id}>
                                  {p.gateway_transaction_id || '—'}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </div>

                <div>
                  <h2 className="text-lg font-semibold text-white mb-4">Legacy invoices & automation</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card className="p-6 bg-och-midnight border border-och-steel/20">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Invoice revenue (period)</p>
                          <p className="text-2xl font-bold text-white">
                            {formatInvoiceCurrency(Number(analyticsData.revenue.total_revenue))}
                          </p>
                          <p className="text-xs text-och-steel mt-1">Paid invoices · USD display</p>
                        </div>
                        <DollarSign className="h-8 w-8 text-och-steel" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-och-midnight border border-och-steel/20">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Payment success</p>
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

                    <Card className="p-6 bg-och-midnight border border-och-steel/20">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Customer metrics (ledger)</p>
                          <p className="text-2xl font-bold text-white">{formatPercentage(analyticsData.growth.growth_rate)}</p>
                          <p className="text-xs text-och-steel mt-1">+{analyticsData.growth.new_customers} new (CustomerMetrics)</p>
                        </div>
                        <Users className="h-8 w-8 text-och-gold" />
                      </div>
                    </Card>

                    <Card className="p-6 bg-och-midnight border border-och-steel/20">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-och-steel mb-1">Dunning recovery</p>
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
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-2">MRR by plan (KES)</h3>
                    <p className="text-xs text-och-steel mb-4">Active + trial, monthly run-rate</p>
                    <div className="space-y-4">
                      {sub.plan_distribution.length === 0 ? (
                        <p className="text-och-steel text-sm">No paying subscriptions yet.</p>
                      ) : (
                        sub.plan_distribution.map((row) => (
                          <div key={row.plan_id} className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-3 min-w-0">
                              <div className="w-3 h-3 bg-och-mint rounded-full shrink-0" />
                              <span className="text-white truncate">{row.plan_display_name}</span>
                            </div>
                            <div className="text-right shrink-0">
                              <p className="text-white font-medium">{formatKes(row.mrr_kes)}</p>
                              <p className="text-xs text-och-steel">
                                {row.paying_subscribers} subs · {row.tier}
                              </p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>

                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-2">Revenue by invoice type</h3>
                    <p className="text-xs text-och-steel mb-4">Legacy Invoice model (USD labels)</p>
                    <div className="space-y-4">
                      {analyticsData.revenue.revenue_by_type.length === 0 ? (
                        <p className="text-och-steel text-sm">No paid invoices in this window.</p>
                      ) : (
                        analyticsData.revenue.revenue_by_type.map((item) => (
                          <div key={item.type} className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-3 h-3 bg-och-mint rounded-full" />
                              <span className="text-white capitalize">{item.type.replace('_', ' ')}</span>
                            </div>
                            <div className="text-right">
                              <p className="text-white font-medium">{formatInvoiceCurrency(Number(item.total))}</p>
                              <p className="text-xs text-och-steel">{item.count} invoices</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-2">Recognized revenue streams</h3>
                    <p className="text-xs text-och-steel mb-4">RevenueStream records (finance DB)</p>
                    <div className="space-y-4">
                      {analyticsData.revenue_streams.length === 0 ? (
                        <p className="text-och-steel text-sm">No stream rows in this period.</p>
                      ) : (
                        analyticsData.revenue_streams.map((stream) => (
                          <div key={stream.stream_type} className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-3 h-3 bg-och-defender rounded-full" />
                              <span className="text-white capitalize">{stream.stream_type}</span>
                            </div>
                            <div className="text-right">
                              <p className="text-white font-medium">{formatInvoiceCurrency(Number(stream.total))}</p>
                              <p className="text-xs text-och-steel">{stream.count} transactions</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                  <Card className="p-6 bg-och-midnight/50 border border-och-steel/10 border-dashed">
                    <h3 className="text-h3 font-semibold text-white mb-2">Totals</h3>
                    <p className="text-sm text-och-steel mb-4">
                      Canceled subscriptions (all time): <span className="text-white">{sub.canceled_total}</span>
                    </p>
                    <p className="text-xs text-och-steel">
                      Subscription counts and MRR come from <code className="text-och-mint">UserSubscription</code> + plans.
                      Paystack totals use <code className="text-och-mint">PaymentTransaction</code> completed in range.
                    </p>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'revenue' && analyticsData && (
              <div className="space-y-8">
                <Card className="p-6 bg-och-midnight border border-och-mint/20">
                  <h3 className="text-h3 font-semibold text-white mb-2">Invoice revenue by OCH stream</h3>
                  <p className="text-sm text-och-steel mb-4">
                    Filtered <code className="text-och-mint/90">finance_invoices</code> by type for the selected
                    period. Data is computed on request; full dashboard also refreshes every 5 minutes.
                  </p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {REVENUE_STREAM_FILTERS.map((s) => (
                      <button
                        key={s.key}
                        type="button"
                        onClick={() => selectRevenueStream(s.key)}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                          selectedStreamKey === s.key
                            ? 'bg-och-defender text-white'
                            : 'bg-och-steel/10 text-och-steel hover:text-white'
                        }`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                  {streamLoading ? (
                    <p className="text-och-steel text-sm">Loading stream metrics…</p>
                  ) : streamDetail ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div>
                        <p className="text-xs text-och-steel uppercase">Stream</p>
                        <p className="text-lg font-semibold text-white capitalize">{streamDetail.revenue.stream}</p>
                      </div>
                      <div>
                        <p className="text-xs text-och-steel uppercase">Paid invoice total</p>
                        <p className="text-lg font-semibold text-white">
                          {formatInvoiceCurrency(Number(streamDetail.revenue.total_revenue))}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-och-steel uppercase">Success rate (payments)</p>
                        <p className="text-lg font-semibold text-white">
                          {formatPercentage(streamDetail.revenue.payment_success_rate)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-och-steel uppercase">Invoices / payments</p>
                        <p className="text-lg font-semibold text-white">
                          {streamDetail.revenue.total_invoices} / {streamDetail.revenue.total_payments}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-och-steel text-sm">No stream data.</p>
                  )}
                </Card>

                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-2">OCH subscription MRR by plan</h3>
                  <p className="text-sm text-och-steel mb-6">KES · same basis as student pricing and finance dashboard</p>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-och-steel/20">
                      <thead className="bg-och-midnight/50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-och-steel uppercase">Plan</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-och-steel uppercase">Tier</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-och-steel uppercase">Subscribers</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-och-steel uppercase">MRR (KES)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-och-steel/20">
                        {sub.plan_distribution.length === 0 ? (
                          <tr>
                            <td colSpan={4} className="px-4 py-6 text-och-steel text-sm">
                              No paying subscriptions.
                            </td>
                          </tr>
                        ) : (
                          sub.plan_distribution.map((row) => (
                            <tr key={row.plan_id}>
                              <td className="px-4 py-3 text-white">{row.plan_display_name}</td>
                              <td className="px-4 py-3 text-och-steel text-sm">{row.tier}</td>
                              <td className="px-4 py-3 text-right text-white">{row.paying_subscribers}</td>
                              <td className="px-4 py-3 text-right text-white font-medium">{formatKes(row.mrr_kes)}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </Card>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-4">Invoice revenue by type</h3>
                    <div className="space-y-4">
                      {analyticsData.revenue.revenue_by_type.length === 0 ? (
                        <p className="text-och-steel text-sm">No data.</p>
                      ) : (
                        analyticsData.revenue.revenue_by_type.map((item) => (
                          <div key={item.type} className="flex items-center justify-between">
                            <span className="text-white capitalize">{item.type.replace('_', ' ')}</span>
                            <div className="text-right">
                              <p className="text-white font-medium">{formatInvoiceCurrency(Number(item.total))}</p>
                              <p className="text-xs text-och-steel">{item.count} invoices</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                  <Card className="p-6 bg-och-midnight border border-och-steel/20">
                    <h3 className="text-h3 font-semibold text-white mb-4">Recognized streams</h3>
                    <div className="space-y-4">
                      {analyticsData.revenue_streams.length === 0 ? (
                        <p className="text-och-steel text-sm">No RevenueStream rows.</p>
                      ) : (
                        analyticsData.revenue_streams.map((stream) => (
                          <div key={stream.stream_type} className="flex items-center justify-between">
                            <span className="text-white capitalize">{stream.stream_type}</span>
                            <div className="text-right">
                              <p className="text-white font-medium">{formatInvoiceCurrency(Number(stream.total))}</p>
                              <p className="text-xs text-och-steel">{stream.count} tx</p>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'customers' && customerMetrics && (
              <div className="space-y-8">
                <Card className="p-6 bg-och-midnight border border-och-mint/30">
                  <h3 className="text-h3 font-semibold text-white mb-2">Top payers (Paystack / subscriptions)</h3>
                  <p className="text-sm text-och-steel mb-4">
                    Completed {customerMetrics.subscription_payment_currency ?? 'KES'} totals (all time)
                  </p>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-och-steel/20">
                      <thead className="bg-och-midnight/50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase">#</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase">Email</th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-och-steel uppercase">Total</th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-och-steel uppercase">Payments</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-och-steel/20">
                        {leaders.length === 0 ? (
                          <tr>
                            <td colSpan={4} className="px-6 py-6 text-och-steel text-sm">
                              No completed Paystack transactions yet.
                            </td>
                          </tr>
                        ) : (
                          leaders.map((row, index) => (
                            <tr key={row.email + index}>
                              <td className="px-6 py-4 text-och-mint font-medium">#{index + 1}</td>
                              <td className="px-6 py-4 text-white text-sm">{row.email || '—'}</td>
                              <td className="px-6 py-4 text-right text-white font-medium">
                                {formatKes(row.total_revenue_kes)}
                              </td>
                              <td className="px-6 py-4 text-right text-och-steel">{row.payments}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </Card>

                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-2">Top customers (CustomerMetrics ledger)</h3>
                  <p className="text-xs text-och-steel mb-4">Separate aggregate table; may be sparse if not backfilled.</p>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-och-steel/20">
                      <thead className="bg-och-midnight/50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Customer
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">Type</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Total Revenue
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">MRR</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">LTV</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Active Months
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                        {customerMetrics.top_customers.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="px-6 py-6 text-och-steel text-sm">
                              No CustomerMetrics rows.
                            </td>
                          </tr>
                        ) : (
                          customerMetrics.top_customers.map((customer, index) => (
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
                                {formatInvoiceCurrency(Number(customer.total_revenue))}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                                {formatInvoiceCurrency(Number(customer.monthly_recurring_revenue))}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                                {formatInvoiceCurrency(Number(customer.lifetime_value))}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                                {customer.months_active} months
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </Card>

                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-4">Churn analysis (ledger)</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-sm font-medium text-och-steel mb-2">Churned customers (last 30 days)</p>
                      <p className="text-3xl font-bold text-och-orange">
                        {customerMetrics.churn_analysis.churned_last_30_days}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-och-steel mb-2">Cohort retention</p>
                      <p className="text-sm text-och-steel">
                        Tracking {customerMetrics.churn_analysis.cohort_data.length} cohorts
                      </p>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {activeTab === 'performance' && analyticsData && (
              <div className="space-y-8">
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-6">OCH subscriptions</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg">
                      <div>
                        <p className="text-white font-medium">Period churn (subscriptions)</p>
                        <p className="text-xs text-och-steel">Canceled ÷ paying base · same window as overview</p>
                      </div>
                      <p
                        className={`text-lg font-bold ${getStatusColor(sub.subscription_churn_rate_period_pct, 5, true)}`}
                      >
                        {formatPercentage(sub.subscription_churn_rate_period_pct)}
                      </p>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg">
                      <div>
                        <p className="text-white font-medium">Paystack success (period revenue)</p>
                        <p className="text-xs text-och-steel">{formatKes(sub.paystack_completed_revenue_kes_period)}</p>
                      </div>
                      <p className="text-lg font-bold text-och-mint">{sub.paystack_completed_transactions_period} tx</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-6">Legacy automation</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(analyticsData.payment_success.success_rate, 95)}
                          <div>
                            <p className="text-white font-medium">Payment success rate</p>
                            <p className="text-xs text-och-steel">Target: {'>'}95%</p>
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
                            <p className="text-white font-medium">Dunning recovery rate</p>
                            <p className="text-xs text-och-steel">Target: {'>'}80%</p>
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
                            <p className="text-white font-medium">Churn rate (CustomerMetrics)</p>
                            <p className="text-xs text-och-steel">Target: {'<'}5%</p>
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
                        <p className="text-white font-medium mb-2">Invoices processed</p>
                        <p className="text-2xl font-bold text-och-mint">{analyticsData.revenue.total_invoices}</p>
                        <p className="text-xs text-och-steel">Paid invoices in period (ledger)</p>
                      </div>

                      <div className="p-4 bg-och-steel/10 rounded-lg">
                        <p className="text-white font-medium mb-2">Stream sources</p>
                        <p className="text-2xl font-bold text-och-defender">
                          {sub.plan_distribution.length + analyticsData.revenue_streams.length}
                        </p>
                        <p className="text-xs text-och-steel">
                          {sub.plan_distribution.length} subscription plans (MRR) + {analyticsData.revenue_streams.length}{' '}
                          finance streams
                        </p>
                      </div>

                      <div className="p-4 bg-och-steel/10 rounded-lg">
                        <p className="text-white font-medium mb-2">Customer growth (ledger)</p>
                        <p className="text-2xl font-bold text-och-gold">+{analyticsData.growth.new_customers}</p>
                        <p className="text-xs text-och-steel">New customers this period</p>
                      </div>
                    </div>
                  </div>
                </Card>

                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-4">System health</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-3 p-4 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                      <CheckCircle className="h-6 w-6 text-och-savanna-green" />
                      <div>
                        <p className="text-white font-medium">Financial operations</p>
                        <p className="text-xs text-och-steel">Operational</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                      <CheckCircle className="h-6 w-6 text-och-savanna-green" />
                      <div>
                        <p className="text-white font-medium">Payment processing</p>
                        <p className="text-xs text-och-steel">Gateway + webhooks</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 p-4 bg-och-savanna-green/10 rounded-lg border border-och-savanna-green/30">
                      <CheckCircle className="h-6 w-6 text-och-savanna-green" />
                      <div>
                        <p className="text-white font-medium">Compliance</p>
                        <p className="text-xs text-och-steel">Audit trail</p>
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
