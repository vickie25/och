/**
 * Mentor Credit Wallets (Finance)
 * View mentor credit balances and transactions (earned from mentee ratings).
 */

'use client'

import { useEffect, useMemo, useState } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { financeService, type MentorCreditWallet } from '@/services/financeService'
import { Search, Star, Wallet } from 'lucide-react'

export default function MentorCreditWalletsPage() {
  const [wallets, setWallets] = useState<MentorCreditWallet[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    void load()
  }, [])

  const load = async () => {
    try {
      setLoading(true)
      const data = await financeService.getMentorCreditWallets()
      setWallets(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error('Failed to load mentor credit wallets:', e)
      setWallets([])
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    const q = searchTerm.trim().toLowerCase()
    if (!q) return wallets
    return wallets.filter((w) => {
      return (
        w.mentor_name.toLowerCase().includes(q) ||
        w.mentor_email.toLowerCase().includes(q) ||
        w.mentor_slug.toLowerCase().includes(q)
      )
    })
  }, [wallets, searchTerm])

  const totals = useMemo(() => {
    return {
      mentors: wallets.length,
      totalCredits: wallets.reduce((sum, w) => sum + (w.credits?.current_balance ?? 0), 0),
    }
  }, [wallets])

  if (loading) {
    return (
      <RouteGuard requiredRoles={['finance', 'admin']}>
        <div className="min-h-screen bg-och-midnight flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
            <p className="text-och-steel text-sm">Loading mentor credit wallets...</p>
          </div>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard requiredRoles={['finance', 'admin']}>
      <div className="min-h-screen bg-och-midnight">
        <div className="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <h1 className="text-h1 font-bold text-white">Mentor Credit Wallets</h1>
              <p className="mt-1 body-m text-och-steel">
                Mentors earn credits from mentee ratings (5★=10, 4★=8, 3★=6, 2★=4, 1★=2).
              </p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => void load()}>
                Refresh
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            <Card className="p-4 bg-och-midnight border border-och-steel/20">
              <div className="flex items-center gap-3 mb-2">
                <Wallet className="h-5 w-5 text-och-defender" />
                <p className="font-medium text-white">Mentors</p>
              </div>
              <p className="text-2xl font-bold text-white">{totals.mentors}</p>
            </Card>
            <Card className="p-4 bg-och-mint/10 border border-och-mint/30">
              <div className="flex items-center gap-3 mb-2">
                <Star className="h-5 w-5 text-och-mint" />
                <p className="font-medium text-white">Total Current Credits</p>
              </div>
              <p className="text-2xl font-bold text-white">{totals.totalCredits.toLocaleString()}</p>
            </Card>
          </div>

          <Card className="p-4 mb-6 bg-och-midnight border border-och-steel/20">
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-64">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-och-steel" />
                  <input
                    type="text"
                    placeholder="Search mentors..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:ring-2 focus:ring-och-mint"
                  />
                </div>
              </div>
            </div>
          </Card>

          <div className="space-y-4">
            {filtered.map((w) => (
              <Card key={w.mentor_id} className="p-5 bg-och-midnight border border-och-steel/20">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-white">{w.mentor_name}</h3>
                      <Badge variant="steel">{w.mentor_slug}</Badge>
                      {typeof w.average_rating === 'number' && (
                        <Badge variant="gold">{w.average_rating.toFixed(2)}★</Badge>
                      )}
                    </div>
                    <p className="text-sm text-och-steel">{w.mentor_email}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-xs text-och-steel uppercase tracking-widest font-bold">Current credits</p>
                      <p className="text-2xl font-bold text-white">{w.credits.current_balance.toLocaleString()}</p>
                    </div>
                    <div className="hidden sm:block w-px h-10 bg-och-steel/20" />
                    <div className="text-right">
                      <p className="text-xs text-och-steel uppercase tracking-widest font-bold">Total earned</p>
                      <p className="text-lg font-bold text-och-mint">{w.credits.total_earned.toLocaleString()}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-och-steel uppercase tracking-widest font-bold">Redeemed</p>
                      <p className="text-lg font-bold text-och-steel">{w.credits.total_redeemed.toLocaleString()}</p>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
            {filtered.length === 0 && (
              <Card className="p-10 bg-och-midnight border border-och-steel/20 text-center">
                <p className="text-och-steel">No mentors found.</p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </RouteGuard>
  )
}

