'use client'

import type { ReactNode } from 'react'
import { AdminLayout } from '@/components/admin/AdminLayout'

interface AdminDashboardLayoutProps {
  children: ReactNode
}

export default function AdminDashboardLayout({ children }: AdminDashboardLayoutProps) {
  return <AdminLayout>{children}</AdminLayout>
}

