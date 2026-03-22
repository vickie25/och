/**
 * System-wide currency model.
 * Primary currency is KES (Kenyan Shilling). All subscription and stored amounts are in KES.
 * Converts KES to the user's country currency for display only.
 */

// Rate: 1 KES = rate units of local currency (e.g. 1 KES ≈ 17.8 TZS)
const KES_TO_LOCAL: Record<string, number> = {
  KE: 1,
  DZ: 0.12,   // Algerian Dinar
  AO: 6.5,    // Angolan Kwanza
  BJ: 1.9,    // West African CFA
  BW: 0.078,  // Botswana Pula
  BF: 1.9,    // West African CFA
  BI: 24,     // Burundian Franc
  CV: 0.65,   // Cape Verdean Escudo
  CM: 0.52,   // Central African CFA
  CF: 0.52,   // Central African CFA
  TD: 0.52,   // Central African CFA
  KM: 2.1,    // Comorian Franc
  CG: 0.52,   // Central African CFA
  CD: 27,     // Congolese Franc
  CI: 1.9,    // West African CFA
  DJ: 1.8,    // Djiboutian Franc
  EG: 0.19,   // Egyptian Pound
  GQ: 0.52,   // Central African CFA
  ER: 0.05,   // Eritrean Nakfa
  SZ: 0.14,   // Swazi Lilangeni
  ET: 1.5,    // Ethiopian Birr
  GA: 0.52,   // Central African CFA
  GM: 0.13,   // Gambian Dalasi
  GH: 0.012,  // Ghanaian Cedi
  GN: 0.078,  // Guinean Franc
  GW: 0.078,  // Guinea-Bissau Peso
  LS: 0.14,   // Lesotho Loti
  LR: 0.006,  // Liberian Dollar
  LY: 0.002,  // Libyan Dinar
  MG: 0.032,  // Malagasy Ariary
  MW: 0.11,   // Malawian Kwacha
  ML: 1.9,    // West African CFA
  MR: 0.36,   // Mauritanian Ouguiya
  MU: 0.29,   // Mauritian Rupee
  MA: 0.078,  // Moroccan Dirham
  MZ: 0.52,   // Mozambican Metical
  NA: 0.14,   // Namibian Dollar
  NE: 1.9,    // West African CFA
  NG: 0.009,  // Nigerian Naira
  RW: 0.77,   // Rwandan Franc
  ST: 0.065,  // Dobra
  SN: 1.9,    // West African CFA
  SC: 0.58,   // Seychellois Rupee
  SL: 0.006,  // Leone
  SO: 0.014,  // Somali Shilling
  ZA: 0.14,   // South African Rand
  SS: 0.025,  // South Sudanese Pound
  SD: 0.014,  // Sudanese Pound
  TZ: 17.8,   // Tanzanian Shilling
  TG: 1.9,    // West African CFA
  TN: 0.024,  // Tunisian Dinar
  UG: 28.5,   // Ugandan Shilling
  ZM: 0.12,   // Zambian Kwacha
  ZW: 0.014,  // Zimbabwean Dollar (ZWL)
}

const CURRENCY_CODES: Record<string, string> = {
  KE: 'KES',
  DZ: 'DZD', AO: 'AOA', BJ: 'XOF', BW: 'BWP', BF: 'XOF', BI: 'BIF', CV: 'CVE',
  CM: 'XAF', CF: 'XAF', TD: 'XAF', KM: 'KMF', CG: 'XAF', CD: 'CDF', CI: 'XOF',
  DJ: 'DJF', EG: 'EGP', GQ: 'XAF', ER: 'ERN', SZ: 'SZL', ET: 'ETB', GA: 'XAF',
  GM: 'GMD', GH: 'GHS', GN: 'GNF', GW: 'XOF', LS: 'LSL', LR: 'LRD', LY: 'LYD',
  MG: 'MGA', MW: 'MWK', ML: 'XOF', MR: 'MRU', MU: 'MUR', MA: 'MAD', MZ: 'MZN',
  NA: 'NAD', NE: 'XOF', NG: 'NGN', RW: 'RWF', ST: 'STN', SN: 'XOF', SC: 'SCR',
  SL: 'SLE', SO: 'SOS', ZA: 'ZAR', SS: 'SSP', SD: 'SDG', TZ: 'TZS', TG: 'XOF',
  TN: 'TND', UG: 'UGX', ZM: 'ZMW', ZW: 'ZWL',
}

const CURRENCY_SYMBOLS: Record<string, string> = {
  KES: 'KSh', DZD: 'DA', BWP: 'P', ZAR: 'R', NGN: '₦', GHS: '₵', TZS: 'TSh',
  UGX: 'USh', ETB: 'Br', RWF: 'FRw', XOF: 'CFA', XAF: 'FCFA', CDF: 'FC',
  EGP: 'E£', MUR: '₨', MAD: 'DH', ZMW: 'ZK', GMD: 'D', LRD: '$', LYD: 'LD',
  MGA: 'Ar', MWK: 'MK', MZN: 'MT', NAD: '$', RWF: 'FRw', SLE: 'Le', SOS: 'Sh',
  SZL: 'E', SSP: '£', SDG: '£', TND: 'DT', ZWL: '$', CVE: 'Esc', DJF: 'Fdj',
  ERN: 'Nfk', SZL: 'E', GNF: 'FG', LSL: 'L', MRU: 'UM', STN: 'Db', SCR: '₨',
  KMF: 'CF', BIF: 'FBu', AOA: 'Kz', XAF: 'FCFA',
}

/**
 * Get currency code for a country (ISO 3166-1 alpha-2).
 */
export function getCurrencyCode(countryCode?: string | null): string {
  if (!countryCode) return 'KES'
  return CURRENCY_CODES[countryCode.toUpperCase()] || 'KES'
}

/**
 * Convert KES (system primary) to user's local currency for display.
 */
export function convertKEStoLocal(kesAmount: number, countryCode?: string | null): number {
  if (kesAmount == null || kesAmount === 0) return 0
  const code = countryCode?.toUpperCase() || 'KE'
  const rate = KES_TO_LOCAL[code] ?? KES_TO_LOCAL['KE']
  return Math.round(kesAmount * rate * 100) / 100
}

/**
 * Format a KES amount in the user's local currency (converts then formats).
 * Use this across the app for subscriptions, revenue, etc.
 */
/** Format a USD list price (Stream A catalog / admin USD fields). */
export function formatUsd(amount: number | null | undefined): string {
  if (amount == null || Number.isNaN(amount)) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount)
}

/** Convert USD list/catalog amounts to KES using admin policy rate (ledger is KES). */
export function kesFromUsdAmount(usd: number, kesPerUsd: number): number {
  if (usd == null || Number.isNaN(usd) || !kesPerUsd) return 0
  return Math.round(usd * kesPerUsd * 100) / 100
}

/** English country name for ISO 3166-1 alpha-2 (e.g. UG → Uganda). */
export function getCountryDisplayName(countryCode?: string | null): string {
  const code = (countryCode || 'KE').toUpperCase()
  try {
    const dn = new Intl.DisplayNames(['en'], { type: 'region' })
    return dn.of(code) || code
  } catch {
    return code
  }
}

/**
 * Approximate local currency for a USD list price: USD → KES (policy) → local display.
 */
export function formatUsdApproxLocal(
  usd: number | null | undefined,
  countryCode: string | null | undefined,
  kesPerUsd: number,
): string {
  if (usd == null || Number.isNaN(usd)) return ''
  const kes = kesFromUsdAmount(usd, kesPerUsd)
  return formatFromKES(kes, countryCode)
}

export function formatFromKES(kesAmount: number, countryCode?: string | null): string {
  const local = convertKEStoLocal(kesAmount, countryCode)
  const currencyCode = getCurrencyCode(countryCode)
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(local)
  const symbol = CURRENCY_SYMBOLS[currencyCode] || currencyCode
  return `${symbol} ${formatted}`
}

/**
 * Format currency amount with code (e.g. "1,234 KES").
 */
export function formatCurrency(amount: number, countryCode?: string | null): string {
  const currencyCode = getCurrencyCode(countryCode)
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
  return `${formatted} ${currencyCode}`
}

/**
 * Format currency with symbol (e.g. "KSh 1,234").
 */
export function formatCurrencyWithSymbol(amount: number, countryCode?: string | null): string {
  const currencyCode = getCurrencyCode(countryCode)
  const formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
  const symbol = CURRENCY_SYMBOLS[currencyCode] || currencyCode
  return `${symbol} ${formatted}`
}

/** @deprecated Use convertKEStoLocal and formatFromKES. Subscription amounts are in KES. */
export function convertUSDToLocal(usdAmount: number, countryCode?: string | null): number {
  return convertKEStoLocal(usdAmount, countryCode)
}

/** @deprecated System uses KES only; avoid converting to USD. */
export function convertLocalToUSD(localAmount: number, countryCode?: string | null): number {
  if (!localAmount || localAmount === 0) return 0
  const code = countryCode?.toUpperCase() || 'KE'
  const rate = KES_TO_LOCAL[code] ?? 1
  if (!rate) return 0
  return localAmount / rate
}

/**
 * Calculate annual price from monthly KES with 10% discount.
 * Subscription amounts are in KES.
 */
export function calculateAnnualPriceFromKES(monthlyKes: number, countryCode?: string | null): {
  monthlyKes: number
  annualKes: number
  annualLocal: number
  discount: number
  formattedMonthly: string
  formattedAnnual: string
} {
  const annualKes = monthlyKes * 12
  const discount = annualKes * 0.1
  const annualDiscountedKes = annualKes - discount
  const monthlyLocal = convertKEStoLocal(monthlyKes, countryCode)
  const annualLocal = convertKEStoLocal(annualDiscountedKes, countryCode)
  return {
    monthlyKes,
    annualKes: annualDiscountedKes,
    annualLocal,
    discount,
    formattedMonthly: formatFromKES(monthlyKes, countryCode),
    formattedAnnual: formatFromKES(annualDiscountedKes, countryCode),
  }
}

/** @deprecated Use calculateAnnualPriceFromKES; subscription prices are in KES. */
export function calculateAnnualPrice(monthlyPriceKes: number, countryCode?: string | null): ReturnType<typeof calculateAnnualPriceFromKES> {
  return calculateAnnualPriceFromKES(monthlyPriceKes, countryCode)
}
