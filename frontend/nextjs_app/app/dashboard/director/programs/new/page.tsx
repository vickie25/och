'use client'

import { RouteGuard } from '@/components/auth/RouteGuard'
import CreateProgramForm from '@/components/director/CreateProgramForm'

export default function CreateProgramPage() {
  return (
    <RouteGuard>
      <CreateProgramForm />
    </RouteGuard>
  )
}