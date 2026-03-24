import { redirect } from 'next/navigation'

export default function LegacyFinanceDashboardRedirect() {
  redirect('/dashboard/finance')
}
