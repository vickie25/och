'use client'

import type { ReactNode } from 'react'
import { DirectorLayout } from '@/components/director/DirectorLayout'

interface DirectorDashboardLayoutProps {
  children: ReactNode
}

export default function DirectorDashboardLayout({ children }: DirectorDashboardLayoutProps) {
  return <DirectorLayout>{children}</DirectorLayout>
}

