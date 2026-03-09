'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import PlansManagementClient from './plans-management-client'

export default function PlansPage() {
  return (
    <RouteGuard>
      <PlansManagementClient />
    </RouteGuard>
  )
}















































































