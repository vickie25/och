'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useAuth } from '@/hooks/useAuth'
import { apiGateway } from '@/services/apiGateway'
import { 
  CheckCircle2, CreditCard, Calendar, AlertCircle, Clock, 
  RefreshCw, XCircle, ArrowRight, DollarSign, History 
} from 'lucide-react'
import { formatFromKES } from '@/lib/currency'
import PlanChangeModal from './components/PlanChangeModal'
import CancellationModal from './components/CancellationModal'
import ReactivationModal from './components/ReactivationModal'
import PaymentMethodModal from './components/PaymentMethodModal'
import BillingHistoryModal from './components/BillingHistoryModal'

interface EnhancedSubscription {
  id: string
  user_email: string
  plan_version: {
    id: string
    plan_id: string
    version: number
    name: string
    price_monthly: number
    price_annual: number
    billing_cycles: string[]
    trial_days: number
    tier_access: string[]
    track_access: string[]
    feature_flags: Record<string, boolean>
    mentorship_credits: number
    status: string
  }
  status: 'TRIAL' | 'ACTIVE' | 'PAST_DUE' | 'SUSPENDED' | 'CANCELED' | 'EXPIRED'
  billing_cycle: 'monthly' | 'annual'
  current_period_start: string
  current_period_end: string
  trial_start?: string
  trial_end?: string
  canceled_at?: string
  cancellation_type?: 'immediate' | 'end_of_period'
  cancel_at_period_end: boolean
  suspended_at?: string
  reactivation_window_end?: string
  days_until_period_end: number
  can_reactivate: boolean
  created_at: string
  updated_at: string
}

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

interface DunningSequence {
  id: string
  current_attempt: number
  max_attempts: number
  next_retry_at: string
  grace_period_end: string
}

interface SubscriptionStatus {
  subscription: EnhancedSubscription
  billing_periods: BillingPeriod[]
  change_history: any[]
  active_dunning?: DunningSequence
}

interface PlanVersion {
  id: string
  plan_id: string
  version: number
  name: string
  price_monthly: number
  price_annual: number
  billing_cycles: string[]
  trial_days: number
  tier_access: string[]
  track_access: string[]
  feature_flags: Record<string, boolean>
  mentorship_credits: number
  status: string
}

const STATUS_COLORS = {
  TRIAL: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  ACTIVE: 'bg-green-500/20 text-green-400 border-green-500/30',
  PAST_DUE: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  SUSPENDED: 'bg-red-500/20 text-red-400 border-red-500/30',
  CANCELED: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  EXPIRED: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
}

const STATUS_DESCRIPTIONS = {
  TRIAL: 'Free trial period - no payment required',
  ACTIVE: 'Current billing period paid, full access granted',
  PAST_DUE: 'Payment failed, retry in progress',
  SUSPENDED: 'All payment retries failed, access restricted',
  CANCELED: 'User-initiated cancellation, access continues until period end',
  EXPIRED: 'Billing period ended or reactivation window closed'
}

export default function EnhancedSubscriptionClient() {
  const { user } = useAuth()
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null)
  const [availablePlans, setAvailablePlans] = useState<PlanVersion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  
  // Modal states
  const [showPlanChange, setShowPlanChange] = useState(false)
  const [showCancellation, setShowCancellation] = useState(false)
  const [showReactivation, setShowReactivation] = useState(false)
  const [showPaymentMethod, setShowPaymentMethod] = useState(false)
  const [showBillingHistory, setShowBillingHistory] = useState(false)

  const selectedCountry = user?.country?.toUpperCase() || 'KE'

  useEffect(() => {
    if (user?.id) {
      loadSubscriptionData()
    }
  }, [user?.id])

  const loadSubscriptionData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [statusRes, plansRes] = await Promise.all([
        apiGateway.get('/enhanced-billing/subscription/status'),
        apiGateway.get('/enhanced-billing/plans/available')
      ])
      
      setSubscriptionStatus(statusRes as SubscriptionStatus)
      setAvailablePlans(plansRes.plans || [])
    } catch (err: any) {
      if (err.status === 404) {
        // No subscription exists - show plan selection
        const plansRes = await apiGateway.get('/enhanced-billing/plans/available')
        setAvailablePlans(plansRes.plans || [])
        setSubscriptionStatus(null)
      } else {
        setError(err?.message || 'Failed to load subscription data')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateSubscription = async (planId: string, billingCycle: 'monthly' | 'annual') => {
    setActionLoading(true)
    setError(null)
    try {
      await apiGateway.post('/enhanced-billing/subscription/create/', {
        plan_id: planId,
        billing_cycle: billingCycle
      })
      setSuccess('Trial subscription created successfully!')
      await loadSubscriptionData()
    } catch (err: any) {
      setError(err?.message || 'Failed to create subscription')
    } finally {
      setActionLoading(false)
    }
  }

  const handleConvertTrial = async (paymentMethod: string) => {
    setActionLoading(true)
    setError(null)
    try {
      await apiGateway.post('/enhanced-billing/subscription/convert-trial/', {
        payment_method: paymentMethod
      })
      setSuccess('Trial converted to active subscription!')
      await loadSubscriptionData()
    } catch (err: any) {
      setError(err?.message || 'Failed to convert trial')
    } finally {
      setActionLoading(false)
    }
  }

  const clearMessages = () => {
    setError(null)
    setSuccess(null)
  }

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
          <p className="text-och-steel text-sm">Loading subscription data...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full py-6 px-4 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-4xl font-bold mb-2 text-och-mint">Subscription Management</h1>
        <p className="text-och-steel">Manage your subscription, billing, and plan details</p>
      </div>

      {/* Status Messages */}
      {error && (
        <Card className="p-4 bg-red-500/10 border-red-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-red-400">
              <AlertCircle className="w-4 h-4" />
              <p className="text-sm">{error}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={clearMessages}>
              <XCircle className="w-4 h-4" />
            </Button>
          </div>
        </Card>
      )}

      {success && (
        <Card className="p-4 bg-green-500/10 border-green-500/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-green-400">
              <CheckCircle2 className="w-4 h-4" />
              <p className="text-sm">{success}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={clearMessages}>
              <XCircle className="w-4 h-4" />
            </Button>
          </div>
        </Card>
      )}

      {/* Current Subscription Status */}
      {subscriptionStatus ? (
        <Card className="p-6 border border-och-steel/20">
          <div className="flex items-start justify-between mb-6">
            <div>
              <p className="text-sm text-och-steel mb-1">Current Subscription</p>
              <h2 className="text-3xl font-bold text-white mb-2">
                {subscriptionStatus.subscription.plan_version.name}
              </h2>
              <div className="flex items-center gap-3">
                <div className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[subscriptionStatus.subscription.status]}`}>
                  {subscriptionStatus.subscription.status}
                </div>
                <div className="text-sm text-och-steel">
                  {subscriptionStatus.subscription.billing_cycle} billing
                </div>
              </div>
              <p className="text-xs text-och-steel mt-2">
                {STATUS_DESCRIPTIONS[subscriptionStatus.subscription.status]}
              </p>
            </div>
            
            <div className="text-right">
              {subscriptionStatus.subscription.status === 'TRIAL' && subscriptionStatus.subscription.trial_end && (
                <div>
                  <p className="text-sm text-och-steel mb-1">Trial Ends</p>
                  <p className="text-white font-medium">
                    {new Date(subscriptionStatus.subscription.trial_end).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-och-steel">
                    {subscriptionStatus.subscription.days_until_period_end} days left
                  </p>
                </div>
              )}
              
              {subscriptionStatus.subscription.status === 'ACTIVE' && (
                <div>
                  <p className="text-sm text-och-steel mb-1">Next Billing</p>
                  <p className="text-white font-medium">
                    {new Date(subscriptionStatus.subscription.current_period_end).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-och-steel">
                    {subscriptionStatus.subscription.days_until_period_end} days left
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Dunning Status */}
          {subscriptionStatus.active_dunning && (
            <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-yellow-400" />
                <p className="text-sm font-medium text-yellow-400">Payment Retry in Progress</p>
              </div>
              <p className="text-xs text-och-steel mb-2">
                Attempt {subscriptionStatus.active_dunning.current_attempt} of {subscriptionStatus.active_dunning.max_attempts}
              </p>
              <p className="text-xs text-och-steel">
                Next retry: {new Date(subscriptionStatus.active_dunning.next_retry_at).toLocaleString()}
              </p>
              <p className="text-xs text-och-steel">
                Grace period ends: {new Date(subscriptionStatus.active_dunning.grace_period_end).toLocaleString()}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            {subscriptionStatus.subscription.status === 'TRIAL' && (
              <Button 
                variant="mint" 
                onClick={() => setShowPaymentMethod(true)}
                disabled={actionLoading}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Convert to Paid Plan
              </Button>
            )}
            
            {subscriptionStatus.subscription.status === 'ACTIVE' && (
              <>
                <Button 
                  variant="outline" 
                  onClick={() => setShowPlanChange(true)}
                  disabled={actionLoading}
                >
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Change Plan
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => setShowCancellation(true)}
                  disabled={actionLoading}
                >
                  <XCircle className="w-4 h-4 mr-2" />
                  Cancel Subscription
                </Button>
              </>
            )}
            
            {subscriptionStatus.subscription.status === 'SUSPENDED' && subscriptionStatus.subscription.can_reactivate && (
              <Button 
                variant="mint" 
                onClick={() => setShowReactivation(true)}
                disabled={actionLoading}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Reactivate Subscription
              </Button>
            )}
            
            {['ACTIVE', 'PAST_DUE', 'CANCELED'].includes(subscriptionStatus.subscription.status) && (
              <Button 
                variant="outline" 
                onClick={() => setShowPaymentMethod(true)}
                disabled={actionLoading}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Update Payment Method
              </Button>
            )}
            
            <Button 
              variant="outline" 
              onClick={() => setShowBillingHistory(true)}
            >
              <History className="w-4 h-4 mr-2" />
              Billing History
            </Button>
          </div>
        </Card>
      ) : (
        /* No Subscription - Show Plan Selection */
        <Card className="p-6 border border-och-steel/20">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">Choose Your Plan</h2>
            <p className="text-och-steel">Start with a free trial, upgrade anytime</p>
          </div>
        </Card>
      )}

      {/* Available Plans */}
      {(!subscriptionStatus || subscriptionStatus.subscription.status === 'EXPIRED') && availablePlans.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {availablePlans.map(plan => {
            const isRecommended = plan.plan_id === 'premium'
            const monthlyPrice = plan.price_monthly || 0
            const annualPrice = plan.price_annual || (monthlyPrice * 12)
            
            return (
              <div
                key={plan.id}
                className={`relative p-6 rounded-lg border-2 transition-all ${
                  isRecommended
                    ? 'bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40'
                    : 'bg-gradient-to-br from-och-steel/20 to-och-steel/5 border-och-steel/30'
                }`}
              >
                {isRecommended && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge variant="gold" className="text-xs font-bold px-3 py-1">
                      RECOMMENDED
                    </Badge>
                  </div>
                )}

                <div className="mt-4">
                  <h3 className="text-2xl font-bold text-white mb-4">{plan.name}</h3>

                  {monthlyPrice === 0 ? (
                    <div className="mb-6">
                      <p className="text-4xl font-bold text-white">Free</p>
                      <p className="text-sm text-och-steel">{plan.trial_days}-day trial</p>
                    </div>
                  ) : (
                    <div className="mb-6">
                      <div className="flex items-baseline gap-2 mb-2">
                        <p className="text-3xl font-bold text-white">
                          {formatFromKES(monthlyPrice, selectedCountry)}
                        </p>
                        <span className="text-sm text-och-steel">/month</span>
                      </div>
                      {plan.billing_cycles.includes('annual') && (
                        <div className="text-xs text-och-steel">
                          <p>or {formatFromKES(annualPrice, selectedCountry)}/year</p>
                          <p className="text-och-mint">Save {Math.round((1 - (annualPrice / (monthlyPrice * 12))) * 100)}%</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Features */}
                  <div className="space-y-2 mb-6 min-h-[120px]">
                    {plan.feature_flags.mentorship && (
                      <p className="text-xs text-white flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-och-mint" />
                        Human Mentorship ({plan.mentorship_credits} credits/month)
                      </p>
                    )}
                    {plan.feature_flags.missions && (
                      <p className="text-xs text-white flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-och-mint" />
                        Full Mission Access
                      </p>
                    )}
                    {plan.feature_flags.ai_coach && (
                      <p className="text-xs text-white flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-och-mint" />
                        AI Coach
                      </p>
                    )}
                    {plan.feature_flags.talentscope && (
                      <p className="text-xs text-white flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-och-mint" />
                        TalentScope Analytics
                      </p>
                    )}
                    {plan.feature_flags.marketplace && (
                      <p className="text-xs text-white flex items-center gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-och-mint" />
                        Employer Contact
                      </p>
                    )}
                    <p className="text-xs text-white flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-och-mint" />
                      {plan.tier_access.length} Tier{plan.tier_access.length > 1 ? 's' : ''} Access
                    </p>
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-2">
                    <Button
                      variant={isRecommended ? 'mint' : 'outline'}
                      className="w-full"
                      disabled={actionLoading}
                      onClick={() => handleCreateSubscription(plan.plan_id, 'monthly')}
                    >
                      Start {plan.trial_days}-Day Trial
                    </Button>
                    {plan.billing_cycles.includes('annual') && monthlyPrice > 0 && (
                      <Button
                        variant="outline"
                        className="w-full text-xs"
                        disabled={actionLoading}
                        onClick={() => handleCreateSubscription(plan.plan_id, 'annual')}
                      >
                        Annual Billing (Save {Math.round((1 - (annualPrice / (monthlyPrice * 12))) * 100)}%)
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Modals */}
      {showPlanChange && subscriptionStatus && (
        <PlanChangeModal
          currentSubscription={subscriptionStatus.subscription}
          availablePlans={availablePlans}
          onClose={() => setShowPlanChange(false)}
          onSuccess={() => {
            setShowPlanChange(false)
            loadSubscriptionData()
          }}
        />
      )}

      {showCancellation && subscriptionStatus && (
        <CancellationModal
          subscription={subscriptionStatus.subscription}
          onClose={() => setShowCancellation(false)}
          onSuccess={() => {
            setShowCancellation(false)
            loadSubscriptionData()
          }}
        />
      )}

      {showReactivation && subscriptionStatus && (
        <ReactivationModal
          subscription={subscriptionStatus.subscription}
          onClose={() => setShowReactivation(false)}
          onSuccess={() => {
            setShowReactivation(false)
            loadSubscriptionData()
          }}
        />
      )}

      {showPaymentMethod && (
        <PaymentMethodModal
          subscription={subscriptionStatus?.subscription}
          onClose={() => setShowPaymentMethod(false)}
          onSuccess={() => {
            setShowPaymentMethod(false)
            loadSubscriptionData()
          }}
          onTrialConvert={subscriptionStatus?.subscription.status === 'TRIAL' ? handleConvertTrial : undefined}
        />
      )}

      {showBillingHistory && subscriptionStatus && (
        <BillingHistoryModal
          subscription={subscriptionStatus.subscription}
          billingPeriods={subscriptionStatus.billing_periods}
          changeHistory={subscriptionStatus.change_history}
          onClose={() => setShowBillingHistory(false)}
        />
      )}
    </div>
  )
}