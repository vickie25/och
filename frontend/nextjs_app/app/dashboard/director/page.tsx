'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import OverviewClient from './overview-client'

export default function DirectorDashboard() {
  return (
    <RouteGuard>
      <OverviewClient />
    </RouteGuard>
  )
}
