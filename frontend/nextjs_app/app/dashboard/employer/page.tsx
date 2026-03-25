import { Suspense } from 'react'
import EmployerClient from './employer-client'

export default function EmployerDashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[40vh] items-center justify-center p-8 text-och-steel">
          Loading dashboard…
        </div>
      }
    >
      <EmployerClient />
    </Suspense>
  )
}
