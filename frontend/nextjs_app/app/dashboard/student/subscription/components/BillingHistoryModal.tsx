'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { X, Download, Calendar, DollarSign, History, FileText, ArrowUpDown } from 'lucide-react'
import { formatFromKES } from '@/lib/currency'

interface BillingPeriod {
  id: string
  period_start: string
  period_end: string
  status: 'upcoming' | 'current' | 'completed' | 'failed'
  amount: number
  currency: string
  payment_attempted_at?: string
  payment_completed_at?: string
  payment_failed_at?: string
}

interface SubscriptionChange {
  id: string
  change_type: string
  old_value: string
  new_value: string
  proration_credit?: number
  proration_charge?: number
  net_proration?: number
  reason: string
  description: string
  created_at: string
  created_by_email?: string
}

interface EnhancedSubscription {
  id: string
  plan_version: {
    name: string
  }
}

interface BillingHistoryModalProps {
  subscription: EnhancedSubscription
  billingPeriods: BillingPeriod[]
  changeHistory: SubscriptionChange[]
  onClose: () => void
}

const STATUS_COLORS = {
  upcoming: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  current: 'bg-green-500/20 text-green-400 border-green-500/30',
  completed: 'bg-green-500/20 text-green-400 border-green-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30'
}

const CHANGE_TYPE_LABELS = {
  plan_change: 'Plan Change',
  status_change: 'Status Change',
  billing_cycle_change: 'Billing Cycle Change',
  cancellation: 'Cancellation',
  reactivation: 'Reactivation',
  trial_conversion: 'Trial Conversion',
  proration_adjustment: 'Proration Adjustment'
}

export default function BillingHistoryModal({ 
  subscription, 
  billingPeriods, 
  changeHistory, 
  onClose 
}: BillingHistoryModalProps) {
  const [activeTab, setActiveTab] = useState<'billing' | 'changes'>('billing')
  const selectedCountry = 'KE' // Get from user context

  const sortedBillingPeriods = [...billingPeriods].sort((a, b) => 
    new Date(b.period_start).getTime() - new Date(a.period_start).getTime()
  )

  const sortedChangeHistory = [...changeHistory].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  )

  const handleDownloadInvoice = (periodId: string) => {
    // This would trigger invoice download
    console.log('Download invoice for period:', periodId)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-och-dark border border-och-steel/20 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b border-och-steel/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Billing History</h2>
              <p className="text-och-steel text-sm mt-1">
                View your billing periods, invoices, and subscription changes
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-och-steel/20">
          <div className="flex">
            <button
              onClick={() => setActiveTab('billing')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'billing'
                  ? 'border-och-mint text-och-mint'
                  : 'border-transparent text-och-steel hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4" />
                Billing Periods
              </div>
            </button>
            <button
              onClick={() => setActiveTab('changes')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'changes'
                  ? 'border-och-mint text-och-mint'
                  : 'border-transparent text-och-steel hover:text-white'
              }`}
            >
              <div className="flex items-center gap-2">
                <History className="w-4 h-4" />
                Change History
              </div>
            </button>
          </div>
        </div>

        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {activeTab === 'billing' ? (
            <div className="space-y-4">
              {sortedBillingPeriods.length === 0 ? (
                <div className="text-center py-8">
                  <Calendar className="w-12 h-12 text-och-steel mx-auto mb-4" />
                  <p className="text-och-steel">No billing periods found</p>
                </div>
              ) : (
                sortedBillingPeriods.map(period => (
                  <Card key={period.id} className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-white">
                            {formatDate(period.period_start)} - {formatDate(period.period_end)}
                          </h3>
                          <div className={`px-2 py-1 rounded text-xs font-medium border ${STATUS_COLORS[period.status]}`}>
                            {period.status.toUpperCase()}
                          </div>
                        </div>
                        <p className="text-sm text-och-steel">
                          Billing period for {subscription.plan_version.name}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xl font-bold text-white">
                          {formatFromKES(period.amount, selectedCountry)}
                        </p>
                        <p className="text-xs text-och-steel">{period.currency}</p>
                      </div>
                    </div>

                    {/* Payment Timeline */}
                    <div className="space-y-2 text-xs text-och-steel">
                      {period.payment_attempted_at && (
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-yellow-400 rounded-full" />
                          <span>Payment attempted: {formatDateTime(period.payment_attempted_at)}</span>
                        </div>
                      )}
                      {period.payment_completed_at && (
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full" />
                          <span>Payment completed: {formatDateTime(period.payment_completed_at)}</span>
                        </div>
                      )}
                      {period.payment_failed_at && (
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-red-400 rounded-full" />
                          <span>Payment failed: {formatDateTime(period.payment_failed_at)}</span>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    {period.status === 'completed' && (
                      <div className="mt-4 pt-3 border-t border-och-steel/20">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadInvoice(period.id)}
                        >
                          <Download className="w-3 h-3 mr-2" />
                          Download Invoice
                        </Button>
                      </div>
                    )}
                  </Card>
                ))
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {sortedChangeHistory.length === 0 ? (
                <div className="text-center py-8">
                  <History className="w-12 h-12 text-och-steel mx-auto mb-4" />
                  <p className="text-och-steel">No subscription changes found</p>
                </div>
              ) : (
                sortedChangeHistory.map(change => (
                  <Card key={change.id} className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-white">
                            {CHANGE_TYPE_LABELS[change.change_type as keyof typeof CHANGE_TYPE_LABELS] || change.change_type}
                          </h3>
                          <Badge variant="steel" className="text-xs">
                            {change.reason.replace('_', ' ')}
                          </Badge>
                        </div>
                        <p className="text-sm text-och-steel mb-2">
                          {change.description}
                        </p>
                        <div className="text-xs text-och-steel">
                          <p>{formatDateTime(change.created_at)}</p>
                          {change.created_by_email && (
                            <p>by {change.created_by_email}</p>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Change Details */}
                    {(change.old_value || change.new_value) && (
                      <div className="mb-3 p-3 bg-och-steel/5 rounded">
                        <div className="flex items-center gap-2 mb-2">
                          <ArrowUpDown className="w-3 h-3 text-och-steel" />
                          <span className="text-xs font-medium text-och-steel">Change Details</span>
                        </div>
                        <div className="grid grid-cols-2 gap-4 text-xs">
                          {change.old_value && (
                            <div>
                              <p className="text-och-steel mb-1">From:</p>
                              <p className="text-white">{change.old_value}</p>
                            </div>
                          )}
                          {change.new_value && (
                            <div>
                              <p className="text-och-steel mb-1">To:</p>
                              <p className="text-white">{change.new_value}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Proration Details */}
                    {(change.proration_credit || change.proration_charge || change.net_proration) && (
                      <div className="p-3 bg-och-mint/5 border border-och-mint/20 rounded">
                        <div className="flex items-center gap-2 mb-2">
                          <DollarSign className="w-3 h-3 text-och-mint" />
                          <span className="text-xs font-medium text-och-mint">Proration Details</span>
                        </div>
                        <div className="space-y-1 text-xs">
                          {change.proration_credit && (
                            <div className="flex justify-between">
                              <span className="text-och-steel">Credit:</span>
                              <span className="text-green-400">
                                -{formatFromKES(change.proration_credit, selectedCountry)}
                              </span>
                            </div>
                          )}
                          {change.proration_charge && (
                            <div className="flex justify-between">
                              <span className="text-och-steel">Charge:</span>
                              <span className="text-white">
                                +{formatFromKES(change.proration_charge, selectedCountry)}
                              </span>
                            </div>
                          )}
                          {change.net_proration !== undefined && (
                            <div className="flex justify-between font-medium pt-1 border-t border-och-steel/20">
                              <span className="text-white">Net:</span>
                              <span className="text-och-mint">
                                {change.net_proration === 0 
                                  ? 'No charge' 
                                  : formatFromKES(change.net_proration, selectedCountry)
                                }
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </Card>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-och-steel/20">
          <div className="flex items-center justify-between">
            <div className="text-sm text-och-steel">
              {activeTab === 'billing' 
                ? `${sortedBillingPeriods.length} billing period${sortedBillingPeriods.length !== 1 ? 's' : ''}`
                : `${sortedChangeHistory.length} change${sortedChangeHistory.length !== 1 ? 's' : ''}`
              }
            </div>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}