import { apiGateway } from '@/services/apiGateway'

export type InstitutionalBillingCycle = 'monthly' | 'quarterly' | 'annual'

export type InstitutionalContractStatus = 'draft' | 'active' | 'expired' | 'terminated' | 'pending_renewal'

export type InstitutionalContractListItem = {
  id: string
  contract_number: string
  organization: { id: number | string; name: string }
  status: InstitutionalContractStatus
  start_date: string
  end_date: string
  student_seat_count: number
  per_student_rate: number
  billing_cycle: InstitutionalBillingCycle
  monthly_amount: number
  annual_amount: number
  active_students: number
  seat_utilization: number
  total_invoiced: number
  days_until_expiry: number | null
  is_renewable: boolean
  created_at: string
}

export type InstitutionalContractsResponse = {
  contracts: InstitutionalContractListItem[]
  pagination?: { total: number; page: number; page_size: number; total_pages: number }
}

export type InstitutionalInvoiceListItem = {
  id: string
  invoice_number: string
  invoice_date: string
  due_date: string
  total_amount: number
  status: string
  is_overdue: boolean
  days_overdue: number
}

export const institutionalService = {
  async listContracts() {
    return apiGateway.get<InstitutionalContractsResponse>('/institutional/contracts/')
  },
  async getContract(id: string) {
    return apiGateway.get<unknown>(`/institutional/contracts/${id}/`)
  },
  async activateContract(id: string) {
    return apiGateway.post(`/institutional/contracts/${id}/activate/`, {})
  },
  async updateContractSeatsAndBilling(id: string, payload: { student_seat_count: number; billing_cycle: InstitutionalBillingCycle }) {
    // Institutional endpoint doesn't expose PATCH-by-default with these fields in the custom list() serializer,
    // but ModelViewSet supports update/partial_update via serializer. Keep payload minimal.
    return apiGateway.patch(`/institutional/contracts/${id}/`, payload)
  },
  async adjustSeats(id: string, payload: { new_seat_count: number; effective_date?: string; reason?: string }) {
    return apiGateway.post(`/institutional/contracts/${id}/adjust_seats/`, payload)
  },
  async listBilling() {
    return apiGateway.get<{ invoices?: InstitutionalInvoiceListItem[]; results?: InstitutionalInvoiceListItem[]; billing?: InstitutionalInvoiceListItem[] }>(
      '/institutional/billing/'
    )
  },
}

