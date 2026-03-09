'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import SubscriptionOverviewClient from './subscription-overview-client'

export default function SubscriptionsPage() {
  return (
    <RouteGuard>
      <SubscriptionOverviewClient />
    </RouteGuard>
  )
}
