'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  CreditCard,
  AlertTriangle,
  CheckCircle,
  Clock,
  Shield,
  Receipt,
  Repeat,
} from 'lucide-react'

interface PaymentMetrics {
  overall_metrics: {
    success_rate: number
    total_attempts: number
    successful_payments: number
    failed_payments: number
    meets_95_percent_target: boolean
  }
  daily_data: Array<{
    date: string
    success_rate: number
    total_attempts: number
    successful_payments: number
    failed_payments: number
    meets_threshold: boolean
  }>
  gateway_breakdown: Record<string, {
    success: number
    failed: number
    success_rate: number
  }>
}

interface InvoiceMetrics {
  sla_metrics: {
    total_invoices: number
    sla_compliant: number
    sla_compliance_rate: number
    meets_5min_target: boolean
  }
  timing_metrics: {
    avg_generation_time_seconds: number
    avg_total_time_seconds: number
    avg_generation_time_minutes: number
    avg_total_time_minutes: number
  }
  recent_deliveries: Array<{
    invoice_number: string
    transaction_completed_at: string
    total_time_seconds: number
    meets_5min_sla: boolean
    sla_breach_reason: string
  }>
}

interface DunningMetrics {
  recovery_metrics: {
    total_cycles: number
    recovered_cycles: number
    failed_cycles: number
    active_cycles: number
    recovery_rate: number
    meets_80_percent_target: boolean
  }
  financial_metrics: {
    total_recovered_amount: number
    avg_recovery_amount: number
  }
  timing_metrics: {
    avg_cycle_duration_days: number
  }
  recent_recoveries: Array<{
    user_email: string
    recovered_at: string
    recovery_amount: number
    total_attempts: number
    cycle_duration_days: number
  }>
}

interface ComplianceMetrics {
  compliance_status: {
    total_violations: number
    open_violations: number
    resolved_violations: number
    critical_violations: number
    zero_violations_target_met: boolean
    compliance_score: number
  }
  violation_breakdown: Record<string, {
    total: number
    open: number
    critical: number
  }>
  recent_violations: Array<{
    id: string
    violation_type: string
    severity: string
    status: string
    detected_at: string
    description: string
    affected_systems: string[]
  }>
}

export default function EnhancedFinancialDashboard() {
  const [paymentMetrics, setPaymentMetrics] = useState<PaymentMetrics | null>(null)
  const [invoiceMetrics, setInvoiceMetrics] = useState<InvoiceMetrics | null>(null)
  const [dunningMetrics, setDunningMetrics] = useState<DunningMetrics | null>(null)
  const [complianceMetrics, setComplianceMetrics] = useState<ComplianceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedTimeRange, setSelectedTimeRange] = useState(30)
  const [autoRefresh, setAutoRefresh] = useState(true)

  useEffect(() => {
    fetchAllMetrics()
    
    if (autoRefresh) {
      const interval = setInterval(fetchAllMetrics, 60000) // Refresh every minute
      return () => clearInterval(interval)
    }
  }, [selectedTimeRange, autoRefresh])

  const fetchAllMetrics = async () => {
    try {
      setLoading(true)
      const [paymentData, invoiceData, dunningData, complianceData] = await Promise.all([
        apiGateway.get(`/financial/payment-success-rate/?days=${selectedTimeRange}`),
        apiGateway.get(`/financial/invoice-delivery-metrics/?days=${selectedTimeRange}`),
        apiGateway.get(`/financial/dunning-recovery-metrics/?days=${selectedTimeRange * 3}`), // Longer period for dunning
        apiGateway.get('/financial/pci-compliance-dashboard/?days=30'),
      ])

      setPaymentMetrics(paymentData.data)
      setInvoiceMetrics(invoiceData.data)
      setDunningMetrics(dunningData.data)
      setComplianceMetrics(complianceData.data)
    } catch (error) {
      console.error('Failed to fetch financial metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  const getStatusColor = (isGood: boolean) => isGood ? 'text-green-500' : 'text-red-500'
  const getStatusIcon = (isGood: boolean) => isGood ? CheckCircle : AlertTriangle

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-och-defender"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Financial Dashboard</h1>
          <p className="text-och-steel">Real-time financial metrics and compliance monitoring</p>
        </div>
        
        <div className="flex items-center gap-4">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(Number(e.target.value))}
            className="px-3 py-2 bg-och-midnight border border-och-steel/30 rounded-lg text-white"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            variant={autoRefresh ? 'defender' : 'outline'}
            size="sm"
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          
          <Button onClick={fetchAllMetrics} variant="outline" size="sm">
            Refresh Now
          </Button>
        </div>
      </div>

      {/* Success Criteria Overview */}
      <Card className="border-och-defender/30">
        <div className="p-6">
          <h2 className="text-xl font-bold text-white mb-4">Success Criteria Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="flex items-center gap-3">
              {paymentMetrics && React.createElement(
                getStatusIcon(paymentMetrics.overall_metrics.meets_95_percent_target),
                { className: `w-5 h-5 ${getStatusColor(paymentMetrics.overall_metrics.meets_95_percent_target)}` }
              )}
              <div>
                <p className="text-sm text-och-steel">Payment Success</p>
                <p className="font-semibold text-white">
                  {paymentMetrics?.overall_metrics.success_rate.toFixed(1)}% / 95%
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {invoiceMetrics && React.createElement(
                getStatusIcon(invoiceMetrics.sla_metrics.meets_5min_target),
                { className: `w-5 h-5 ${getStatusColor(invoiceMetrics.sla_metrics.meets_5min_target)}` }
              )}
              <div>
                <p className="text-sm text-och-steel">Invoice Delivery</p>
                <p className="font-semibold text-white">
                  {invoiceMetrics?.timing_metrics.avg_total_time_minutes.toFixed(1)}m / 5m
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {dunningMetrics && React.createElement(
                getStatusIcon(dunningMetrics.recovery_metrics.meets_80_percent_target),
                { className: `w-5 h-5 ${getStatusColor(dunningMetrics.recovery_metrics.meets_80_percent_target)}` }
              )}
              <div>
                <p className="text-sm text-och-steel">Dunning Recovery</p>
                <p className="font-semibold text-white">
                  {dunningMetrics?.recovery_metrics.recovery_rate.toFixed(1)}% / 80%
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              {complianceMetrics && React.createElement(
                getStatusIcon(complianceMetrics.compliance_status.zero_violations_target_met),
                { className: `w-5 h-5 ${getStatusColor(complianceMetrics.compliance_status.zero_violations_target_met)}` }
              )}
              <div>
                <p className="text-sm text-och-steel">PCI Compliance</p>
                <p className="font-semibold text-white">
                  {complianceMetrics?.compliance_status.open_violations} violations
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-green-500" />
              <div>
                <p className="text-sm text-och-steel">Audit Retention</p>
                <p className="font-semibold text-white">7 years</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Payment Success Rate */}
      {paymentMetrics && (
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                Payment Success Rate
              </h2>
              <Badge 
                variant={paymentMetrics.overall_metrics.meets_95_percent_target ? 'defender' : 'orange'}
              >
                {paymentMetrics.overall_metrics.meets_95_percent_target ? 'Target Met' : 'Below Target'}
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Success Rate</p>
                <p className="text-2xl font-bold text-white">
                  {paymentMetrics.overall_metrics.success_rate.toFixed(1)}%
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Total Attempts</p>
                <p className="text-2xl font-bold text-white">
                  {paymentMetrics.overall_metrics.total_attempts.toLocaleString()}
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Successful</p>
                <p className="text-2xl font-bold text-green-500">
                  {paymentMetrics.overall_metrics.successful_payments.toLocaleString()}
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Failed</p>
                <p className="text-2xl font-bold text-red-500">
                  {paymentMetrics.overall_metrics.failed_payments.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Daily Success Rate Chart */}
            <div className="h-64 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={paymentMetrics.daily_data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#8B9DAF"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    stroke="#8B9DAF"
                    tick={{ fontSize: 12 }}
                    domain={[90, 100]}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0A1628', 
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="success_rate" 
                    stroke="#00D9FF" 
                    strokeWidth={2}
                    dot={{ fill: '#00D9FF', strokeWidth: 2 }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey={95} 
                    stroke="#FF6B35" 
                    strokeDasharray="5 5"
                    strokeWidth={1}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Gateway Breakdown */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Gateway Performance</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(paymentMetrics.gateway_breakdown).map(([gateway, stats]) => (
                  <div key={gateway} className="bg-och-midnight/50 p-4 rounded-lg">
                    <h4 className="font-medium text-white capitalize mb-2">{gateway}</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-och-steel">Success Rate:</span>
                        <span className={`font-medium ${stats.success_rate >= 95 ? 'text-green-500' : 'text-red-500'}`}>
                          {stats.success_rate.toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-och-steel">Successful:</span>
                        <span className="text-white">{stats.success.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-och-steel">Failed:</span>
                        <span className="text-white">{stats.failed.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Invoice Delivery Metrics */}
      {invoiceMetrics && (
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Receipt className="w-5 h-5" />
                Invoice Delivery SLA
              </h2>
              <Badge 
                variant={invoiceMetrics.sla_metrics.meets_5min_target ? 'defender' : 'orange'}
              >
                {invoiceMetrics.sla_metrics.meets_5min_target ? '5-Min SLA Met' : 'SLA Breach'}
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">SLA Compliance</p>
                <p className="text-2xl font-bold text-white">
                  {invoiceMetrics.sla_metrics.sla_compliance_rate.toFixed(1)}%
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Avg Generation Time</p>
                <p className="text-2xl font-bold text-white">
                  {invoiceMetrics.timing_metrics.avg_generation_time_minutes.toFixed(1)}m
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Avg Total Time</p>
                <p className="text-2xl font-bold text-white">
                  {invoiceMetrics.timing_metrics.avg_total_time_minutes.toFixed(1)}m
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Total Invoices</p>
                <p className="text-2xl font-bold text-white">
                  {invoiceMetrics.sla_metrics.total_invoices.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Recent Deliveries */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Recent Invoice Deliveries</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-och-steel/20">
                      <th className="text-left text-och-steel p-2">Invoice</th>
                      <th className="text-left text-och-steel p-2">Delivery Time</th>
                      <th className="text-left text-och-steel p-2">SLA Status</th>
                      <th className="text-left text-och-steel p-2">Breach Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invoiceMetrics.recent_deliveries.slice(0, 10).map((delivery) => (
                      <tr key={delivery.invoice_number} className="border-b border-och-steel/10">
                        <td className="text-white p-2 font-mono">{delivery.invoice_number}</td>
                        <td className="text-white p-2">{formatTime(delivery.total_time_seconds)}</td>
                        <td className="p-2">
                          <Badge variant={delivery.meets_5min_sla ? 'defender' : 'orange'}>
                            {delivery.meets_5min_sla ? 'Met' : 'Breach'}
                          </Badge>
                        </td>
                        <td className="text-och-steel p-2">{delivery.sla_breach_reason || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Dunning Recovery Metrics */}
      {dunningMetrics && (
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Repeat className="w-5 h-5" />
                Dunning Management
              </h2>
              <Badge 
                variant={dunningMetrics.recovery_metrics.meets_80_percent_target ? 'defender' : 'orange'}
              >
                {dunningMetrics.recovery_metrics.meets_80_percent_target ? '80% Target Met' : 'Below Target'}
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Recovery Rate</p>
                <p className="text-2xl font-bold text-white">
                  {dunningMetrics.recovery_metrics.recovery_rate.toFixed(1)}%
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Total Recovered</p>
                <p className="text-2xl font-bold text-green-500">
                  {formatCurrency(dunningMetrics.financial_metrics.total_recovered_amount)}
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Active Cycles</p>
                <p className="text-2xl font-bold text-white">
                  {dunningMetrics.recovery_metrics.active_cycles}
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Avg Cycle Duration</p>
                <p className="text-2xl font-bold text-white">
                  {dunningMetrics.timing_metrics.avg_cycle_duration_days.toFixed(1)} days
                </p>
              </div>
            </div>

            {/* Recent Recoveries */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Recent Recoveries</h3>
              <div className="space-y-2">
                {dunningMetrics.recent_recoveries.slice(0, 5).map((recovery, index) => (
                  <div key={index} className="bg-och-midnight/50 p-3 rounded-lg flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{recovery.user_email}</p>
                      <p className="text-och-steel text-sm">
                        {recovery.total_attempts} attempts • {recovery.cycle_duration_days} days
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-green-500 font-bold">{formatCurrency(recovery.recovery_amount)}</p>
                      <p className="text-och-steel text-sm">
                        {new Date(recovery.recovered_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* PCI Compliance */}
      {complianceMetrics && (
        <Card>
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Shield className="w-5 h-5" />
                PCI Compliance Monitoring
              </h2>
              <Badge 
                variant={complianceMetrics.compliance_status.zero_violations_target_met ? 'defender' : 'orange'}
              >
                {complianceMetrics.compliance_status.zero_violations_target_met ? 'Zero Violations' : 'Violations Found'}
              </Badge>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Compliance Score</p>
                <p className="text-2xl font-bold text-white">
                  {complianceMetrics.compliance_status.compliance_score}/100
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Open Violations</p>
                <p className="text-2xl font-bold text-red-500">
                  {complianceMetrics.compliance_status.open_violations}
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Critical Issues</p>
                <p className="text-2xl font-bold text-red-500">
                  {complianceMetrics.compliance_status.critical_violations}
                </p>
              </div>
              <div className="bg-och-midnight/50 p-4 rounded-lg">
                <p className="text-och-steel text-sm">Resolved</p>
                <p className="text-2xl font-bold text-green-500">
                  {complianceMetrics.compliance_status.resolved_violations}
                </p>
              </div>
            </div>

            {/* Recent Violations */}
            {complianceMetrics.recent_violations.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Recent Violations</h3>
                <div className="space-y-2">
                  {complianceMetrics.recent_violations.slice(0, 5).map((violation) => (
                    <div key={violation.id} className="bg-och-midnight/50 p-3 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="text-white font-medium">{violation.violation_type}</h4>
                        <div className="flex items-center gap-2">
                          <Badge variant={violation.severity === 'critical' ? 'orange' : 'steel'}>
                            {violation.severity}
                          </Badge>
                          <Badge variant={violation.status === 'resolved' ? 'defender' : 'steel'}>
                            {violation.status}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-och-steel text-sm mb-2">{violation.description}</p>
                      <p className="text-och-steel text-xs">
                        Detected: {new Date(violation.detected_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}