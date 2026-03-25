import { Suspense } from 'react'
import InstitutionClient from './institution-client'

export default function InstitutionDashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[40vh] items-center justify-center p-8 text-och-steel">
          Loading dashboard…
        </div>
      }
    >
      <InstitutionClient />
    </Suspense>
  )
}
