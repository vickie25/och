/**
 * Compliance & Security Dashboard
 * Monitor audit trails, security events, and compliance reports
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
  Shield, 
  AlertTriangle,
  CheckCircle,
  FileText,
  Eye,
  Download,
  Search,
  Filter,
  Clock,
  User,
  Lock,
  Activity,
  Database,
  Globe,
  Plus,
  Trash2,
  DollarSign,
} from 'lucide-react'

type AuditLog = {
  id: string
  timestamp: string
  user_email: string
  action: string
  entity_type: string
  entity_id: string
  description: string
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  user_ip: string
  is_pci_relevant: boolean
  is_gdpr_relevant: boolean
}

type SecurityEvent = {
  id: string
  event_type: string
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical'
  description: string
  user_ip: string
  is_resolved: boolean
  detected_at: string
  resolved_at?: string
}

type ComplianceReport = {
  report_id: string
  report_type: string
  compliance_score: number
  issues_found: number
  critical_issues: number
  summary: string
}

export default function CompliancePage() {
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'audit' | 'security' | 'reports'>('audit')
  
  // Filters
  const [auditFilters, setAuditFilters] = useState({
    entity_type: '',
    risk_level: '',
    days: '7',
    search: ''
  })
  
  const [securityFilters, setSecurityFilters] = useState({
    severity: '',
    event_type: '',
    is_resolved: '',
    days: '7'
  })

  useEffect(() => {
    loadData()
  }, [auditFilters, securityFilters])

  const loadData = async () => {
    try {
      setLoading(true)
      
      if (activeTab === 'audit') {
        const auditParams = new URLSearchParams()
        Object.entries(auditFilters).forEach(([key, value]) => {
          if (value) auditParams.append(key, value)
        })
        
        const auditResponse = await apiGateway.get(`/finance/compliance/audit_trail/?${auditParams}`)
        setAuditLogs(auditResponse.results || [])
      }
      
      if (activeTab === 'security') {
        const securityParams = new URLSearchParams()
        Object.entries(securityFilters).forEach(([key, value]) => {
          if (value) securityParams.append(key, value)
        })
        
        const securityResponse = await apiGateway.get(`/finance/compliance/security_events/?${securityParams}`)
        setSecurityEvents(securityResponse.events || [])
      }
      
    } catch (error) {
      console.error('Failed to load compliance data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateComplianceReport = async (reportType: string) => {
    try {
      const endDate = new Date().toISOString().split('T')[0]
      const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      
      const response = await apiGateway.post('/finance/compliance/generate_compliance_report/', {
        report_type: reportType,
        period_start: startDate,
        period_end: endDate
      })
      
      // Handle report generation success
      alert(`${reportType.toUpperCase()} compliance report generated successfully. Score: ${response.compliance_score}%`)
      
    } catch (error) {
      console.error('Failed to generate compliance report:', error)
      alert('Failed to generate compliance report')
    }
  }

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'high': return 'text-och-orange bg-och-orange/10 border-och-orange/30'
      case 'medium': return 'text-och-gold bg-och-gold/10 border-och-gold/30'
      case 'low': return 'text-och-mint bg-och-mint/10 border-och-mint/30'
      default: return 'text-och-steel bg-och-steel/10 border-och-steel/30'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'high': return 'text-och-orange bg-och-orange/10 border-och-orange/30'
      case 'medium': return 'text-och-gold bg-och-gold/10 border-och-gold/30'
      case 'low': return 'text-och-defender bg-och-defender/10 border-och-defender/30'
      case 'info': return 'text-och-mint bg-och-mint/10 border-och-mint/30'
      default: return 'text-och-steel bg-och-steel/10 border-och-steel/30'
    }
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'create': return <Plus className="h-4 w-4" />
      case 'update': return <Edit className="h-4 w-4" />
      case 'delete': return <Trash2 className="h-4 w-4" />
      case 'payment': return <DollarSign className="h-4 w-4" />
      case 'access': return <Eye className="h-4 w-4" />
      default: return <Activity className="h-4 w-4" />
    }
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
                  <h1 className="text-h1 font-bold text-white">Compliance & Security</h1>
                  <p className="mt-1 body-m text-och-steel">
                    Monitor audit trails, security events, and compliance reports
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button onClick={() => generateComplianceReport('pci_dss')} variant="outline">
                    <Shield className="h-4 w-4 mr-2" />
                    PCI Report
                  </Button>
                  <Button onClick={() => generateComplianceReport('gdpr')} variant="outline">
                    <Globe className="h-4 w-4 mr-2" />
                    GDPR Report
                  </Button>
                  <Button onClick={() => generateComplianceReport('audit_trail')}>
                    <FileText className="h-4 w-4 mr-2" />
                    Audit Report
                  </Button>
                </div>
              </div>
            </div>

            {/* Compliance Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
              <Card className="p-4 bg-och-savanna-green/10 border border-och-savanna-green/30">
                <div className="flex items-center gap-3 mb-2">
                  <Shield className="h-5 w-5 text-och-savanna-green" />
                  <p className="font-medium text-white">PCI-DSS</p>
                </div>
                <p className="text-2xl font-bold text-och-savanna-green">98%</p>
                <p className="text-xs text-och-steel">Compliant</p>
              </Card>

              <Card className="p-4 bg-och-savanna-green/10 border border-och-savanna-green/30">
                <div className="flex items-center gap-3 mb-2">
                  <Globe className="h-5 w-5 text-och-savanna-green" />
                  <p className="font-medium text-white">GDPR</p>
                </div>
                <p className="text-2xl font-bold text-och-savanna-green">100%</p>
                <p className="text-xs text-och-steel">Compliant</p>
              </Card>

              <Card className="p-4 bg-och-mint/10 border border-och-mint/30">
                <div className="flex items-center gap-3 mb-2">
                  <Database className="h-5 w-5 text-och-mint" />
                  <p className="font-medium text-white">Audit Trail</p>
                </div>
                <p className="text-2xl font-bold text-och-mint">7 Years</p>
                <p className="text-xs text-och-steel">Retention</p>
              </Card>

              <Card className="p-4 bg-och-defender/10 border border-och-defender/30">
                <div className="flex items-center gap-3 mb-2">
                  <Lock className="h-5 w-5 text-och-defender" />
                  <p className="font-medium text-white">Encryption</p>
                </div>
                <p className="text-2xl font-bold text-och-defender">AES-256</p>
                <p className="text-xs text-och-steel">At Rest & Transit</p>
              </Card>
            </div>

            {/* Tabs */}
            <div className="border-b border-och-steel/20 mb-6">
              <nav className="-mb-px flex space-x-8">
                {[
                  { key: 'audit', label: 'Audit Trail', icon: FileText },
                  { key: 'security', label: 'Security Events', icon: AlertTriangle },
                  { key: 'reports', label: 'Compliance Reports', icon: Shield }
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

            {/* Audit Trail Tab */}
            {activeTab === 'audit' && (
              <div className="space-y-6">
                {/* Filters */}
                <Card className="p-4 bg-och-midnight border border-och-steel/20">
                  <div className="flex flex-wrap gap-4">
                    <div className="flex-1 min-w-64">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-och-steel" />
                        <input
                          type="text"
                          placeholder="Search audit logs..."
                          value={auditFilters.search}
                          onChange={(e) => setAuditFilters({...auditFilters, search: e.target.value})}
                          className="w-full pl-10 pr-4 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:ring-2 focus:ring-och-mint"
                        />
                      </div>
                    </div>
                    
                    <select
                      value={auditFilters.entity_type}
                      onChange={(e) => setAuditFilters({...auditFilters, entity_type: e.target.value})}
                      className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                    >
                      <option value="">All Entities</option>
                      <option value="wallet">Wallet</option>
                      <option value="transaction">Transaction</option>
                      <option value="invoice">Invoice</option>
                      <option value="payment">Payment</option>
                      <option value="contract">Contract</option>
                    </select>

                    <select
                      value={auditFilters.risk_level}
                      onChange={(e) => setAuditFilters({...auditFilters, risk_level: e.target.value})}
                      className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                    >
                      <option value="">All Risk Levels</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>

                    <select
                      value={auditFilters.days}
                      onChange={(e) => setAuditFilters({...auditFilters, days: e.target.value})}
                      className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                    >
                      <option value="1">Last 24 hours</option>
                      <option value="7">Last 7 days</option>
                      <option value="30">Last 30 days</option>
                      <option value="90">Last 90 days</option>
                    </select>
                  </div>
                </Card>

                {/* Audit Logs Table */}
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-och-steel/20">
                      <thead className="bg-och-midnight/50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Timestamp
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            User
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Action
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Entity
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Risk Level
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Compliance
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                        {auditLogs.map((log) => (
                          <tr key={log.id} className="hover:bg-och-steel/5">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                              <div className="flex items-center gap-2">
                                <Clock className="h-3 w-3" />
                                {new Date(log.timestamp).toLocaleString()}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                <User className="h-3 w-3 text-och-steel" />
                                <div>
                                  <p className="text-sm text-white">{log.user_email}</p>
                                  <p className="text-xs text-och-steel">{log.user_ip}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                {getActionIcon(log.action)}
                                <span className="text-sm text-white capitalize">{log.action}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <p className="text-sm text-white capitalize">{log.entity_type}</p>
                                <p className="text-xs text-och-steel">{log.entity_id.slice(0, 8)}...</p>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRiskLevelColor(log.risk_level)}`}>
                                {log.risk_level}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex gap-1">
                                {log.is_pci_relevant && (
                                  <Badge variant="defender" className="text-xs">PCI</Badge>
                                )}
                                {log.is_gdpr_relevant && (
                                  <Badge variant="mint" className="text-xs">GDPR</Badge>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <Button variant="ghost" size="sm">
                                <Eye className="h-3 w-3 mr-1" />
                                View
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </div>
            )}

            {/* Security Events Tab */}
            {activeTab === 'security' && (
              <div className="space-y-6">
                {/* Security Events Table */}
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-h3 font-semibold text-white">Security Events</h3>
                    <div className="flex gap-2">
                      <select
                        value={securityFilters.severity}
                        onChange={(e) => setSecurityFilters({...securityFilters, severity: e.target.value})}
                        className="px-3 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-och-mint"
                      >
                        <option value="">All Severities</option>
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                        <option value="info">Info</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-och-steel/20">
                      <thead className="bg-och-midnight/50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Detected
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Event Type
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Severity
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Description
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Source IP
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                        {securityEvents.map((event) => (
                          <tr key={event.id} className="hover:bg-och-steel/5">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                              {new Date(event.detected_at).toLocaleString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="text-sm text-white capitalize">
                                {event.event_type.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getSeverityColor(event.severity)}`}>
                                {event.severity}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-white max-w-xs truncate">
                              {event.description}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                              {event.user_ip}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <Badge variant={event.is_resolved ? 'mint' : 'orange'}>
                                {event.is_resolved ? 'Resolved' : 'Open'}
                              </Badge>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <div className="flex gap-2">
                                <Button variant="ghost" size="sm">
                                  <Eye className="h-3 w-3 mr-1" />
                                  View
                                </Button>
                                {!event.is_resolved && (
                                  <Button variant="ghost" size="sm">
                                    <CheckCircle className="h-3 w-3 mr-1" />
                                    Resolve
                                  </Button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              </div>
            )}

            {/* Reports Tab */}
            {activeTab === 'reports' && (
              <div className="space-y-6">
                <Card className="p-6 bg-och-midnight border border-och-steel/20">
                  <h3 className="text-h3 font-semibold text-white mb-4">Generate Compliance Reports</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 border border-och-steel/20 rounded-lg">
                      <div className="flex items-center gap-3 mb-3">
                        <Shield className="h-6 w-6 text-och-defender" />
                        <h4 className="text-white font-medium">PCI-DSS Report</h4>
                      </div>
                      <p className="text-sm text-och-steel mb-4">
                        Payment Card Industry Data Security Standard compliance report
                      </p>
                      <Button 
                        onClick={() => generateComplianceReport('pci_dss')}
                        className="w-full"
                      >
                        Generate Report
                      </Button>
                    </div>

                    <div className="p-4 border border-och-steel/20 rounded-lg">
                      <div className="flex items-center gap-3 mb-3">
                        <Globe className="h-6 w-6 text-och-mint" />
                        <h4 className="text-white font-medium">GDPR Report</h4>
                      </div>
                      <p className="text-sm text-och-steel mb-4">
                        General Data Protection Regulation compliance report
                      </p>
                      <Button 
                        onClick={() => generateComplianceReport('gdpr')}
                        className="w-full"
                      >
                        Generate Report
                      </Button>
                    </div>

                    <div className="p-4 border border-och-steel/20 rounded-lg">
                      <div className="flex items-center gap-3 mb-3">
                        <FileText className="h-6 w-6 text-och-gold" />
                        <h4 className="text-white font-medium">Audit Trail Report</h4>
                      </div>
                      <p className="text-sm text-och-steel mb-4">
                        Comprehensive audit trail and activity report
                      </p>
                      <Button 
                        onClick={() => generateComplianceReport('audit_trail')}
                        className="w-full"
                      >
                        Generate Report
                      </Button>
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