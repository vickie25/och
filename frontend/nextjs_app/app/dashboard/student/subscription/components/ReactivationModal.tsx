'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { X, RefreshCw, CreditCard, AlertTriangle, CheckCircle2, Clock } from 'lucide-react'
import { formatFromKES } from '@/lib/currency'

interface EnhancedSubscription {
  id: string
  plan_version: {
    name: string
    price_monthly: number
    price_annual: number
  }
  status: string
  billing_cycle: 'monthly' | 'annual'
  suspended_at: string
  reactivation_window_end: string
  can_reactivate: boolean
}

interface ReactivationModalProps {
  subscription: EnhancedSubscription
  onClose: () => void
  onSuccess: () => void
}

const PAYMENT_METHODS = [
  { id: 'card', name: 'Credit/Debit Card', icon: CreditCard },
  { id: 'paystack', name: 'Paystack', icon: CreditCard },
  { id: 'bank_transfer', name: 'Bank Transfer', icon: CreditCard }
]

export default function ReactivationModal({ 
  subscription, 
  onClose, 
  onSuccess 
}: ReactivationModalProps) {
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState('card')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedCountry = 'KE' // Get from user context
  const suspendedDate = new Date(subscription.suspended_at).toLocaleDateString()
  const windowEndDate = new Date(subscription.reactivation_window_end).toLocaleDateString()
  const daysLeft = Math.ceil((new Date(subscription.reactivation_window_end).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  
  // Calculate outstanding amount (this would come from API in real implementation)
  const outstandingAmount = subscription.billing_cycle === 'annual' 
    ? subscription.plan_version.price_annual 
    : subscription.plan_version.price_monthly

  const handleReactivate = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      await apiGateway.post('/enhanced-billing/subscription/reactivate/', {
        payment_method: selectedPaymentMethod
      })
      onSuccess()
    } catch (err: any) {
      setError(err?.message || 'Failed to reactivate subscription')
    } finally {
      setIsLoading(false)
    }
  }

  if (!subscription.can_reactivate) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-och-dark border border-och-steel/20 rounded-lg max-w-md w-full">
          <div className="p-6 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <X className="w-8 h-8 text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Reactivation Window Expired</h2>
            <p className="text-och-steel text-sm mb-6">
              The 30-day reactivation window has expired. You'll need to create a new subscription.
            </p>
            <Button variant="mint" onClick={onClose} className="w-full">
              Create New Subscription
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-och-dark border border-och-steel/20 rounded-lg max-w-2xl w-full">
        <div className="p-6 border-b border-och-steel/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Reactivate Subscription</h2>
              <p className="text-och-steel text-sm mt-1">
                Restore your {subscription.plan_version.name} subscription
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <Card className="p-4 bg-red-500/10 border-red-500/30">
              <div className="flex items-center gap-2 text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <p className="text-sm">{error}</p>
              </div>
            </Card>
          )}

          {/* Reactivation Window Status */}
          <Card className="p-4 bg-yellow-500/10 border-yellow-500/30">
            <div className="flex items-start gap-3">
              <Clock className="w-5 h-5 text-yellow-400 mt-0.5" />
              <div>
                <h3 className="font-semibold text-yellow-400 mb-1">Reactivation Window</h3>
                <p className="text-sm text-och-steel mb-2">
                  Your subscription was suspended on {suspendedDate}. You have until {windowEndDate} to reactivate.
                </p>
                <div className="flex items-center gap-2">
                  <Badge variant={daysLeft <= 3 ? 'destructive' : 'gold'} className="text-xs">
                    {daysLeft} days left
                  </Badge>
                </div>
              </div>
            </div>
          </Card>

          {/* Outstanding Balance */}
          <Card className="p-4 bg-och-steel/5">
            <h3 className="font-semibold text-white mb-3">Outstanding Balance</h3>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-och-steel">
                  {subscription.plan_version.name} - {subscription.billing_cycle} billing
                </p>
                <p className="text-xs text-och-steel mt-1">
                  Payment failed during last billing cycle
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-och-mint">
                  {formatFromKES(outstandingAmount, selectedCountry)}
                </p>
                <p className="text-xs text-och-steel">Due now</p>
              </div>
            </div>
          </Card>

          {/* Payment Method Selection */}
          <div>
            <h3 className="font-semibold text-white mb-3">Payment Method</h3>
            <div className="space-y-3">
              {PAYMENT_METHODS.map(method => {
                const Icon = method.icon
                const isSelected = selectedPaymentMethod === method.id
                
                return (
                  <Card
                    key={method.id}
                    className={`p-4 cursor-pointer transition-all ${
                      isSelected
                        ? 'border-och-mint bg-och-mint/10'
                        : 'border-och-steel/20 hover:border-och-steel/40'
                    }`}
                    onClick={() => setSelectedPaymentMethod(method.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded-full border-2 ${
                        isSelected
                          ? 'border-och-mint bg-och-mint'
                          : 'border-och-steel'
                      }`}>
                        {isSelected && (
                          <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                        )}
                      </div>
                      <Icon className="w-5 h-5 text-och-steel" />
                      <span className="text-white font-medium">{method.name}</span>
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>

          {/* What Happens After Reactivation */}
          <Card className="p-4 bg-green-500/10 border-green-500/30">
            <h4 className="font-semibold text-green-400 mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              What happens after reactivation:
            </h4>
            <div className="space-y-2 text-sm text-och-steel">
              <p>• Your subscription will be immediately restored to active status</p>
              <p>• Full access to all {subscription.plan_version.name} features will be restored</p>
              <p>• Your billing cycle will resume as normal</p>
              <p>• All your data and progress has been preserved</p>
              <p>• Future payments will be processed automatically</p>
            </div>
          </Card>

          {/* Urgency Warning */}
          {daysLeft <= 3 && (
            <Card className="p-4 bg-red-500/10 border-red-500/30">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5" />
                <div className="text-sm">
                  <p className="text-red-400 font-medium mb-1">Urgent: Reactivation Window Closing</p>
                  <p className="text-och-steel">
                    You only have {daysLeft} day{daysLeft !== 1 ? 's' : ''} left to reactivate your subscription. 
                    After {windowEndDate}, you'll need to create a new subscription and may lose some benefits.
                  </p>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* Actions */}
        <div className="p-6 border-t border-och-steel/20">
          <div className="flex items-center justify-end gap-3">
            <Button variant="outline" onClick={onClose} disabled={isLoading}>
              Cancel
            </Button>
            <Button
              variant="mint"
              onClick={handleReactivate}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing Payment...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" />
                  Pay {formatFromKES(outstandingAmount, selectedCountry)} & Reactivate
                </div>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}