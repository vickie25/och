/**
 * Finance API Service
 * Service functions for interacting with finance endpoints
 */

import { apiGateway } from './apiGateway'

export interface WalletData {
  id: string
  balance: number
  currency: string
  last_transaction_at: string | null
  created_at: string
  updated_at: string
}

export interface Transaction {
  id: string
  type: 'credit' | 'debit'
  amount: number
  description: string
  reference_type: string
  reference_id: string
  created_at: string
}

export interface Credit {
  id: string
  type: 'purchased' | 'promotional' | 'referral' | 'scholarship'
  amount: number
  remaining: number
  expires_at: string | null
  is_expired: boolean
  created_at: string
  updated_at: string
}

export interface Contract {
  id: string
  organization_name: string
  type: 'institution' | 'employer'
  start_date: string
  end_date: string
  status: 'proposal' | 'negotiation' | 'signed' | 'active' | 'renewal' | 'terminated'
  total_value: number
  payment_terms: string
  auto_renew: boolean
  renewal_notice_days: number
  is_active: boolean
  days_until_expiry: number
  created_at: string
  updated_at: string
}

export interface TaxRate {
  id: string
  country: string
  region: string
  rate: number
  type: 'VAT' | 'GST' | 'sales_tax'
  is_active: boolean
  effective_date: string
  created_at: string
}

export interface Invoice {
  id: string
  user_email?: string
  organization_name?: string
  contract_id?: string
  type: 'subscription' | 'institution' | 'employer' | 'cohort' | 'contract'
  amount: number
  tax: number
  total: number
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'void'
  due_date: string
  paid_date?: string
  invoice_number: string
  pdf_url?: string
  created_at: string
  updated_at: string
}

export interface MentorPayout {
  id: string
  mentor_email: string
  mentor_name: string
  amount: number
  period_start: string
  period_end: string
  status: 'pending' | 'approved' | 'paid' | 'rejected'
  payout_method: 'bank_transfer' | 'mobile_money' | 'paypal'
  paystack_transfer_id?: string
  created_at: string
  updated_at: string
}

export interface FinancialDashboard {
  wallet: {
    balance: number
    currency: string
    last_transaction_at: string | null
  }
  credits: {
    active_balance: number
    total_credits: number
  }
  invoices: {
    pending: number
    overdue: number
    total: number
  }
  recent_transactions: Transaction[]
}

class FinanceService {
  // Wallet operations
  async getMyWallet(): Promise<WalletData> {
    return apiGateway.get('/finance/wallets/my_wallet/')
  }

  async topUpWallet(walletId: string, amount: number, description?: string): Promise<{ message: string; new_balance: number }> {
    return apiGateway.post(`/finance/wallets/${walletId}/top_up/`, {
      amount,
      description: description || 'Wallet top-up'
    })
  }

  async getWalletTransactions(walletId: string): Promise<Transaction[]> {
    return apiGateway.get(`/finance/wallets/${walletId}/transactions/`)
  }

  // Credits operations
  async getCredits(): Promise<Credit[]> {
    const response = await apiGateway.get('/finance/credits/')
    return Array.isArray(response) ? response : response.results || []
  }

  async getCreditSummary(): Promise<Record<string, { total_amount: number; total_remaining: number; count: number }>> {
    return apiGateway.get('/finance/credits/summary/')
  }

  async purchaseCredits(amount: number, type: string = 'purchased', expiresDays?: number): Promise<{ message: string; credit_id: string; amount: number }> {
    const payload: any = { amount, type }
    if (expiresDays) payload.expires_days = expiresDays
    return apiGateway.post('/finance/credits/purchase/', payload)
  }

  // Contract operations
  async getContracts(): Promise<Contract[]> {
    const response = await apiGateway.get('/finance/contracts/')
    return Array.isArray(response) ? response : response.results || []
  }

  async getActiveContracts(): Promise<Contract[]> {
    return apiGateway.get('/finance/contracts/active/')
  }

  async getExpiringContracts(): Promise<Contract[]> {
    return apiGateway.get('/finance/contracts/expiring_soon/')
  }

  async createContract(contractData: Partial<Contract>): Promise<Contract> {
    return apiGateway.post('/finance/contracts/', contractData)
  }

  async updateContract(id: string, contractData: Partial<Contract>): Promise<Contract> {
    return apiGateway.put(`/finance/contracts/${id}/`, contractData)
  }

  async deleteContract(id: string): Promise<void> {
    return apiGateway.delete(`/finance/contracts/${id}/`)
  }

  // Tax rate operations
  async getTaxRates(): Promise<TaxRate[]> {
    const response = await apiGateway.get('/finance/tax-rates/')
    return Array.isArray(response) ? response : response.results || []
  }

  async getTaxRateByLocation(country: string, region?: string, type: string = 'VAT'): Promise<{ rate: number; country: string; region?: string }> {
    const params = new URLSearchParams({ country, type })
    if (region) params.append('region', region)
    return apiGateway.get(`/finance/tax-rates/by_location/?${params}`)
  }

  async createTaxRate(taxRateData: Partial<TaxRate>): Promise<TaxRate> {
    return apiGateway.post('/finance/tax-rates/', taxRateData)
  }

  async updateTaxRate(id: string, taxRateData: Partial<TaxRate>): Promise<TaxRate> {
    return apiGateway.put(`/finance/tax-rates/${id}/`, taxRateData)
  }

  async deleteTaxRate(id: string): Promise<void> {
    return apiGateway.delete(`/finance/tax-rates/${id}/`)
  }

  // Invoice operations
  async getInvoices(): Promise<Invoice[]> {
    const response = await apiGateway.get('/finance/invoices/')
    return Array.isArray(response) ? response : response.results || []
  }

  async createInvoice(invoiceData: Partial<Invoice>): Promise<Invoice> {
    return apiGateway.post('/finance/invoices/', invoiceData)
  }

  async markInvoicePaid(id: string): Promise<{ message: string }> {
    return apiGateway.post(`/finance/invoices/${id}/mark_paid/`)
  }

  // Mentor payout operations
  async getMentorPayouts(): Promise<MentorPayout[]> {
    const response = await apiGateway.get('/finance/mentor-payouts/')
    return Array.isArray(response) ? response : response.results || []
  }

  async approvePayout(id: string): Promise<{ message: string }> {
    return apiGateway.post(`/finance/mentor-payouts/${id}/approve/`)
  }

  async markPayoutPaid(id: string): Promise<{ message: string }> {
    return apiGateway.post(`/finance/mentor-payouts/${id}/mark_paid/`)
  }

  // Dashboard
  async getFinancialDashboard(): Promise<FinancialDashboard> {
    return apiGateway.get('/finance/dashboard/')
  }

  // Utility functions
  formatCurrency(amount: number, currency: string = 'USD'): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  calculateTax(amount: number, taxRate: number): number {
    return amount * (taxRate / 100)
  }

  calculateTotal(amount: number, taxRate: number): number {
    return amount + this.calculateTax(amount, taxRate)
  }
}

export const financeService = new FinanceService()
export default financeService