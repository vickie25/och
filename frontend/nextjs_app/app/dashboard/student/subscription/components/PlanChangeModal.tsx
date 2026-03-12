'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { X, ArrowRight, DollarSign, Calculator, AlertTriangle } from 'lucide-react'
import { formatFromKES } from '@/lib/currency'

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

interface EnhancedSubscription {
  id: string
  plan_version: PlanVersion
  status: string
  billing_cycle: 'monthly' | 'annual'
  current_period_start: string
  current_period_end: string
  days_until_period_end: number
}

interface ProrationPreview {
  credit_amount: number
  charge_amount: number
  net_charge: number
  remaining_days: number
}

interface PlanChangeModalProps {
  currentSubscription: EnhancedSubscription
  availablePlans: PlanVersion[]
  onClose: () => void
  onSuccess: () => void
}

export default function PlanChangeModal({ 
  currentSubscription, 
  availablePlans, 
  onClose, 
  onSuccess 
}: PlanChangeModalProps) {
  const [selectedPlan, setSelectedPlan] = useState<PlanVersion | null>(null)
  const [prorationPreview, setProrationPreview] = useState<ProrationPreview | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isCalculating, setIsCalculating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const currentPlan = currentSubscription.plan_version
  const selectedCountry = 'KE' // Get from user context

  // Filter out current plan and inactive plans
  const eligiblePlans = availablePlans.filter(plan => 
    plan.plan_id !== currentPlan.plan_id && plan.status === 'active'
  )

  useEffect(() => {
    if (selectedPlan) {
      calculateProration()
    }
  }, [selectedPlan])

  const calculateProration = async () => {
    if (!selectedPlan) return
    
    setIsCalculating(true)
    setError(null)
    
    try {
      // Calculate proration preview (this would be an API call in real implementation)
      const currentPrice = currentSubscription.billing_cycle === 'annual' 
        ? currentPlan.price_annual 
        : currentPlan.price_monthly
      const newPrice = currentSubscription.billing_cycle === 'annual'
        ? selectedPlan.price_annual
        : selectedPlan.price_monthly
      
      const remainingDays = currentSubscription.days_until_period_end
      const totalDays = currentSubscription.billing_cycle === 'annual' ? 365 : 30
      
      const currentDailyRate = currentPrice / totalDays
      const newDailyRate = newPrice / totalDays
      
      const creditAmount = currentDailyRate * remainingDays
      const chargeAmount = newDailyRate * remainingDays
      const netCharge = Math.max(0, chargeAmount - creditAmount)
      
      setProrationPreview({
        credit_amount: creditAmount,
        charge_amount: chargeAmount,
        net_charge: netCharge,
        remaining_days: remainingDays
      })
    } catch (err: any) {
      setError('Failed to calculate proration')
    } finally {
      setIsCalculating(false)
    }
  }

  const handlePlanChange = async () => {
    if (!selectedPlan) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      await apiGateway.post('/enhanced-billing/subscription/change-plan/', {
        new_plan_id: selectedPlan.plan_id
      })
      onSuccess()
    } catch (err: any) {
      setError(err?.message || 'Failed to change plan')
    } finally {
      setIsLoading(false)
    }
  }

  const getPlanComparison = (plan: PlanVersion) => {
    const currentPrice = currentSubscription.billing_cycle === 'annual' 
      ? currentPlan.price_annual 
      : currentPlan.price_monthly
    const newPrice = currentSubscription.billing_cycle === 'annual'
      ? plan.price_annual
      : plan.price_monthly
    
    const isUpgrade = newPrice > currentPrice
    const isDowngrade = newPrice < currentPrice
    
    return { isUpgrade, isDowngrade, currentPrice, newPrice }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-och-dark border border-och-steel/20 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-och-steel/20">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white">Change Subscription Plan</h2>
              <p className="text-och-steel text-sm mt-1">
                Select a new plan and preview the proration charges
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

          {/* Current Plan */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3">Current Plan</h3>
            <Card className="p-4 border-och-mint/30 bg-och-mint/5">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white">{currentPlan.name}</h4>
                  <p className="text-sm text-och-steel">
                    {formatFromKES(
                      currentSubscription.billing_cycle === 'annual' 
                        ? currentPlan.price_annual 
                        : currentPlan.price_monthly, 
                      selectedCountry
                    )}
                    /{currentSubscription.billing_cycle === 'annual' ? 'year' : 'month'}
                  </p>
                </div>
                <Badge variant="mint">Current</Badge>
              </div>
            </Card>
          </div>

          {/* Available Plans */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3">Available Plans</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {eligiblePlans.map(plan => {
                const { isUpgrade, isDowngrade, newPrice } = getPlanComparison(plan)
                const isSelected = selectedPlan?.id === plan.id
                
                return (
                  <Card
                    key={plan.id}
                    className={`p-4 cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-och-mint bg-och-mint/10' 
                        : 'border-och-steel/20 hover:border-och-steel/40'
                    }`}
                    onClick={() => setSelectedPlan(plan)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-semibold text-white">{plan.name}</h4>
                        <p className="text-sm text-och-steel">
                          {formatFromKES(newPrice, selectedCountry)}
                          /{currentSubscription.billing_cycle === 'annual' ? 'year' : 'month'}
                        </p>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        {isUpgrade && <Badge variant="mint">Upgrade</Badge>}
                        {isDowngrade && <Badge variant="steel">Downgrade</Badge>}
                        {isSelected && <Badge variant="gold">Selected</Badge>}
                      </div>
                    </div>

                    {/* Feature Highlights */}
                    <div className="space-y-1">
                      {plan.feature_flags.mentorship && (
                        <p className="text-xs text-och-steel">
                          • {plan.mentorship_credits} mentorship credits/month
                        </p>
                      )}
                      {plan.feature_flags.ai_coach && (
                        <p className="text-xs text-och-steel">• AI Coach access</p>
                      )}
                      {plan.feature_flags.talentscope && (
                        <p className="text-xs text-och-steel">• TalentScope analytics</p>
                      )}
                      {plan.feature_flags.marketplace && (
                        <p className="text-xs text-och-steel">• Employer contact</p>
                      )}
                    </div>
                  </Card>
                )
              })}
            </div>
          </div>

          {/* Proration Preview */}
          {selectedPlan && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Proration Calculation
              </h3>
              
              {isCalculating ? (
                <Card className="p-4">
                  <div className="flex items-center gap-2 text-och-steel">
                    <div className="w-4 h-4 border-2 border-och-mint border-t-transparent rounded-full animate-spin" />
                    <p className="text-sm">Calculating proration...</p>
                  </div>
                </Card>
              ) : prorationPreview && (
                <Card className="p-4 bg-och-steel/5">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-och-steel">Remaining days in current period:</span>
                      <span className="text-white font-medium">{prorationPreview.remaining_days} days</span>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-och-steel">Credit for unused {currentPlan.name}:</span>
                      <span className="text-green-400 font-medium">
                        -{formatFromKES(prorationPreview.credit_amount, selectedCountry)}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-och-steel">Charge for {selectedPlan.name} (prorated):</span>
                      <span className="text-white font-medium">
                        +{formatFromKES(prorationPreview.charge_amount, selectedCountry)}
                      </span>
                    </div>
                    
                    <div className="border-t border-och-steel/20 pt-3">
                      <div className="flex items-center justify-between">
                        <span className="text-white font-semibold">Net charge today:</span>
                        <span className="text-och-mint font-bold text-lg">
                          {prorationPreview.net_charge === 0 
                            ? 'No charge' 
                            : formatFromKES(prorationPreview.net_charge, selectedCountry)
                          }
                        </span>
                      </div>
                    </div>
                    
                    <div className="bg-och-steel/10 p-3 rounded text-xs text-och-steel">
                      <p>
                        Your next billing date remains {new Date(currentSubscription.current_period_end).toLocaleDateString()}.
                        Future billing will be at the new plan rate.
                      </p>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* Downgrade Warning */}
          {selectedPlan && getPlanComparison(selectedPlan).isDowngrade && (
            <Card className="p-4 bg-yellow-500/10 border-yellow-500/30">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5" />
                <div className="text-sm">
                  <p className="text-yellow-400 font-medium mb-1">Downgrade Notice</p>
                  <p className="text-och-steel">
                    Downgrades take effect at the end of your current billing period. 
                    You'll continue to have access to your current plan features until then.
                    No refund will be provided for the downgrade.
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
              onClick={handlePlanChange}
              disabled={!selectedPlan || isLoading || isCalculating}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <ArrowRight className="w-4 h-4" />
                  {selectedPlan && getPlanComparison(selectedPlan).isUpgrade ? 'Upgrade Plan' : 'Change Plan'}
                </div>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}