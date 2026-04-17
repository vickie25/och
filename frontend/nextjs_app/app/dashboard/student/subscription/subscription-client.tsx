'use client'

import { useState, useEffect, useMemo } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useAuth } from '@/hooks/useAuth'
import { apiGateway } from '@/services/apiGateway'
import { financeService, type FinancialDashboard } from '@/services/financeService'
import { CheckCircle2, CreditCard, AlertCircle, Info } from 'lucide-react'
import {
  formatFromKES,
  formatUsd,
  formatUsdApproxLocal,
  getCountryDisplayName,
  getCurrencyCode,
} from '@/lib/currency'

type StreamPolicy = {
  grace_period_days_monthly?: number
  grace_period_days_annual?: number
  renewal_attempt_days_before?: number
  academic_discount_percent?: number
  promo_single_code_per_checkout?: boolean
  auto_renewal_default?: boolean
  downgrade_effective?: string
  upgrade_effective?: string
  usd_to_kes_rate?: number
}

type PlanFeatures = {
  tier_2_6_access?: boolean
  tier_7_9_access?: boolean
  priority_support?: boolean
  certification_prep?: boolean
  enterprise_dashboard_trial?: boolean
}

type PlanCatalog = {
  display_name?: string
  tier_rank?: number
  usd_monthly?: number | null
  usd_annual?: number | null
  tier_range?: { min?: number; max?: number }
  mentorship_credits_per_month?: number | null
  trial_days?: number
  trial_requires_payment_method?: boolean
  features?: PlanFeatures
  annual_savings_percent?: number | null
}

interface SubscriptionStatus {
  tier: string
  plan_tier?: string
  plan_name?: string
  plan_catalog?: PlanCatalog
  status: string
  days_enhanced_left: number | null
  next_payment: string | null
  current_period_end: string | null
  billing_interval?: string
  trial_end?: string | null
  cancel_at_period_end?: boolean
  grace_period_end?: string | null
  pending_downgrade_plan?: string | null
  pending_downgrade_effective_at?: string | null
  policy?: StreamPolicy
}

interface Plan {
  id: string
  name: string
  tier: string
  stream?: string
  billing_interval?: string
  sort_order?: number
  is_listed?: boolean
  price_monthly: number | null
  price_annual?: number | null
  catalog?: PlanCatalog
  mentorship_access: boolean
  missions_access_type: string
  talentscope_access: string
  marketplace_contact: boolean
  ai_coach_daily_limit: number | null
  portfolio_item_limit: number | null
  enhanced_access_days: number | null
}

function normalizePlansResponse(res: unknown): { plans: Plan[]; policy: StreamPolicy } {
  if (Array.isArray(res)) {
    return { plans: res as Plan[], policy: {} }
  }
  const o = res as { plans?: Plan[]; policy?: StreamPolicy }
  return {
    plans: Array.isArray(o.plans) ? o.plans : [],
    policy: o.policy || {},
  }
}

export default function SubscriptionClient() {
  const { user } = useAuth()
  const [subStatus, setSubStatus] = useState<SubscriptionStatus | null>(null)
  const [plans, setPlans] = useState<Plan[]>([])
  const [policy, setPolicy] = useState<StreamPolicy>({})
  const [billing, setBilling] = useState<any[]>([])
  const [financeDash, setFinanceDash] = useState<FinancialDashboard | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const selectedCountry = user?.country?.toUpperCase() || 'KE'
  const kesRate =
    policy.usd_to_kes_rate ?? subStatus?.policy?.usd_to_kes_rate ?? 130
  const countryLabel = getCountryDisplayName(selectedCountry)
  const currencyCode = getCurrencyCode(selectedCountry)

  const paystackPublicKey = typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY || '') : ''

  useEffect(() => {
    if (user?.id) loadAll()
  }, [user?.id])

  const loadAll = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const [statusRes, plansRes, billingRes, financeRes] = await Promise.all([
        apiGateway.get('/subscription/status') as Promise<SubscriptionStatus>,
        apiGateway.get('/subscription/plans'),
        apiGateway.get('/subscription/billing-history').catch(() => ({ billing_history: [] })),
        financeService.getFinancialDashboard().catch(() => null),
      ])
      setSubStatus(statusRes)
      const { plans: p, policy: pol } = normalizePlansResponse(plansRes)
      setPlans(p)
      setPolicy(pol || (statusRes as SubscriptionStatus).policy || {})
      const billingList = Array.isArray(billingRes) ? billingRes : (billingRes as { billing_history?: unknown[] })?.billing_history ?? []
      setBilling(billingList)
      setFinanceDash(financeRes)
    } catch (err: any) {
      setError(err?.message || 'Failed to load subscription data')
    } finally {
      setIsLoading(false)
    }
  }

  const sortedPlans = useMemo(
    () => [...plans].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0)),
    [plans]
  )

  const currentRank = (): number => {
    const cat = subStatus?.plan_catalog
    if (cat?.tier_rank != null) return cat.tier_rank
    const match = sortedPlans.find((p) => p.name === subStatus?.plan_name)
    return match?.catalog?.tier_rank ?? (subStatus?.tier === 'free' ? 0 : 1)
  }

  const handleUpgrade = async (planName: string, billingInterval?: 'monthly' | 'annual') => {
    setActionLoading(true)
    setError(null)
    let paystackOpened = false
    try {
      const plan = plans.find((p) => p.name === planName)
      const kes = billingInterval === 'annual' ? plan?.price_annual : plan?.price_monthly
      const isPaidPlan = plan && Number(kes || 0) > 0
      const usePaystack = Boolean(paystackPublicKey && isPaidPlan && user?.email)

      if (usePaystack) {
        const body: { plan: string; callback_url: string; interval?: string; billing_interval?: string } = {
          plan: planName,
          callback_url:
            typeof window !== 'undefined'
              ? `${window.location.origin}/payment/success`
              : '',
        }
        if (billingInterval === 'annual' || plan?.billing_interval === 'annual') {
          body.interval = 'yearly'
          body.billing_interval = 'annual'
        }

        const initRes = await apiGateway.post<{ authorization_url: string; reference: string }>(
          '/subscription/paystack/initialize',
          body
        )
        if (!initRes?.authorization_url) {
          const errMsg = (initRes as { error?: string })?.error ?? 'Could not start payment'
          setError(errMsg)
          return
        }
        const authUrl = initRes.authorization_url
        const reference = initRes.reference
        const popup = window.open(authUrl, 'paystack_checkout', 'width=600,height=700,scrollbars=yes')
        paystackOpened = true

        const handleMessage = (event: MessageEvent) => {
          if (event.data?.type === 'paystack_success' && event.data?.reference === reference) {
            window.removeEventListener('message', handleMessage)
            apiGateway
              .post('/subscription/paystack/verify', { reference: event.data.reference })
              .then(() => loadAll())
              .catch((e: unknown) => setError(e instanceof Error ? e.message : 'Verification failed'))
              .finally(() => setActionLoading(false))
          }
        }
        window.addEventListener('message', handleMessage)

        const checkClosed = setInterval(() => {
          if (popup?.closed) {
            clearInterval(checkClosed)
            window.removeEventListener('message', handleMessage)
            setActionLoading(false)
          }
        }, 500)
      } else {
        if (isPaidPlan) {
          setError('Payments are required for this plan. Paystack is not configured for checkout.')
          return
        }
        // Free plans can be applied without Paystack.
        const body: { plan: string; billing_interval?: string } = { plan: planName }
        if (billingInterval) body.billing_interval = billingInterval
        await apiGateway.post('/subscription/simulate-payment', body)
        await loadAll()
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Payment failed')
    } finally {
      if (!paystackOpened) setActionLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!confirm('Cancel subscription? Access continues until end of billing period.')) return
    try {
      setActionLoading(true)
      await apiGateway.post('/subscription/cancel', {})
      await loadAll()
    } catch (err: any) {
      setError(err?.message || 'Failed to cancel')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDowngrade = async (planName: string) => {
    if (!confirm('Schedule this downgrade for the end of your current billing period? No refunds.')) return
    try {
      setActionLoading(true)
      setError(null)
      await apiGateway.post('/subscription/downgrade', { plan: planName })
      await loadAll()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to schedule downgrade')
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancelDowngrade = async () => {
    try {
      setActionLoading(true)
      setError(null)
      await apiGateway.post('/subscription/downgrade/cancel', {})
      await loadAll()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to cancel scheduled downgrade')
    } finally {
      setActionLoading(false)
    }
  }

  const displayLabel = (plan: Plan) => plan.catalog?.display_name || plan.name

  /** USD catalog → KES (policy rate) → user’s local currency for display. */
  const renderPlanPrice = (plan: Plan) => {
    const c = plan.catalog || {}
    const period = plan.billing_interval === 'annual' ? '/year' : '/month'

    if (plan.billing_interval === 'annual') {
      if (c.usd_annual != null) {
        return (
          <>
            <p className="text-och-mint text-xl font-semibold">
              {formatUsd(c.usd_annual)}
              {period}
            </p>
            <p className="text-xs text-och-steel mt-1">
              ≈ {formatUsdApproxLocal(c.usd_annual, selectedCountry, kesRate)}
              {period}
            </p>
          </>
        )
      }
      if (plan.price_annual) {
        return (
          <>
            <p className="text-och-mint text-xl font-semibold">
              {formatFromKES(plan.price_annual, selectedCountry)}
              {period}
            </p>
            <p className="text-xs text-och-steel mt-1">KES {Number(plan.price_annual).toLocaleString()}</p>
          </>
        )
      }
      return <p className="text-och-mint text-xl font-semibold">—</p>
    }

    if (plan.billing_interval === 'none' || (plan.price_monthly ?? 0) === 0) {
      return <p className="text-och-mint text-xl font-semibold">Free</p>
    }

    if (c.usd_monthly != null) {
      return (
        <>
          <p className="text-och-mint text-xl font-semibold">
            {formatUsd(c.usd_monthly)}
            {period}
          </p>
          <p className="text-xs text-och-steel mt-1">
            ≈ {formatUsdApproxLocal(c.usd_monthly, selectedCountry, kesRate)}
            {period}
          </p>
          {plan.price_monthly && selectedCountry !== 'KE' ? (
            <p className="text-xs text-och-steel/80 mt-0.5">
              Charged KSh {Number(plan.price_monthly).toLocaleString()}
            </p>
          ) : null}
        </>
      )
    }

    return (
      <>
        <p className="text-och-mint text-xl font-semibold">
          {formatFromKES(plan.price_monthly || 0, selectedCountry)}
          {period}
        </p>
        <p className="text-xs text-och-steel mt-1">
          KES {Number(plan.price_monthly || 0).toLocaleString()}
        </p>
      </>
    )
  }

  const mentorshipLabel = (plan: Plan) => {
    const n = plan.catalog?.mentorship_credits_per_month
    if (n === null || n === undefined) return 'Unlimited'
    return `${n}/month`
  }

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
          <p className="text-och-steel text-sm">Loading...</p>
        </div>
      </div>
    )
  }

  const rank = currentRank()

  return (
    <div className="w-full py-6 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-och-mint">Subscription</h1>
        <p className="text-sm text-och-steel">
          <span className="text-white/90">{countryLabel}</span>
          {' · '}
          <span className="font-medium tabular-nums">{currencyCode}</span>
          {' · '}
          <span className="text-och-steel/90">
            {selectedCountry === 'KE'
              ? `USD list × ${kesRate} → KES (ledger)`
              : `USD × ${kesRate} KES → ${currencyCode}`}
          </span>
        </p>
      </div>

      {error && (
        <Card className="p-4 bg-och-orange/10 border-och-orange/30">
          <div className="flex items-center gap-2 text-och-orange">
            <AlertCircle className="w-4 h-4" />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {(policy.grace_period_days_monthly != null ||
        policy.academic_discount_percent != null ||
        policy.renewal_attempt_days_before != null) && (
        <Card className="p-3 border border-och-steel/20 bg-och-midnight/40">
          <div className="flex gap-2 items-center text-xs text-och-steel">
            <Info className="w-4 h-4 text-och-mint shrink-0" />
            <p className="leading-snug">
              {policy.auto_renewal_default !== false && <span>Paid plans auto-renew until cancelled. </span>}
              {policy.grace_period_days_monthly != null && (
                <span>Grace (monthly): {policy.grace_period_days_monthly}d. </span>
              )}
              {policy.grace_period_days_annual != null && (
                <span>Grace (annual): {policy.grace_period_days_annual}d. </span>
              )}
              {policy.renewal_attempt_days_before != null && (
                <span>Renewal charge {policy.renewal_attempt_days_before}d before period end. </span>
              )}
              {policy.academic_discount_percent != null && (
                <span>Academic −{policy.academic_discount_percent}%. </span>
              )}
              {policy.promo_single_code_per_checkout && <span>One promo code per checkout.</span>}
            </p>
          </div>
        </Card>
      )}

      {subStatus && (
        <Card className="p-6 border border-och-steel/20">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <p className="text-sm text-och-steel mb-1">Current plan</p>
              <p className="text-2xl font-bold text-white">
                {subStatus.plan_catalog?.display_name || subStatus.plan_name || subStatus.tier}
              </p>
              <div className="flex flex-wrap gap-2 mt-2">
                <Badge variant="mint">{subStatus.status}</Badge>
                {subStatus.billing_interval && (
                  <Badge variant="steel">{subStatus.billing_interval}</Badge>
                )}
                {subStatus.trial_end && (
                  <Badge variant="steel">Trial ends {new Date(subStatus.trial_end).toLocaleDateString()}</Badge>
                )}
                {subStatus.grace_period_end && (
                  <Badge variant="orange">Grace until {new Date(subStatus.grace_period_end).toLocaleString()}</Badge>
                )}
                {subStatus.cancel_at_period_end && <Badge variant="steel">Cancels at period end</Badge>}
                {subStatus.pending_downgrade_plan && (
                  <Badge variant="orange">
                    Downgrade scheduled → {subStatus.pending_downgrade_plan}
                  </Badge>
                )}
              </div>
            </div>
            {subStatus.next_payment && (
              <div className="text-right">
                <p className="text-sm text-och-steel mb-1">Next renewal</p>
                <p className="text-white">{new Date(subStatus.next_payment).toLocaleDateString()}</p>
              </div>
            )}
          </div>
          {subStatus.status === 'active' && subStatus.tier !== 'free' && (
            <div className="mt-4 pt-4 border-t border-och-steel/10">
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" size="sm" disabled={actionLoading} onClick={handleCancel}>
                  Cancel subscription
                </Button>
                {subStatus.pending_downgrade_plan && (
                  <Button variant="outline" size="sm" disabled={actionLoading} onClick={handleCancelDowngrade}>
                    Cancel scheduled downgrade
                  </Button>
                )}
              </div>
            </div>
          )}
        </Card>
      )}

      {financeDash && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 border border-och-steel/20">
            <p className="text-sm text-och-steel mb-1">Wallet balance</p>
            <p className="text-2xl font-bold text-white tabular-nums">
              {Number(financeDash.wallet.balance).toLocaleString()} {financeDash.wallet.currency}
            </p>
            <p className="text-xs text-och-steel mt-2">
              Last activity:{' '}
              {financeDash.wallet.last_transaction_at
                ? new Date(financeDash.wallet.last_transaction_at).toLocaleString()
                : '—'}
            </p>
          </Card>
          <Card className="p-6 border border-och-steel/20">
            <p className="text-sm text-och-steel mb-1">Credits</p>
            <p className="text-2xl font-bold text-white tabular-nums">
              {Number(financeDash.credits.active_balance).toLocaleString()}
            </p>
            <p className="text-xs text-och-steel mt-2">
              Credit records: {financeDash.credits.total_credits}
            </p>
          </Card>
          <Card className="p-6 border border-och-steel/20">
            <p className="text-sm text-och-steel mb-1">Invoices</p>
            <p className="text-2xl font-bold text-white tabular-nums">{financeDash.invoices.total}</p>
            <p className="text-xs text-och-steel mt-2">
              Pending: {financeDash.invoices.pending} · Overdue: {financeDash.invoices.overdue}
            </p>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {sortedPlans.map((plan) => {
          const cat = plan.catalog || {}
          const feat = cat.features || {}
          const pr = cat.tier_rank ?? 0
          const isCurrent = plan.name === subStatus?.plan_name
          const isUpgrade = pr > rank
          const isDowngrade = pr < rank
          const isPremiumSku = plan.name === 'och_premium'

          return (
            <div
              key={plan.id}
              className={`relative p-6 rounded-lg border-2 transition-all ${
                feat.tier_7_9_access
                  ? 'bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40'
                  : plan.tier === 'starter'
                  ? 'bg-gradient-to-br from-och-defender/20 to-och-defender/5 border-och-defender/40'
                  : 'bg-gradient-to-br from-och-steel/20 to-och-steel/5 border-och-steel/30'
              } ${isCurrent ? 'ring-2 ring-och-mint' : ''}`}
            >
              {feat.tier_7_9_access && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge variant="gold" className="text-xs font-bold px-3 py-1">
                    PREMIUM
                  </Badge>
                </div>
              )}
              {isCurrent && (
                <div className="absolute -top-3 right-4">
                  <Badge variant="mint" className="text-xs font-bold">
                    Current
                  </Badge>
                </div>
              )}

              <div className="mt-8">
                <h3 className="text-2xl font-bold text-white mb-2">{displayLabel(plan)}</h3>
                <div className="mb-4">
                  {renderPlanPrice(plan)}
                  {cat.annual_savings_percent != null && (
                    <p className="text-xs text-och-mint mt-1">
                      Annual savings vs monthly: ~{cat.annual_savings_percent}%
                    </p>
                  )}
                </div>

                {cat.trial_days ? (
                  <p className="text-xs text-och-steel mb-2">
                    Trial: {cat.trial_days} days
                    {cat.trial_requires_payment_method ? ' (card on file)' : ' (no card required)'}
                  </p>
                ) : null}

                <div className="space-y-2 mb-6 min-h-[120px] text-xs">
                  {cat.tier_range && (
                    <p className="text-white flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-och-mint shrink-0" />
                      Tiers {cat.tier_range.min ?? '—'}–{cat.tier_range.max ?? '—'}
                    </p>
                  )}
                  <p className="text-white flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-och-mint shrink-0" />
                    Mentorship credits: {mentorshipLabel(plan)}
                  </p>
                  {feat.tier_2_6_access && (
                    <p className="text-white flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-och-mint shrink-0" />
                      Tier 2–6 access
                    </p>
                  )}
                  {feat.tier_7_9_access && (
                    <p className="text-white flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-och-mint shrink-0" />
                      Tier 7–9 access
                    </p>
                  )}
                  {feat.certification_prep && (
                    <p className="text-white flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-och-mint shrink-0" />
                      Certification prep
                    </p>
                  )}
                  {feat.priority_support && (
                    <p className="text-white flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-och-mint shrink-0" />
                      Priority support
                    </p>
                  )}
                </div>

                {isPremiumSku ? (
                  <div className="space-y-2">
                    <Button
                      variant="mint"
                      className="w-full"
                      disabled={
                        actionLoading ||
                        (isCurrent && subStatus?.billing_interval === 'monthly')
                      }
                      onClick={() => handleUpgrade(plan.name, 'monthly')}
                    >
                      {isCurrent && subStatus?.billing_interval === 'monthly' ? 'Current' : 'Monthly'}
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full"
                      disabled={
                        actionLoading ||
                        (isCurrent && subStatus?.billing_interval === 'annual')
                      }
                      onClick={() => handleUpgrade(plan.name, 'annual')}
                    >
                      {isCurrent && subStatus?.billing_interval === 'annual' ? 'Current' : 'Annual (save)'}
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant={isUpgrade ? (feat.tier_7_9_access ? 'gold' : 'mint') : 'outline'}
                    className="w-full"
                    disabled={isCurrent || actionLoading}
                    onClick={() =>
                      isDowngrade
                        ? handleDowngrade(plan.name)
                        : handleUpgrade(
                            plan.name,
                            plan.billing_interval === 'annual' ? 'annual' : 'monthly'
                          )
                    }
                  >
                    {isCurrent ? 'Current plan' : isUpgrade ? 'Choose plan' : 'Downgrade at period end'}
                  </Button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {sortedPlans.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-bold text-white mb-4">Compare features</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-och-steel/20">
                  <th className="text-left p-3 text-white">Feature</th>
                  {sortedPlans.map((p) => (
                    <th key={p.id} className="text-left p-3 text-white min-w-[120px]">
                      {displayLabel(p)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-och-steel/10">
                  <td className="p-3 text-och-steel">Tier 2–6 access</td>
                  {sortedPlans.map((p) => (
                    <td key={p.id} className="p-3">
                      {p.catalog?.features?.tier_2_6_access ? (
                        <CheckCircle2 className="w-4 h-4 text-och-mint" />
                      ) : (
                        <span className="text-och-steel">—</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-och-steel/10">
                  <td className="p-3 text-och-steel">Tier 7–9 access</td>
                  {sortedPlans.map((p) => (
                    <td key={p.id} className="p-3">
                      {p.catalog?.features?.tier_7_9_access ? (
                        <CheckCircle2 className="w-4 h-4 text-och-mint" />
                      ) : (
                        <span className="text-och-steel">—</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-och-steel/10">
                  <td className="p-3 text-och-steel">Mentorship credits / mo</td>
                  {sortedPlans.map((p) => (
                    <td key={p.id} className="p-3 text-white">
                      {mentorshipLabel(p)}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-och-steel/10">
                  <td className="p-3 text-och-steel">Priority support</td>
                  {sortedPlans.map((p) => (
                    <td key={p.id} className="p-3">
                      {p.catalog?.features?.priority_support ? (
                        <CheckCircle2 className="w-4 h-4 text-och-mint" />
                      ) : (
                        <span className="text-och-steel">—</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr className="border-b border-och-steel/10">
                  <td className="p-3 text-och-steel">Certification prep</td>
                  {sortedPlans.map((p) => (
                    <td key={p.id} className="p-3">
                      {p.catalog?.features?.certification_prep ? (
                        <CheckCircle2 className="w-4 h-4 text-och-mint" />
                      ) : (
                        <span className="text-och-steel">—</span>
                      )}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {billing.length > 0 && (
        <Card className="p-6">
          <h2 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
            <CreditCard className="w-5 h-5" /> Billing history
          </h2>
          <p className="text-xs text-och-steel mb-4">Stored in KES · shown as {currencyCode}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-och-steel/20">
                  <th className="text-left py-2 px-3 text-och-steel">Date</th>
                  <th className="text-left py-2 px-3 text-och-steel">Plan</th>
                  <th className="text-left py-2 px-3 text-och-steel">Amount</th>
                  <th className="text-left py-2 px-3 text-och-steel">Status</th>
                </tr>
              </thead>
              <tbody>
                {billing.map((b, i) => (
                  <tr key={i} className="border-b border-och-steel/10">
                    <td className="py-2 px-3 text-och-steel">
                      {new Date(b.date).toLocaleDateString()}
                    </td>
                    <td className="py-2 px-3 text-white">{b.plan_name}</td>
                    <td className="py-2 px-3 text-white">
                      {formatFromKES(b.amount, selectedCountry)}
                    </td>
                    <td className="py-2 px-3">
                      <Badge variant={b.status === 'completed' ? 'mint' : 'steel'}>{b.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
