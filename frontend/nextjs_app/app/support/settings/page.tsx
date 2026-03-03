'use client'

import { Card } from '@/components/ui/Card'
import { CardContent } from '@/components/ui/card-enhanced'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { LifeBuoy, Shield, Hash, Ticket, User } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import Link from 'next/link'
import { Button } from '@/components/ui/Button'

export default function SupportSettingsPage() {
  const { user } = useAuth()
  const displayName = user?.first_name && user?.last_name
    ? `${user.first_name} ${user.last_name}`
    : user?.email ?? 'Support user'

  return (
    <RouteGuard requiredRoles={['support']}>
      <div className="w-full max-w-7xl py-6 px-4 sm:px-6 lg:px-8 mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Support settings</h1>
          <p className="text-sm text-slate-400">
            Internal support role: you were added by a Program Director.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <User className="w-6 h-6 text-och-defender" aria-hidden />
                <h2 className="text-lg font-semibold text-white">Profile</h2>
              </div>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-slate-400">Name</dt>
                  <dd className="text-white">{displayName}</dd>
                </div>
                <div>
                  <dt className="text-slate-400">Email</dt>
                  <dd className="text-white">{user?.email ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-slate-400">Role</dt>
                  <dd className="text-och-defender">Support</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <Ticket className="w-6 h-6 text-och-defender" aria-hidden />
                <h2 className="text-lg font-semibold text-white">Tickets</h2>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Create and manage support tickets. Assign to yourself or other support agents. Use problem codes for reporting and SLA.
              </p>
              <Link href="/support/tickets">
                <Button variant="outline" size="sm">View tickets</Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <Hash className="w-6 h-6 text-och-defender" aria-hidden />
                <h2 className="text-lg font-semibold text-white">Problem codes</h2>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Problem tracking codes (e.g. AUTH-001, BILL-002) are defined by directors or admins. You can view and attach them to tickets.
              </p>
              <Link href="/support/problem-codes">
                <Button variant="outline" size="sm">View problem codes</Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-slate-700 md:col-span-2">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <Shield className="w-6 h-6 text-och-defender" aria-hidden />
                <h2 className="text-lg font-semibold text-white">Role & access</h2>
              </div>
              <p className="text-sm text-slate-300 mb-4">
                Support is an internal role. Only Program Directors and Admins can assign the support role to users. You have access to the support dashboard, tickets, and problem codes.
              </p>
              <div className="flex items-center gap-2 text-och-steel text-sm">
                <LifeBuoy className="w-4 h-4 shrink-0" aria-hidden />
                <span>To add or remove support users, ask a Program Director to go to Director Dashboard → Support Team.</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </RouteGuard>
  )
}
