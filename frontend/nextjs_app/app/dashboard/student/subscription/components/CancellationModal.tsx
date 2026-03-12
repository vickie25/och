'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { X, AlertTriangle, Calendar, XCircle } from 'lucide-react'

interface EnhancedSubscription {
  id: string
  plan_version: {
    name: string
    price_monthly: number
    price_annual: number
  }
  status: string
  billing_cycle: 'monthly' | 'annual'
  current_period_end: string
  days_until_period_end: number
}

interface CancellationModalProps {
  subscription: EnhancedSubscription
  onClose: () => void
  onSuccess: () => void
}

export default function CancellationModal({ 
  subscription, 
  onClose, 
  onSuccess 
}: CancellationModalProps) {
  const [cancellationType, setCancellationType] = useState<'immediate' | 'end_of_period'>('end_of_period')
  const [reason, setReason] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCancel = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      await apiGateway.post('/enhanced-billing/subscription/cancel/', {
        type: cancellationType,
        reason: reason || 'User requested cancellation'
      })
      onSuccess()
    } catch (err: any) {
      setError(err?.message || 'Failed to cancel subscription')
    } finally {
      setIsLoading(false)
    }
  }

  const periodEndDate = new Date(subscription.current_period_end).toLocaleDateString()

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-och-dark border border-och-steel/20 rounded-lg max-w-2xl w-full">
        <div className="p-6 border-b border-och-steel/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Cancel Subscription</h2>
              <p className="text-och-steel text-sm mt-1">
                Choose how you'd like to cancel your {subscription.plan_version.name} subscription
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

          {/* Cancellation Options */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Cancellation Options</h3>
            
            {/* End of Period Option (Recommended) */}
            <Card
              className={`p-4 cursor-pointer transition-all ${
                cancellationType === 'end_of_period'
                  ? 'border-och-mint bg-och-mint/10'
                  : 'border-och-steel/20 hover:border-och-steel/40'
              }`}
              onClick={() => setCancellationType('end_of_period')}
            >
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    cancellationType === 'end_of_period'
                      ? 'border-och-mint bg-och-mint'
                      : 'border-och-steel'
                  }`}>
                    {cancellationType === 'end_of_period' && (
                      <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                    )}
                  </div>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h4 className="font-semibold text-white">Cancel at Period End</h4>
                    <Badge variant="mint" className="text-xs">Recommended</Badge>
                  </div>
                  <p className="text-sm text-och-steel mb-2">
                    Your subscription will be canceled on {periodEndDate}. You'll continue to have 
                    full access to all features until then.
                  </p>
                  <div className="flex items-center gap-2 text-xs text-och-steel">
                    <Calendar className="w-3 h-3" />
                    <span>{subscription.days_until_period_end} days of access remaining</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Immediate Cancellation Option */}
            <Card
              className={`p-4 cursor-pointer transition-all ${
                cancellationType === 'immediate'
                  ? 'border-red-500 bg-red-500/10'
                  : 'border-och-steel/20 hover:border-och-steel/40'
              }`}
              onClick={() => setCancellationType('immediate')}
            >
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  <div className={`w-4 h-4 rounded-full border-2 ${
                    cancellationType === 'immediate'
                      ? 'border-red-500 bg-red-500'
                      : 'border-och-steel'
                  }`}>
                    {cancellationType === 'immediate' && (
                      <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                    )}
                  </div>
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-white mb-2">Cancel Immediately</h4>
                  <p className="text-sm text-och-steel mb-2">
                    Your subscription will be canceled right away and access will be revoked immediately.
                    You may be eligible for a prorated refund based on our refund policy.
                  </p>
                  <div className="flex items-center gap-2 text-xs text-red-400">
                    <XCircle className="w-3 h-3" />
                    <span>Access ends immediately</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Reason for Cancellation */}
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Reason for cancellation (optional)
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Help us improve by telling us why you're canceling..."
              className="w-full p-3 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/60 focus:border-och-mint focus:outline-none resize-none"
              rows={3}
              maxLength={500}
            />
            <p className="text-xs text-och-steel mt-1">{reason.length}/500 characters</p>
          </div>

          {/* Impact Summary */}
          <Card className="p-4 bg-och-steel/5">
            <h4 className="font-semibold text-white mb-3">What happens when you cancel:</h4>
            <div className="space-y-2 text-sm text-och-steel">
              {cancellationType === 'end_of_period' ? (
                <>
                  <p>• You'll keep full access until {periodEndDate}</p>
                  <p>• No refund will be processed (you've paid for the full period)</p>
                  <p>• You can reactivate anytime before {periodEndDate}</p>
                  <p>• Your data and progress will be preserved</p>
                </>
              ) : (
                <>
                  <p>• Access will be revoked immediately</p>
                  <p>• You may receive a prorated refund for unused time</p>
                  <p>• Your data and progress will be preserved for 30 days</p>
                  <p>• You can create a new subscription anytime</p>
                </>
              )}
            </div>
          </Card>

          {/* Warning for Immediate Cancellation */}
          {cancellationType === 'immediate' && (
            <Card className="p-4 bg-red-500/10 border-red-500/30">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5" />
                <div className="text-sm">
                  <p className="text-red-400 font-medium mb-1">Immediate Cancellation Warning</p>
                  <p className="text-och-steel">
                    You will lose access to all premium features immediately, including any ongoing 
                    mentorship sessions, AI coach conversations, and mission progress. This action 
                    cannot be undone.
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
              Keep Subscription
            </Button>
            <Button
              variant={cancellationType === 'immediate' ? 'destructive' : 'outline'}
              onClick={handleCancel}
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Canceling...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  {cancellationType === 'immediate' ? 'Cancel Immediately' : 'Cancel at Period End'}
                </div>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}