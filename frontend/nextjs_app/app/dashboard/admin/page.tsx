'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import OverviewClient from './overview-client'

export default function AdminDashboard() {
  return (
    <RouteGuard>
      <OverviewClient />
    </RouteGuard>
  )
}

