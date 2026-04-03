'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'
import { 
  DollarSign, 
  BarChart3, 
  FileText, 
  Wallet, 
  Shield,
  Home,
  UserCircle,
  Settings,
  CreditCard,
  Building2,
  Calculator,
  Users
} from 'lucide-react'

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: number
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard/finance', icon: Home },
  { label: 'Analytics', href: '/dashboard/finance/analytics', icon: BarChart3 },
  { label: 'Wallet & Credits', href: '/dashboard/finance/wallet', icon: Wallet },
  { label: 'Billing & Invoices', href: '/dashboard/finance/billing', icon: FileText },
  { label: 'Contracts', href: '/dashboard/finance/contracts', icon: Building2 },
  { label: 'Tax Management', href: '/dashboard/finance/tax', icon: Calculator },
  { label: 'Compliance', href: '/dashboard/finance/compliance', icon: Shield },
  { label: 'Subscriptions', href: '/finance/subscriptions', icon: CreditCard },
  { label: 'Mentor Credit Wallets', href: '/finance/mentor-credit-wallets', icon: Users },
  { label: 'Reconciliation', href: '/finance/reconciliation', icon: Calculator },
  { label: 'Settings', href: '/finance/settings', icon: Settings },
]

export function FinanceNavigation() {
  const pathname = usePathname()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const isActive = (href: string) => {
    if (href === '/dashboard/finance' && pathname === '/dashboard/finance') {
      return true
    }
    if (href === '/finance/dashboard') {
      return pathname === '/finance/dashboard'
    }
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Mobile Menu Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 bg-och-defender text-white rounded-lg hover:bg-och-defender/80"
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

      {/* Mobile Overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-och-midnight/90 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={clsx(
          'fixed left-0 top-0 h-full w-64 bg-och-midnight border-r border-och-steel/20 z-40 transition-transform duration-300',
          'lg:translate-x-0',
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo/Brand */}
          <div className="p-6 border-b border-och-steel/20">
            <Link href="/dashboard/finance" className="flex items-center gap-2">
              <DollarSign className="h-8 w-8 text-och-defender" />
              <span className="text-xl font-bold text-white">OCH Finance</span>
            </Link>
          </div>

          {/* Navigation Items */}
          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={clsx(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                    active
                      ? 'bg-och-defender text-och-mint'
                      : 'text-och-steel hover:bg-och-midnight/50 hover:text-white'
                  )}
                >
                  <Icon className="h-5 w-5" />
                  <span className="font-medium">{item.label}</span>
                  {item.badge && (
                    <span className="ml-auto bg-och-defender text-white text-xs px-2 py-1 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-och-steel/20">
            <div className="text-xs text-och-steel text-center">
              MFA Required
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

