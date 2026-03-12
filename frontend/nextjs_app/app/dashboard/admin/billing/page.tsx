'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import AdminBillingClient from './admin-billing-client'

export default function AdminBillingPage() {
  return (
    <RouteGuard requiredRole="admin">
      <AdminBillingClient />
    </RouteGuard>
  )
}