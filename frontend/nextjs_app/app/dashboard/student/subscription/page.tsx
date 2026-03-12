'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import EnhancedSubscriptionClient from './enhanced-subscription-client'

export default function SubscriptionPage() {
  return (
    <RouteGuard>
      <EnhancedSubscriptionClient />
    </RouteGuard>
  )
}

