'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { calculateAnnualPriceFromKES, formatFromKES } from '@/lib/currency'
import { useAuth } from '@/hooks/useAuth'

interface SubscriptionPlan {
  id: string
  name: string
  tier: 'free' | 'starter' | 'premium'
  stream?: string
  billing_interval?: 'none' | 'monthly' | 'annual'
  sort_order?: number
  is_listed?: boolean
  price_monthly: number | null
  price_annual?: number | null
  ai_coach_daily_limit: number | null
  portfolio_item_limit: number | null
  missions_access_type: 'none' | 'ai_only' | 'full'
  mentorship_access: boolean
  talentscope_access: 'none' | 'basic' | 'preview' | 'full'
  marketplace_contact: boolean
  enhanced_access_days: number | null
  features: string[]
  catalog?: Record<string, unknown>
  created_at?: string
  updated_at?: string
}

interface TierFeature {
  feature: string
  free: string
  starterEnhanced: string
  starterNormal: string
  premium: string
}

const TIER_FEATURES: TierFeature[] = [
  {
    feature: 'Curriculum',
    free: 'Read-only access',
    starterEnhanced: 'Full curriculum visibility',
    starterNormal: 'Limited curriculum visibility',
    premium: 'Full curriculum access'
  },
  {
    feature: 'AI Coach',
    free: 'Limited use (1 prompt per day)',
    starterEnhanced: 'Full AI features unlocked',
    starterNormal: 'Limited AI features',
    premium: 'Full AI and Lab integrations'
  },
  {
    feature: 'Community',
    free: 'Limited access',
    starterEnhanced: 'Full community access',
    starterNormal: 'Limited community access',
    premium: 'Full community access'
  },
  {
    feature: 'Missions',
    free: 'No access',
    starterEnhanced: 'Full mission catalog (AI-only missions)',
    starterNormal: 'Limited missions',
    premium: 'Full missions (including Capstones)'
  },
  {
    feature: 'Portfolio',
    free: 'No access',
    starterEnhanced: 'Unlimited portfolio capacity',
    starterNormal: 'Limited portfolio capacity (5 items)',
    premium: 'Unlimited portfolio'
  },
  {
    feature: 'TalentScope',
    free: 'No access',
    starterEnhanced: 'Preview mode',
    starterNormal: 'Basic TalentScope',
    premium: 'Full analytics (readiness, CV scoring, Mentor Influence Index, Career Readiness Report)'
  },
  {
    feature: 'Mentorship',
    free: 'No access',
    starterEnhanced: 'Access prevented',
    starterNormal: 'Access prevented',
    premium: 'Full mentorship (group sessions, recordings, mission reviews, pass/fail grades)'
  },
  {
    feature: 'Talent Discovery',
    free: 'No access',
    starterEnhanced: 'Access prevented',
    starterNormal: 'No employer contact',
    premium: 'Full visibility and employer contact enabled'
  }
]

export default function PlansManagementClient() {
  const { user } = useAuth()
  const [plans, setPlans] = useState<SubscriptionPlan[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [editingPlan, setEditingPlan] = useState<SubscriptionPlan | null>(null)
  const [viewingPlan, setViewingPlan] = useState<SubscriptionPlan | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [activeView, setActiveView] = useState<'overview' | 'manage'>('overview')
  const [selectedCountry, setSelectedCountry] = useState<string>('KE') // Default to Kenya
  const [subscriptionStats, setSubscriptionStats] = useState<{
    total: number
    active: number
    byTier: Record<string, number>
  } | null>(null)

  useEffect(() => {
    loadPlans()
    loadSubscriptionStats()
    // Get user's country if available, default to Kenya
    if (user?.country) {
      setSelectedCountry(user.country.toUpperCase())
    }
  }, [user])

  const loadSubscriptionStats = async () => {
    try {
      const response = await apiGateway.get<any>('/admin/subscriptions/')
      const subscriptions: any[] = Array.isArray(response) ? response : (response?.results || [])
      
      const byTier: Record<string, number> = {}
      subscriptions.forEach((sub: any) => {
        const tier = sub.plan?.tier || sub.tier || 'unknown'
        byTier[tier] = (byTier[tier] || 0) + 1
      })
      
      setSubscriptionStats({
        total: subscriptions.length,
        active: subscriptions.filter((s: any) => s.status === 'active').length,
        byTier,
      })
    } catch (error) {
      console.error('Failed to load subscription stats:', error)
      setSubscriptionStats(null)
    }
  }

  const loadPlans = async () => {
    try {
      setIsLoading(true)

      const response = await apiGateway.get<any>('/admin/plans/')
      console.log('📡 Plans API Response:', response)
      
      // Handle paginated response
      let plansData: SubscriptionPlan[] = []
      if (response?.results && Array.isArray(response.results)) {
        plansData = response.results
      } else if (Array.isArray(response)) {
        plansData = response
      } else if (response?.data && Array.isArray(response.data)) {
        plansData = response.data
      }
      
      console.log('✅ Loaded plans:', plansData.length)
      setPlans(plansData)
    } catch (error: any) {
      console.error('❌ Failed to load plans:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to load plans'
      alert(`Error loading plans: ${errorMessage}`)
      setPlans([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async (planData: Partial<SubscriptionPlan>) => {
    try {
      if (editingPlan?.id) {
        await apiGateway.put(`/admin/plans/${editingPlan.id}/`, planData)
      } else {
        await apiGateway.post('/admin/plans/', planData)
      }
      await loadPlans()
      await loadSubscriptionStats()
      setIsModalOpen(false)
      setEditingPlan(null)
      alert('Plan saved successfully!')
    } catch (error: any) {
      console.error('Failed to save plan:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to save plan'
      alert(`Error: ${errorMessage}`)
    }
  }

  const handleDelete = async (planId: string) => {
    if (!confirm('Are you sure you want to delete this plan? This action cannot be undone.')) {
      return
    }
    try {
      await apiGateway.delete(`/admin/plans/${planId}/`)
      await loadPlans()
      await loadSubscriptionStats()
      alert('Plan deleted successfully!')
    } catch (error: any) {
      console.error('Failed to delete plan:', error)
      const data = error?.response?.data
      const errorMessage =
        (typeof data?.error === 'string' ? data.error : null) ||
        data?.detail ||
        error?.message ||
        'Failed to delete plan'
      alert(`Error: ${errorMessage}`)
    }
  }

  // Dynamic tier config based on loaded plans
  const getTierConfig = (tier: string) => {
    const plan = plans.find(p => p.tier === tier)
    if (!plan) return { label: tier, color: 'steel' as const, bgColor: 'bg-och-steel/10' }
    
    const price = plan.price_monthly ? formatFromKES(plan.price_monthly, selectedCountry) : 'Free'
    return {
      label: `${plan.name} (${price}/month)`,
      color: tier === 'free' ? 'steel' as const : tier === 'starter' ? 'defender' as const : 'mint' as const,
      bgColor: tier === 'free' ? 'bg-och-steel/10' : tier === 'starter' ? 'bg-och-defender/10' : 'bg-och-mint/10'
    }
  }

  // Get paid plans (non-free) for pricing display
  const paidPlans = plans.filter(p => p.price_monthly && p.price_monthly > 0)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-och-mint mx-auto mb-4"></div>
          <p className="text-och-steel">Loading subscription plans...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2 text-och-gold">Subscription Plans Management</h1>
          <p className="text-och-steel max-w-3xl">
            Stream A (student): Free, Pro Monthly, Pro Annual, and Premium SKUs. USD list prices and feature matrix live in
            each plan&apos;s <strong className="text-white">catalog</strong> JSON; KES amounts in{' '}
            <strong className="text-white">price_monthly</strong> / <strong className="text-white">price_annual</strong>{' '}
            drive checkout. Global grace periods, academic discount %, and renewal timing are in{' '}
            <code className="text-och-mint">PaymentSettings.student_subscription_policy</code> (seeded by migration).
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={activeView === 'overview' ? 'defender' : 'outline'}
            onClick={() => setActiveView('overview')}
          >
            Overview
          </Button>
          <Button
            variant={activeView === 'manage' ? 'defender' : 'outline'}
            onClick={() => setActiveView('manage')}
          >
            Manage Plans
          </Button>
        </div>
      </div>

      {activeView === 'overview' && (
        <div className="space-y-6">
          {/* Header Section with Stats */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Subscription Statistics */}
            <Card className="lg:col-span-2">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-white mb-4">Subscription Overview</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-och-midnight/50 p-4 rounded-lg border border-och-steel/20">
                    <div className="text-sm text-och-steel mb-1">Total Plans</div>
                    <div className="text-2xl font-bold text-white">{plans.length}</div>
                  </div>
                  <div className="bg-och-midnight/50 p-4 rounded-lg border border-och-steel/20">
                    <div className="text-sm text-och-steel mb-1">Total Subscriptions</div>
                    <div className="text-2xl font-bold text-och-mint">
                      {subscriptionStats?.total || '-'}
                    </div>
                  </div>
                  <div className="bg-och-midnight/50 p-4 rounded-lg border border-och-steel/20">
                    <div className="text-sm text-och-steel mb-1">Active Subscriptions</div>
                    <div className="text-2xl font-bold text-och-defender">
                      {subscriptionStats?.active || '-'}
                    </div>
                  </div>
                  <div className="bg-och-midnight/50 p-4 rounded-lg border border-och-steel/20">
                    <div className="text-sm text-och-steel mb-1">Paid Plans</div>
                    <div className="text-2xl font-bold text-och-gold">
                      {paidPlans.length}
                    </div>
                  </div>
                </div>
                
                {/* Tier Distribution */}
                {subscriptionStats && Object.keys(subscriptionStats.byTier).length > 0 && (
                  <div className="mt-6 pt-6 border-t border-och-steel/20">
                    <h3 className="text-lg font-semibold text-white mb-3">Subscriptions by Tier</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {Object.entries(subscriptionStats.byTier).map(([tier, count]) => (
                        <div key={tier} className="bg-och-midnight/30 p-3 rounded border border-och-steel/10">
                          <div className="text-xs text-och-steel mb-1 capitalize">{tier}</div>
                          <div className="text-xl font-bold text-white">{count}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* Currency Selector */}
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Display Settings</h3>
                <label className="block text-sm font-medium text-white mb-2">Currency</label>
                <select
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                  className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
                >
                  <option value="KE">Kenya (KES)</option>
                  <option value="US">United States (USD)</option>
                  <option value="BW">Botswana (BWP)</option>
                  <option value="ZA">South Africa (ZAR)</option>
                  <option value="NG">Nigeria (NGN)</option>
                  <option value="GH">Ghana (GHS)</option>
                  <option value="TZ">Tanzania (TZS)</option>
                  <option value="UG">Uganda (UGX)</option>
                  <option value="ET">Ethiopia (ETB)</option>
                  <option value="RW">Rwanda (RWF)</option>
                </select>
                <p className="text-xs text-och-steel mt-3">
                  Prices are stored in Kenyan Shillings (KSh) and converted for display when you choose another country.
                  Free tier: 14-day trial. Starter: monthly subscription. Premium: annual subscription.
                </p>
              </div>
            </Card>
          </div>

          {/* Subscription Pricing Overview */}
          <Card>
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold text-white mb-2">Subscription Plans & Pricing</h2>
                  <p className="text-och-steel text-sm">
                    Free: 14-day trial. Starter: Monthly billing in KSh. Premium: Annual billing in KSh (can still show equivalent monthly for information).
                  </p>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {plans.map((plan) => {
                  const subscriptionCount = subscriptionStats?.byTier[plan.tier] || 0
                  
                  if (!plan.price_monthly || plan.price_monthly === 0) {
                    // Free tier - 14-day trial
                    return (
                      <div key={plan.id} className="relative p-6 bg-gradient-to-br from-och-steel/20 to-och-steel/5 rounded-lg border-2 border-och-steel/30 hover:border-och-steel/50 transition-all">
                        <div className="absolute top-4 right-4">
                          <Badge variant="steel">{plan.name}</Badge>
                        </div>
                        <div className="mt-8">
                          <h3 className="text-2xl font-bold text-white mb-3">{plan.name}</h3>
                          <div className="mb-4">
                            <p className="text-4xl font-bold text-white mb-1">Free</p>
                            <p className="text-sm text-och-steel">14-day free trial</p>
                            <p className="text-xs text-och-steel mt-1">No charges during trial period</p>
                          </div>
                          {subscriptionCount > 0 && (
                            <div className="mt-4 pt-4 border-t border-och-steel/20">
                              <p className="text-xs text-och-steel">Active Subscriptions</p>
                              <p className="text-lg font-semibold text-white">{subscriptionCount}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  }

                  const isStarter = plan.tier === 'starter'
                  const isPremium = plan.tier === 'premium'
                  
                  // Subscription prices in KES. Starter: monthly; Premium: annual.
                  let monthlyKes = plan.price_monthly ?? 0
                  let annualKes: number | null = null
                  let billingType = ''
                  
                  if (isStarter) {
                    monthlyKes = plan.price_monthly || 650
                    annualKes = monthlyKes * 12
                    billingType = 'Monthly'
                  } else if (isPremium) {
                    annualKes = 7020
                    monthlyKes = annualKes / 12
                    billingType = 'Annual'
                  }
                  
                  return (
                    <div 
                      key={plan.id} 
                      className={`relative p-6 rounded-lg border-2 transition-all ${
                        isPremium 
                          ? 'bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40 hover:border-och-mint/60' 
                          : isStarter
                          ? 'bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/40 hover:border-och-defender/60'
                          : 'bg-gradient-to-br from-och-midnight/50 to-och-midnight/30 border-och-steel/30 hover:border-och-steel/50'
                      }`}
                    >
                      {isPremium && (
                        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                          <Badge variant="gold" className="text-xs font-bold px-3 py-1">BEST VALUE</Badge>
                        </div>
                      )}
                      
                      <div className="absolute top-4 right-4">
                        <Badge variant={isStarter ? 'defender' : 'mint'}>{plan.name}</Badge>
                      </div>
                      
                      <div className="mt-8">
                        <h3 className="text-2xl font-bold text-white mb-4">{plan.name}</h3>
                        
                        {isStarter ? (
                          // Starter: Monthly billing
                          <>
                            <div className="mb-4 pb-4 border-b border-och-steel/20">
                              <p className="text-sm text-och-steel mb-1">Monthly Subscription</p>
                              <div className="flex items-baseline gap-2">
                                <p className="text-3xl font-bold text-white">
                                  {formatFromKES(monthlyKes, selectedCountry)}
                                </p>
                                <span className="text-sm text-och-steel">/month</span>
                              </div>
                              <p className="text-xs text-och-steel mt-1">
                                KSh {monthlyKes.toLocaleString()} per month
                              </p>
                            </div>
                            <div className="mb-4">
                              <p className="text-xs text-och-steel">
                                Billed monthly. Cancel anytime.
                              </p>
                            </div>
                          </>
                        ) : isPremium ? (
                          // Premium: Annual billing
                          <>
                            <div className="mb-4 pb-4 border-b border-och-steel/20">
                              <p className="text-sm text-och-steel mb-1">Annual Subscription</p>
                              <div className="flex items-baseline gap-2 mb-1">
                                <p className="text-3xl font-bold text-och-mint">
                                  {formatFromKES(annualKes!, selectedCountry)}
                                </p>
                                <span className="text-sm text-och-steel">/year</span>
                              </div>
                              <div className="flex items-center gap-2 mb-2">
                                <p className="text-xs text-och-steel line-through">
                                  {formatFromKES(7800, selectedCountry)}
                                </p>
                                <Badge variant="mint" className="text-xs font-bold">10% OFF</Badge>
                              </div>
                              <p className="text-xs text-och-steel">
                                KSh {annualKes?.toLocaleString()} per year
                              </p>
                            </div>
                            <div className="mb-4">
                              <p className="text-xs text-och-mint font-medium">
                                💰 Equivalent to {formatFromKES(monthlyKes, selectedCountry)}/month
                              </p>
                              <p className="text-xs text-och-steel mt-1">
                                Billed annually. Save 10% vs monthly.
                              </p>
                            </div>
                          </>
                        ) : null}

                        {/* Subscription Count */}
                        {subscriptionCount > 0 && (
                          <div className="mt-4 pt-4 border-t border-och-steel/20">
                            <p className="text-xs text-och-steel mb-1">Active Subscriptions</p>
                            <p className="text-lg font-semibold text-white">{subscriptionCount}</p>
                          </div>
                        )}

                        {/* Key Features Preview */}
                        <div className="mt-4 pt-4 border-t border-och-steel/20">
                          <p className="text-xs text-och-steel mb-2">Key Features:</p>
                          <div className="space-y-1">
                            {plan.mentorship_access && (
                              <p className="text-xs text-white">✓ Human Mentorship</p>
                            )}
                            {plan.missions_access_type === 'full' && (
                              <p className="text-xs text-white">✓ Full Mission Access</p>
                            )}
                            {plan.talentscope_access === 'full' && (
                              <p className="text-xs text-white">✓ Full TalentScope Analytics</p>
                            )}
                            {plan.marketplace_contact && (
                              <p className="text-xs text-white">✓ Employer Contact Enabled</p>
                            )}
                            {plan.ai_coach_daily_limit === null && (
                              <p className="text-xs text-white">✓ Unlimited AI Coach</p>
                            )}
                            {plan.portfolio_item_limit === null && (
                              <p className="text-xs text-white">✓ Unlimited Portfolio</p>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </Card>

          {/* System Overview */}
          <Card>
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-white mb-2">Feature Comparison Matrix</h2>
                <p className="text-och-steel text-sm">
                  Compare features and access levels across all subscription tiers. Access rights are defined by entitlements 
                  which are activated instantly upon successful payment. Upgrades take effect immediately, while downgrades 
                  apply at the end of the current billing cycle.
                </p>
              </div>

              {/* Dynamic Feature Comparison Table */}
              {plans.length > 0 && (
                <div className="overflow-x-auto rounded-lg border border-och-steel/20">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-och-midnight/50 border-b border-och-steel/20">
                        <th className="text-left p-4 text-white font-semibold">Feature</th>
                        {plans.map((plan) => (
                          <th key={plan.id} className="text-left p-4 text-white font-semibold">
                            <div className="flex flex-col">
                              <span>{plan.name}</span>
                              {plan.price_monthly ? (
                                <span className="text-xs text-och-steel mt-1 font-normal">
                                  {formatFromKES(plan.price_monthly!, selectedCountry)}/mo
                                </span>
                              ) : (
                                <span className="text-xs text-och-steel mt-1 font-normal">Free</span>
                              )}
                            </div>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                        <td className="p-4 text-white font-medium">Missions Access</td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="p-4">
                            <Badge 
                              variant={plan.missions_access_type === 'full' ? 'mint' : plan.missions_access_type === 'ai_only' ? 'defender' : 'steel'}
                              className="capitalize"
                            >
                              {plan.missions_access_type.replace('_', ' ')}
                            </Badge>
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                        <td className="p-4 text-white font-medium">Human Mentorship</td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="p-4">
                            {plan.mentorship_access ? (
                              <Badge variant="mint">Full Access</Badge>
                            ) : (
                              <Badge variant="steel">No Access</Badge>
                            )}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                        <td className="p-4 text-white font-medium">TalentScope Analytics</td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="p-4">
                            <Badge 
                              variant={plan.talentscope_access === 'full' ? 'mint' : plan.talentscope_access === 'preview' ? 'defender' : plan.talentscope_access === 'basic' ? 'steel' : 'steel'}
                              className="capitalize"
                            >
                              {plan.talentscope_access === 'none' ? 'No Access' : plan.talentscope_access}
                            </Badge>
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                        <td className="p-4 text-white font-medium">Employer Contact</td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="p-4">
                            {plan.marketplace_contact ? (
                              <Badge variant="mint">Enabled</Badge>
                            ) : (
                              <Badge variant="steel">Disabled</Badge>
                            )}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                        <td className="p-4 text-white font-medium">AI Coach Daily Limit</td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="p-4 text-och-steel">
                            {plan.ai_coach_daily_limit !== null 
                              ? `${plan.ai_coach_daily_limit} interactions/day`
                              : <Badge variant="mint">Unlimited</Badge>}
                          </td>
                        ))}
                      </tr>
                      <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                        <td className="p-4 text-white font-medium">Portfolio Item Limit</td>
                        {plans.map((plan) => (
                          <td key={plan.id} className="p-4 text-och-steel">
                            {plan.portfolio_item_limit !== null 
                              ? `${plan.portfolio_item_limit} items`
                              : <Badge variant="mint">Unlimited</Badge>}
                          </td>
                        ))}
                      </tr>
                      {plans.some(p => p.enhanced_access_days) && (
                        <tr className="border-b border-och-steel/10 hover:bg-och-midnight/30 transition-colors">
                          <td className="p-4 text-white font-medium">Enhanced Access Period</td>
                          {plans.map((plan) => (
                            <td key={plan.id} className="p-4 text-och-steel">
                              {plan.enhanced_access_days 
                                ? (
                                  <div>
                                    <Badge variant="defender">{plan.enhanced_access_days} days</Badge>
                                    <span className="text-xs text-och-steel ml-2">
                                      ({Math.round(plan.enhanced_access_days / 30)} months)
                                    </span>
                                  </div>
                                )
                                : <span className="text-och-steel">N/A</span>}
                            </td>
                          ))}
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Additional Information */}
              <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-och-midnight/30 rounded-lg border border-och-steel/20">
                  <h4 className="text-white font-semibold mb-2">💳 Payment & Billing</h4>
                  <ul className="text-sm text-och-steel space-y-1">
                    <li>• Instant activation upon successful payment</li>
                    <li>• Upgrades take effect immediately</li>
                    <li>• Downgrades apply at end of billing cycle</li>
                    <li>• 5-day grace period for payment failures</li>
                  </ul>
                </div>
                <div className="p-4 bg-och-midnight/30 rounded-lg border border-och-steel/20">
                  <h4 className="text-white font-semibold mb-2">🔄 Subscription Management</h4>
                  <ul className="text-sm text-och-steel space-y-1">
                    <li>• Annual subscriptions save 10% vs monthly</li>
                    <li>• Auto-downgrade to Free tier after grace period</li>
                    <li>• Enhanced access periods for new subscribers</li>
                    <li>• Feature access gated by entitlement status</li>
                  </ul>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {activeView === 'manage' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white">Manage Subscription Plans</h2>
            <Button
              variant="defender"
              onClick={() => {
                setEditingPlan(null)
                setIsModalOpen(true)
              }}
            >
              + Create Plan
            </Button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {plans.map((plan) => {
              const config = getTierConfig(plan.tier)
              return (
                <Card key={plan.id} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <Badge variant={config.color}>{plan.name}</Badge>
                      <h3 className="text-xl font-bold text-white mt-2">{plan.name}</h3>
                      {plan.price_monthly && (
                        <p className="text-och-defender text-lg font-semibold mt-1">
                          {formatFromKES(plan.price_monthly, selectedCountry)}
                          <span className="text-sm text-och-steel"> /month</span>
                        </p>
                      )}
                      {!plan.price_monthly && (
                        <p className="text-och-steel text-lg font-semibold mt-1">Free</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setViewingPlan(plan)
                          setIsDetailModalOpen(true)
                        }}
                      >
                        View
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setEditingPlan(plan)
                          setIsModalOpen(true)
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(plan.id)}
                        className="text-och-orange hover:text-och-orange hover:border-och-orange"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-3 text-sm">
                    <div>
                      <span className="text-och-steel">Missions:</span>
                      <span className="text-white ml-2 capitalize">{plan.missions_access_type.replace('_', ' ')}</span>
                    </div>
                    <div>
                      <span className="text-och-steel">Mentorship:</span>
                      <span className="text-white ml-2">{plan.mentorship_access ? 'Full Access' : 'No Access'}</span>
                    </div>
                    <div>
                      <span className="text-och-steel">TalentScope:</span>
                      <span className="text-white ml-2 capitalize">{plan.talentscope_access}</span>
                    </div>
                    <div>
                      <span className="text-och-steel">Talent Search:</span>
                      <span className="text-white ml-2">{plan.marketplace_contact ? 'Enabled' : 'Disabled'}</span>
                    </div>
                    {plan.ai_coach_daily_limit !== null && (
                      <div>
                        <span className="text-och-steel">AI Coach:</span>
                        <span className="text-white ml-2">{plan.ai_coach_daily_limit} interactions/day</span>
                      </div>
                    )}
                    {plan.portfolio_item_limit !== null && (
                      <div>
                        <span className="text-och-steel">Portfolio:</span>
                        <span className="text-white ml-2">{plan.portfolio_item_limit} items</span>
                      </div>
                    )}
                    {plan.enhanced_access_days && (
                      <div>
                        <span className="text-och-steel">Enhanced Access:</span>
                        <span className="text-white ml-2">{plan.enhanced_access_days} days</span>
                      </div>
                    )}
                  </div>
                </Card>
              )
            })}
          </div>

          {plans.length === 0 && (
            <Card>
              <div className="p-6 text-center">
                <p className="text-och-steel mb-4">No subscription plans found.</p>
                <Button
                  variant="defender"
                  onClick={() => {
                    setEditingPlan(null)
                    setIsModalOpen(true)
                  }}
                >
                  Create First Plan
                </Button>
              </div>
            </Card>
          )}
        </div>
      )}

      {isModalOpen && (
        <PlanEditModal
          plan={editingPlan}
          onClose={() => {
            setIsModalOpen(false)
            setEditingPlan(null)
          }}
          onSave={handleSave}
        />
      )}

      {isDetailModalOpen && viewingPlan && (
        <PlanDetailModal
          plan={viewingPlan}
          onClose={() => {
            setIsDetailModalOpen(false)
            setViewingPlan(null)
          }}
          onEdit={() => {
            setIsDetailModalOpen(false)
            setEditingPlan(viewingPlan)
            setIsModalOpen(true)
          }}
        />
      )}
    </div>
  )
}

function PlanDetailModal({
  plan,
  onClose,
  onEdit,
}: {
  plan: SubscriptionPlan
  onClose: () => void
  onEdit: () => void
}) {
  const { user } = useAuth()
  const [selectedCountry, setSelectedCountry] = useState<string>(user?.country?.toUpperCase() || 'KE')
  
  const tierConfig = {
    free: { label: 'Free Tier', color: 'steel' as const },
    starter: { label: 'Starter Tier', color: 'defender' as const },
    premium: { label: 'Premium Tier', color: 'mint' as const },
  }

  const config = tierConfig[plan.tier] || { label: plan.name, color: 'steel' as const }
  
  // Calculate pricing based on tier type
  const isStarter = plan.tier === 'starter'
  const isPremium = plan.tier === 'premium'
  
  let monthlyKes = plan.price_monthly || 0
  let annualKes: number | null = null
  
  if (isStarter) {
    monthlyKes = plan.price_monthly || 650
    annualKes = monthlyKes * 12
  } else if (isPremium) {
    annualKes = 7020
    monthlyKes = annualKes / 12
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <Badge variant={config.color}>{plan.name}</Badge>
              <h2 className="text-2xl font-bold text-white mt-2">{plan.name}</h2>
              {plan.tier === 'free' ? (
                <div className="mt-2">
                  <p className="text-och-steel text-xl font-semibold">Free</p>
                  <p className="text-xs text-och-steel mt-1">14-day free trial</p>
                </div>
              ) : isStarter ? (
                <div className="mt-2">
                  <p className="text-och-defender text-xl font-semibold">
                    {formatFromKES(monthlyKes, selectedCountry)} per month
                  </p>
                  <p className="text-xs text-och-steel mt-1">
                    KSh {monthlyKes.toLocaleString()}/month • Monthly billing
                  </p>
                </div>
              ) : isPremium ? (
                <div className="mt-2">
                  <p className="text-och-mint text-xl font-semibold">
                    {formatFromKES(annualKes!, selectedCountry)} per year
                  </p>
                  <p className="text-xs text-och-steel mt-1">
                    KSh {annualKes?.toLocaleString()}/year • Equivalent to {formatFromKES(monthlyKes, selectedCountry)}/month
                  </p>
                  <p className="text-xs text-och-mint mt-1">
                    Annual billing • Save 10% vs monthly
                  </p>
                </div>
              ) : null}
            </div>
            <button
              onClick={onClose}
              className="text-och-steel hover:text-white text-xl"
            >
              ✕
            </button>
          </div>
          
          {/* Currency Selector */}
          {(
            <div className="mb-6">
              <label className="block text-sm font-medium text-white mb-2">Display Currency</label>
              <select
                value={selectedCountry}
                onChange={(e) => setSelectedCountry(e.target.value)}
                className="w-full max-w-xs px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white focus:outline-none focus:border-och-defender"
              >
                <option value="KE">Kenya (KES)</option>
                <option value="US">United States (USD)</option>
                <option value="BW">Botswana (BWP)</option>
                <option value="ZA">South Africa (ZAR)</option>
                <option value="NG">Nigeria (NGN)</option>
                <option value="GH">Ghana (GHS)</option>
                <option value="TZ">Tanzania (TZS)</option>
                <option value="UG">Uganda (UGX)</option>
                <option value="ET">Ethiopia (ETB)</option>
                <option value="RW">Rwanda (RWF)</option>
              </select>
            </div>
          )}

          <div className="space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Basic Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-och-steel">Plan ID:</span>
                  <span className="text-white ml-2 font-mono text-xs">{plan.id}</span>
                </div>
                <div>
                  <span className="text-och-steel">Tier:</span>
                  <span className="text-white ml-2 capitalize">{plan.tier}</span>
                </div>
                {plan.created_at && (
                  <div>
                    <span className="text-och-steel">Created:</span>
                    <span className="text-white ml-2">
                      {new Date(plan.created_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
                {plan.updated_at && (
                  <div>
                    <span className="text-och-steel">Last Updated:</span>
                    <span className="text-white ml-2">
                      {new Date(plan.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Feature Access */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Feature Access</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                  <span className="text-och-steel">Missions Access:</span>
                  <span className="text-white capitalize">{plan.missions_access_type.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                  <span className="text-och-steel">Mentorship:</span>
                  <Badge variant={plan.mentorship_access ? 'mint' : 'steel'}>
                    {plan.mentorship_access ? 'Full Access' : 'No Access'}
                  </Badge>
                </div>
                <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                  <span className="text-och-steel">TalentScope:</span>
                  <span className="text-white capitalize">{plan.talentscope_access}</span>
                </div>
                <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                  <span className="text-och-steel">Talent Contact:</span>
                  <Badge variant={plan.marketplace_contact ? 'mint' : 'steel'}>
                    {plan.marketplace_contact ? 'Enabled' : 'Disabled'}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Limits */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Limits & Constraints</h3>
              <div className="space-y-2 text-sm">
                {plan.ai_coach_daily_limit !== null ? (
                  <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                    <span className="text-och-steel">AI Coach Daily Limit:</span>
                    <span className="text-white">{plan.ai_coach_daily_limit} interactions/day</span>
                  </div>
                ) : (
                  <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                    <span className="text-och-steel">AI Coach Daily Limit:</span>
                    <span className="text-white">Unlimited</span>
                  </div>
                )}
                {plan.portfolio_item_limit !== null ? (
                  <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                    <span className="text-och-steel">Portfolio Item Limit:</span>
                    <span className="text-white">{plan.portfolio_item_limit} items</span>
                  </div>
                ) : (
                  <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                    <span className="text-och-steel">Portfolio Item Limit:</span>
                    <span className="text-white">Unlimited</span>
                  </div>
                )}
                {plan.enhanced_access_days && (
                  <div className="flex justify-between p-2 bg-och-midnight/50 rounded">
                    <span className="text-och-steel">Enhanced Access Period:</span>
                    <span className="text-white">{plan.enhanced_access_days} days</span>
                  </div>
                )}
              </div>
            </div>

            {/* Features List */}
            {plan.features && plan.features.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Feature Flags</h3>
                <div className="flex flex-wrap gap-2">
                  {plan.features.map((feature, idx) => (
                    <Badge key={idx} variant="defender">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-4 pt-4 border-t border-och-steel/20">
              <Button
                variant="defender"
                onClick={onEdit}
                className="flex-1"
              >
                Edit Plan
              </Button>
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

function PlanEditModal({
  plan,
  onClose,
  onSave,
}: {
  plan: SubscriptionPlan | null
  onSave: (data: Partial<SubscriptionPlan>) => void
  onClose: () => void
}) {
  const [catalogJson, setCatalogJson] = useState('{}')
  const [formData, setFormData] = useState<Partial<SubscriptionPlan>>({
    name: plan?.name || '',
    tier: plan?.tier || 'free',
    stream: plan?.stream || 'student',
    billing_interval: plan?.billing_interval || 'monthly',
    sort_order: plan?.sort_order ?? 0,
    is_listed: plan?.is_listed !== false,
    price_monthly: plan?.price_monthly || null,
    price_annual: plan?.price_annual ?? null,
    ai_coach_daily_limit: plan?.ai_coach_daily_limit || null,
    portfolio_item_limit: plan?.portfolio_item_limit || null,
    missions_access_type: plan?.missions_access_type || 'none',
    mentorship_access: plan?.mentorship_access || false,
    talentscope_access: plan?.talentscope_access || 'none',
    marketplace_contact: plan?.marketplace_contact || false,
    enhanced_access_days: plan?.enhanced_access_days || null,
    features: plan?.features || [],
    catalog: plan?.catalog || {},
  })

  useEffect(() => {
    setFormData({
      name: plan?.name || '',
      tier: plan?.tier || 'free',
      stream: plan?.stream || 'student',
      billing_interval: plan?.billing_interval || 'monthly',
      sort_order: plan?.sort_order ?? 0,
      is_listed: plan?.is_listed !== false,
      price_monthly: plan?.price_monthly || null,
      price_annual: plan?.price_annual ?? null,
      ai_coach_daily_limit: plan?.ai_coach_daily_limit || null,
      portfolio_item_limit: plan?.portfolio_item_limit || null,
      missions_access_type: plan?.missions_access_type || 'none',
      mentorship_access: plan?.mentorship_access || false,
      talentscope_access: plan?.talentscope_access || 'none',
      marketplace_contact: plan?.marketplace_contact || false,
      enhanced_access_days: plan?.enhanced_access_days || null,
      features: plan?.features || [],
      catalog: plan?.catalog || {},
    })
    setCatalogJson(JSON.stringify(plan?.catalog ?? {}, null, 2))
  }, [plan])

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              {plan ? 'Edit Plan' : 'Create Plan'}
            </h2>
            <button
              onClick={onClose}
              className="text-och-steel hover:text-white text-xl"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white mb-2">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                placeholder="e.g., free, starter, premium"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Tier
                <span className="text-xs text-och-steel ml-2">(from SubscriptionPlan model)</span>
              </label>
              <select
                value={formData.tier}
                onChange={(e) => {
                  const selectedTier = e.target.value as any
                  setFormData({
                    ...formData,
                    tier: selectedTier,
                  })
                }}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
              >
                <option value="free">Free Tier (trial, KSh 0)</option>
                <option value="starter">Starter Tier (monthly plan in KSh)</option>
                <option value="premium">Premium Tier (annual plan in KSh)</option>
              </select>
              <p className="text-xs text-och-steel mt-1">
                Set the tier, then enter the actual monthly price below in Kenyan Shillings (KSh).
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Stream</label>
                <select
                  value={formData.stream || 'student'}
                  onChange={(e) => setFormData({ ...formData, stream: e.target.value })}
                  className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                >
                  <option value="student">Student (Stream A)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-2">Billing interval</label>
                <select
                  value={formData.billing_interval || 'monthly'}
                  onChange={(e) =>
                    setFormData({ ...formData, billing_interval: e.target.value as SubscriptionPlan['billing_interval'] })
                  }
                  className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                >
                  <option value="none">None (free)</option>
                  <option value="monthly">Monthly</option>
                  <option value="annual">Annual</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">Sort order</label>
                <input
                  type="number"
                  value={formData.sort_order ?? 0}
                  onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value, 10) || 0 })}
                  className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_listed !== false}
                    onChange={(e) => setFormData({ ...formData, is_listed: e.target.checked })}
                    className="w-4 h-4"
                  />
                  <span className="text-white text-sm">Listed on student pricing</span>
                </label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Monthly Price (KSh)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.price_monthly != null ? formData.price_monthly : ''}
                onChange={(e) => setFormData({ ...formData, price_monthly: e.target.value ? parseFloat(e.target.value) : null })}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                placeholder={formData.tier === 'free' ? '0.00 (Free)' : 'e.g., 650.00'}
                disabled={formData.tier === 'free'}
              />
              {formData.tier === 'free' && (
                <p className="text-xs text-och-steel mt-1">Free tier is $0 - 14-day trial period</p>
              )}
              {formData.tier === 'starter' && (
                <p className="text-xs text-och-steel mt-1">
                  Starter tier: enter the monthly subscription price in Kenyan Shillings (KSh).
                </p>
              )}
              {formData.tier === 'premium' && (
                <p className="text-xs text-och-mint mt-1">
                  Premium tier: enter the effective monthly KSh price here; billing can still be handled annually.
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Annual price (KSh)</label>
              <input
                type="number"
                step="0.01"
                value={formData.price_annual != null ? formData.price_annual : ''}
                onChange={(e) =>
                  setFormData({ ...formData, price_annual: e.target.value ? parseFloat(e.target.value) : null })
                }
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                placeholder="For annual SKUs or Premium annual option"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">
                Catalog JSON (USD list prices, tier_range, trial, features, mentorship credits)
              </label>
              <textarea
                value={catalogJson}
                onChange={(e) => setCatalogJson(e.target.value)}
                rows={12}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white font-mono text-xs"
                spellCheck={false}
              />
              <p className="text-xs text-och-steel mt-1">
                Example keys: display_name, usd_monthly, usd_annual, tier_range, mentorship_credits_per_month, trial_days,
                trial_requires_payment_method, features.tier_2_6_access, annual_savings_percent.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white mb-2">AI Coach Daily Limit</label>
                <input
                  type="number"
                  value={formData.ai_coach_daily_limit || ''}
                  onChange={(e) => setFormData({ ...formData, ai_coach_daily_limit: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                  placeholder="Leave empty for unlimited"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-white mb-2">Portfolio Item Limit</label>
                <input
                  type="number"
                  value={formData.portfolio_item_limit || ''}
                  onChange={(e) => setFormData({ ...formData, portfolio_item_limit: e.target.value ? parseInt(e.target.value) : null })}
                  className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                  placeholder="Leave empty for unlimited"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Missions Access Type</label>
              <select
                value={formData.missions_access_type}
                onChange={(e) => setFormData({ ...formData, missions_access_type: e.target.value as any })}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
              >
                <option value="none">No Missions</option>
                <option value="ai_only">AI-Only Missions</option>
                <option value="full">Full Missions (including Capstones and Labs)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">TalentScope Access</label>
              <select
                value={formData.talentscope_access}
                onChange={(e) => setFormData({ ...formData, talentscope_access: e.target.value as any })}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
              >
                <option value="none">No Access</option>
                <option value="basic">Basic TalentScope</option>
                <option value="preview">Preview Mode</option>
                <option value="full">Full Analytics</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-white mb-2">Enhanced Access Days</label>
              <input
                type="number"
                value={formData.enhanced_access_days || ''}
                onChange={(e) => setFormData({ ...formData, enhanced_access_days: e.target.value ? parseInt(e.target.value) : null })}
                className="w-full px-4 py-2 bg-och-midnight/50 border border-och-steel/20 rounded-lg text-white"
                placeholder="e.g., 180 for Starter tier"
              />
              <p className="text-xs text-och-steel mt-1">Number of days Enhanced Access is active (e.g., 180 for first 6 months)</p>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.mentorship_access}
                  onChange={(e) => setFormData({ ...formData, mentorship_access: e.target.checked })}
                  className="w-4 h-4 text-och-defender bg-och-midnight border-och-steel/30 rounded"
                />
                <span className="text-white">Mentorship Access</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.marketplace_contact}
                  onChange={(e) => setFormData({ ...formData, marketplace_contact: e.target.checked })}
                  className="w-4 h-4 text-och-defender bg-och-midnight border-och-steel/30 rounded"
                />
                <span className="text-white">Talent Contact</span>
              </label>
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                variant="defender"
                onClick={() => {
                  try {
                    const catalog = catalogJson.trim() ? JSON.parse(catalogJson) : {}
                    onSave({ ...formData, catalog })
                  } catch {
                    alert('Invalid JSON in catalog field')
                  }
                }}
                className="flex-1"
              >
                Save
              </Button>
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
