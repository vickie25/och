'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'
import { OchBrandLockup } from '@/components/brand/OchLogo'

export function EmployerNavigation() {
  const pathname = usePathname()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const dashboardActive = pathname === '/dashboard/employer'
  const contractsActive = pathname?.startsWith('/dashboard/employer/contracts') ?? false
  const overviewActive = pathname === '/dashboard/employer/marketplace'

  const linkClass = (active: boolean) =>
    clsx(
      'flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 text-sm',
      'hover:bg-och-defender/20 hover:text-och-mint',
      active ? 'bg-och-defender/30 text-och-mint border-l-4 border-och-mint' : 'text-och-steel'
    )

  return (
    <>
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          type="button"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 bg-och-defender text-white rounded-lg hover:bg-och-defender/90"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {isMobileMenuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-och-midnight/90 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
          aria-hidden
        />
      )}

      <aside
        className={clsx(
          'fixed left-0 top-0 h-full w-64 bg-och-midnight border-r border-och-steel/20 z-40 transition-transform duration-300',
          'lg:translate-x-0',
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          <div className="p-6 border-b border-och-steel/20">
            <OchBrandLockup href="/dashboard/employer" title="Employers" variant="white" onClick={() => setIsMobileMenuOpen(false)} />
          </div>

          <nav className="flex-1 overflow-y-auto p-4 space-y-1" aria-label="Employer">
            <Link
              href="/dashboard/employer"
              onClick={() => setIsMobileMenuOpen(false)}
              className={linkClass(dashboardActive)}
            >
              <span className="font-medium">Dashboard</span>
            </Link>

            <Link
              href="/dashboard/employer/contracts"
              onClick={() => setIsMobileMenuOpen(false)}
              className={linkClass(contractsActive)}
            >
              <span className="font-medium">Contracts</span>
            </Link>

            <div className="pt-2 pb-1">
              <p className="px-4 text-[11px] font-semibold uppercase tracking-wider text-och-steel/70">
                Marketplace
              </p>
              <Link
                href="/dashboard/employer/marketplace"
                onClick={() => setIsMobileMenuOpen(false)}
                className={clsx(linkClass(overviewActive), 'mt-1')}
              >
                <span className="font-medium pl-1">Overview</span>
              </Link>
              <Link
                href="/dashboard/employer/marketplace/talent"
                onClick={() => setIsMobileMenuOpen(false)}
                className={linkClass(pathname?.includes('/marketplace/talent'))}
              >
                <span className="font-medium pl-1">Browse talent</span>
              </Link>
              <Link
                href="/dashboard/employer/jobs"
                onClick={() => setIsMobileMenuOpen(false)}
                className={linkClass(pathname?.startsWith('/dashboard/employer/jobs'))}
              >
                <span className="font-medium pl-1">Jobs</span>
              </Link>
            </div>

            <Link
              href="/dashboard/employer/contracts/shortlisted-students"
              onClick={() => setIsMobileMenuOpen(false)}
              className={linkClass(pathname?.includes('/shortlisted-students'))}
            >
              <span className="font-medium">Shortlisted students</span>
            </Link>

            <Link
              href="/dashboard/employer/contracts/invoices"
              onClick={() => setIsMobileMenuOpen(false)}
              className={linkClass(pathname?.includes('/contracts/invoices'))}
            >
              <span className="font-medium">Invoices</span>
            </Link>

            <Link
              href="/dashboard/employer/contracts/payments"
              onClick={() => setIsMobileMenuOpen(false)}
              className={linkClass(pathname?.includes('/contracts/payments'))}
            >
              <span className="font-medium">Payments</span>
            </Link>
          </nav>

          <div className="lg:hidden p-4 border-t border-och-steel/20">
            <div className="text-xs text-och-steel text-center">OCH Platform</div>
          </div>
        </div>
      </aside>
    </>
  )
}
