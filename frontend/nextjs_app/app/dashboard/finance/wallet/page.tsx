/**
 * Wallet Management Page
 * Manage user wallet balance, credits, and transaction history
 */

'use client'

import { useState, useEffect } from 'react'
import { RouteGuard } from '@/components/auth/RouteGuard'
import { FinanceNavigation } from '@/components/navigation/FinanceNavigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { 
  Wallet, 
  CreditCard, 
  Plus,
  ArrowUpRight,
  ArrowDownLeft,
  Clock,
  Gift,
  TrendingUp,
  DollarSign
} from 'lucide-react'

type WalletData = {
  id: string
  balance: number
  currency: string
  last_transaction_at: string | null
  created_at: string
}

type Transaction = {
  id: string
  type: 'credit' | 'debit'
  amount: number
  description: string
  reference_type: string
  created_at: string
}

type Credit = {
  id: string
  type: 'purchased' | 'promotional' | 'referral' | 'scholarship'
  amount: number
  remaining: number
  expires_at: string | null
  is_expired: boolean
  created_at: string
}

type CreditSummary = {
  [key: string]: {
    total_amount: number
    total_remaining: number
    count: number
  }
}

export default function WalletPage() {
  const [wallet, setWallet] = useState<WalletData | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [credits, setCredits] = useState<Credit[]>([])
  const [creditSummary, setCreditSummary] = useState<CreditSummary>({})
  const [loading, setLoading] = useState(true)
  const [topUpAmount, setTopUpAmount] = useState('')
  const [topUpLoading, setTopUpLoading] = useState(false)
  const [showTopUpModal, setShowTopUpModal] = useState(false)

  useEffect(() => {
    loadWalletData()
  }, [])

  const loadWalletData = async () => {
    try {
      setLoading(true)
      const [walletRes, creditsRes, creditSummaryRes] = await Promise.all([
        apiGateway.get('/finance/wallets/my_wallet/'),
        apiGateway.get('/finance/credits/'),
        apiGateway.get('/finance/credits/summary/')
      ])

      setWallet(walletRes)
      setCredits(Array.isArray(creditsRes) ? creditsRes : creditsRes.results || [])
      setCreditSummary(creditSummaryRes || {})

      // Load transactions if wallet exists
      if (walletRes?.id) {
        const transactionsRes = await apiGateway.get(`/finance/wallets/${walletRes.id}/transactions/`)
        setTransactions(Array.isArray(transactionsRes) ? transactionsRes : [])
      }
    } catch (error) {
      console.error('Failed to load wallet data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTopUp = async () => {
    if (!topUpAmount || parseFloat(topUpAmount) <= 0) return

    try {
      setTopUpLoading(true)
      await apiGateway.post(`/finance/wallets/${wallet?.id}/top_up/`, {
        amount: parseFloat(topUpAmount),
        description: 'Manual wallet top-up'
      })
      
      setTopUpAmount('')
      setShowTopUpModal(false)
      await loadWalletData()
    } catch (error) {
      console.error('Failed to top up wallet:', error)
    } finally {
      setTopUpLoading(false)
    }
  }

  const getTransactionIcon = (type: string, referenceType: string) => {
    if (type === 'credit') {
      if (referenceType === 'promotion') return <Gift className="h-4 w-4 text-och-mint" />
      return <ArrowUpRight className="h-4 w-4 text-och-savanna-green" />
    }
    return <ArrowDownLeft className="h-4 w-4 text-och-orange" />
  }

  const getCreditTypeColor = (type: string) => {
    switch (type) {
      case 'promotional': return 'mint'
      case 'referral': return 'gold'
      case 'scholarship': return 'defender'
      default: return 'steel'
    }
  }

  if (loading) {
    return (
      <RouteGuard>
        <div className="min-h-screen bg-och-midnight flex">
          <FinanceNavigation />
          <div className="flex-1 lg:ml-64 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
              <p className="text-och-steel text-sm">Loading wallet...</p>
            </div>
          </div>
        </div>
      </RouteGuard>
    )
  }

  return (
    <RouteGuard>
      <div className="min-h-screen bg-och-midnight flex">
        <FinanceNavigation />
        <div className="flex-1 lg:ml-64">
          <div className="px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-h1 font-bold text-white">Wallet & Credits</h1>
              <p className="mt-1 body-m text-och-steel">
                Manage your wallet balance, credits, and transaction history
              </p>
            </div>

            {/* Wallet Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <Card className="p-6 bg-gradient-to-br from-och-mint/20 to-och-mint/5 border-och-mint/40">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <Wallet className="h-6 w-6 text-och-mint" />
                    <h2 className="text-h2 font-semibold text-white">Wallet Balance</h2>
                  </div>
                  <Button 
                    size="sm" 
                    onClick={() => setShowTopUpModal(true)}
                    className="bg-och-mint hover:bg-och-mint/80"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Top Up
                  </Button>
                </div>
                <div className="mb-2">
                  <p className="text-3xl font-bold text-white">
                    ${wallet?.balance?.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-sm text-och-steel">{wallet?.currency || 'USD'}</p>
                </div>
                {wallet?.last_transaction_at && (
                  <p className="text-xs text-och-steel">
                    Last activity: {new Date(wallet.last_transaction_at).toLocaleDateString()}
                  </p>
                )}
              </Card>

              <Card className="p-6 bg-och-midnight border border-och-steel/20">
                <div className="flex items-center gap-3 mb-4">
                  <CreditCard className="h-6 w-6 text-och-defender" />
                  <h2 className="text-h2 font-semibold text-white">Active Credits</h2>
                </div>
                <div className="space-y-2">
                  {Object.entries(creditSummary).map(([type, data]) => (
                    <div key={type} className="flex justify-between items-center">
                      <span className="text-sm text-och-steel capitalize">{type}</span>
                      <div className="text-right">
                        <p className="text-white font-medium">${data.total_remaining.toFixed(2)}</p>
                        <p className="text-xs text-och-steel">{data.count} credits</p>
                      </div>
                    </div>
                  ))}
                  {Object.keys(creditSummary).length === 0 && (
                    <p className="text-sm text-och-steel">No active credits</p>
                  )}
                </div>
              </Card>

              <Card className="p-6 bg-och-midnight border border-och-steel/20">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingUp className="h-6 w-6 text-och-gold" />
                  <h2 className="text-h2 font-semibold text-white">Quick Stats</h2>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-och-steel">Total Credits</span>
                    <span className="text-white">{credits.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-och-steel">Recent Transactions</span>
                    <span className="text-white">{transactions.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-och-steel">Wallet Age</span>
                    <span className="text-white">
                      {wallet?.created_at ? 
                        Math.floor((Date.now() - new Date(wallet.created_at).getTime()) / (1000 * 60 * 60 * 24)) + ' days'
                        : 'N/A'
                      }
                    </span>
                  </div>
                </div>
              </Card>
            </div>

            {/* Credits Section */}
            <Card className="p-6 mb-8 bg-och-midnight border border-och-steel/20">
              <h2 className="text-h2 font-semibold text-white mb-4">Credit Details</h2>
              {credits.length === 0 ? (
                <div className="text-center py-8">
                  <Gift className="h-12 w-12 mx-auto mb-2 text-och-steel" />
                  <p className="body-m text-och-steel">No credits available</p>
                  <p className="body-s text-och-steel/70 mt-2">Credits will appear here when earned or purchased</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-och-steel/20">
                    <thead className="bg-och-midnight/50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Original Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Remaining
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Expires
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-och-steel uppercase tracking-wider">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-och-midnight divide-y divide-och-steel/20">
                      {credits.map((credit) => (
                        <tr key={credit.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={getCreditTypeColor(credit.type)}>
                              {credit.type}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                            ${credit.amount.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                            ${credit.remaining.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-och-steel">
                            {credit.expires_at ? 
                              new Date(credit.expires_at).toLocaleDateString() : 
                              'Never'
                            }
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <Badge variant={credit.is_expired ? 'orange' : 'mint'}>
                              {credit.is_expired ? 'Expired' : 'Active'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>

            {/* Transaction History */}
            <Card className="p-6 bg-och-midnight border border-och-steel/20">
              <h2 className="text-h2 font-semibold text-white mb-4">Recent Transactions</h2>
              {transactions.length === 0 ? (
                <div className="text-center py-8">
                  <Clock className="h-12 w-12 mx-auto mb-2 text-och-steel" />
                  <p className="body-m text-och-steel">No transactions yet</p>
                  <p className="body-s text-och-steel/70 mt-2">Transaction history will appear here</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {transactions.map((transaction) => (
                    <div 
                      key={transaction.id}
                      className="flex items-center justify-between p-4 bg-och-steel/10 rounded-lg border border-och-steel/20"
                    >
                      <div className="flex items-center gap-3">
                        {getTransactionIcon(transaction.type, transaction.reference_type)}
                        <div>
                          <p className="text-white font-medium">{transaction.description}</p>
                          <p className="text-sm text-och-steel">
                            {transaction.reference_type} • {new Date(transaction.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={`font-medium ${
                          transaction.type === 'credit' ? 'text-och-savanna-green' : 'text-och-orange'
                        }`}>
                          {transaction.type === 'credit' ? '+' : '-'}${transaction.amount.toFixed(2)}
                        </p>
                        <Badge variant={transaction.type === 'credit' ? 'mint' : 'orange'}>
                          {transaction.type}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>

      {/* Top Up Modal */}
      {showTopUpModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 bg-och-midnight border border-och-steel/20 w-full max-w-md mx-4">
            <h3 className="text-h3 font-semibold text-white mb-4">Top Up Wallet</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-och-steel mb-2">
                  Amount (USD)
                </label>
                <div className="relative">
                  <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-och-steel" />
                  <input
                    type="number"
                    value={topUpAmount}
                    onChange={(e) => setTopUpAmount(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-och-steel/10 border border-och-steel/20 rounded-lg text-white placeholder-och-steel/50 focus:outline-none focus:ring-2 focus:ring-och-mint"
                    placeholder="0.00"
                    min="1"
                    step="0.01"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setShowTopUpModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleTopUp}
                  disabled={topUpLoading || !topUpAmount || parseFloat(topUpAmount) <= 0}
                  className="flex-1 bg-och-mint hover:bg-och-mint/80"
                >
                  {topUpLoading ? 'Processing...' : 'Top Up'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </RouteGuard>
  )
}