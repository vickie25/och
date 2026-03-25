/** Employer commercial catalog — used in UI and aligned with finance commercial terms. */

export type EmployerPlanKey = 'starter' | 'growth' | 'enterprise' | 'custom'

export const EMPLOYER_PLAN_LABEL: Record<EmployerPlanKey, string> = {
  starter: 'Starter',
  growth: 'Growth',
  enterprise: 'Enterprise',
  custom: 'Custom',
}

export interface TierRow {
  key: EmployerPlanKey
  monthlyUsd: number | null
  candidatesPerQuarter: string
  placementFeeUsd: number | null
  dedicatedAm: boolean
  notes?: string
}

export const TIER_COMPARISON: TierRow[] = [
  {
    key: 'starter',
    monthlyUsd: 500,
    candidatesPerQuarter: 'Up to 5',
    placementFeeUsd: 2000,
    dedicatedAm: false,
  },
  {
    key: 'growth',
    monthlyUsd: 1500,
    candidatesPerQuarter: 'Up to 15',
    placementFeeUsd: 1500,
    dedicatedAm: true,
  },
  {
    key: 'enterprise',
    monthlyUsd: 3500,
    candidatesPerQuarter: 'Unlimited',
    placementFeeUsd: 1000,
    dedicatedAm: true,
  },
  {
    key: 'custom',
    monthlyUsd: null,
    candidatesPerQuarter: 'Unlimited',
    placementFeeUsd: null,
    dedicatedAm: true,
    notes: 'Negotiated',
  },
]

export const RETAINER_FEATURES: Record<EmployerPlanKey, string> = {
  starter: 'Basic talent pipeline access, standard matching',
  growth: 'Priority matching, dedicated account manager',
  enterprise: 'VIP matching, custom reports, exclusive pipeline',
  custom: 'Negotiated scope, SLAs, and reporting',
}

export function formatUsd(n: number | null) {
  if (n == null) return '—'
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}
