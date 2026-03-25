export type InstitutionTierKey = 'tier_1_50' | 'tier_51_200' | 'tier_201_500' | 'tier_500_plus'
export type BillingCycleKey = 'monthly' | 'quarterly' | 'annual'

export const INSTITUTION_TIER_LABEL: Record<InstitutionTierKey, string> = {
  tier_1_50: '1–50 students',
  tier_51_200: '51–200 students',
  tier_201_500: '201–500 students',
  tier_500_plus: '500+ students',
}

/** USD per student / month (2.2.2) */
export const TIER_USD_PER_STUDENT_MONTH: Record<InstitutionTierKey, number> = {
  tier_1_50: 15,
  tier_51_200: 12,
  tier_201_500: 9,
  tier_500_plus: 7,
}

export const BILLING_CYCLE_LABEL: Record<BillingCycleKey, string> = {
  monthly: 'Monthly (net 30)',
  quarterly: 'Quarterly (net 30)',
  annual: 'Annual (net 30, ~2% discount)',
}

export function formatUsd(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}
