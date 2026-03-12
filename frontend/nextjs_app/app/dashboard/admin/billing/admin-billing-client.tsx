'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { apiGateway } from '@/services/apiGateway'
import { 
  Users, DollarSign, AlertTriangle, TrendingUp, 
  Settings, Plus, Edit, Eye, Download, RefreshCw 
} from 'lucide-react'

interface BillingMetrics {
  subscription_metrics: {
    total: number
    active: number
    trial: number
    past_due: number
    suspended: number
  }
  revenue_metrics: {
    monthly_revenue: number
    completed_billing_periods: number
  }
  dunning_metrics: {
    active_dunning_sequences: number
    successful_recoveries: number
  }
}

interface PlanVersion {
  id: string
  plan_id: string
  version: number
  name: string
  price_monthly: number
  price_annual: number
  status: string
  created_at: string
}

interface Subscription {
  id: string
  user_email: string
  plan_version: {
    name: string
    version: number
  }
  status: string
  billing_cycle: string
  current_period_end: string
  created_at: string
}

export default function AdminBillingClient() {
  const [metrics, setMetrics] = useState<BillingMetrics | null>(null)
  const [planVersions, setPlanVersions] = useState<PlanVersion[]>([])
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Mock data for now - replace with actual API calls
      const mockMetrics = {
        subscription_metrics: { total: 1250, active: 980, trial: 150, past_due: 85, suspended: 35 },
        revenue_metrics: { monthly_revenue: 28500, completed_billing_periods: 980 },
        dunning_metrics: { active_dunning_sequences: 85, successful_recoveries: 45 }
      }
      
      const mockPlans = [
        { id: '1', plan_id: 'free', version: 1, name: 'Free Tier', price_monthly: 0, price_annual: 0, status: 'active', created_at: '2024-01-01' },
        { id: '2', plan_id: 'starter', version: 1, name: 'Starter Tier', price_monthly: 3, price_annual: 30, status: 'active', created_at: '2024-01-01' },
        { id: '3', plan_id: 'premium', version: 1, name: 'Premium Tier', price_monthly: 7, price_annual: 70, status: 'active', created_at: '2024-01-01' }
      ]
      
      const mockSubscriptions = [
        { id: '1', user_email: 'user1@example.com', plan_version: { name: 'Premium Tier', version: 1 }, status: 'ACTIVE', billing_cycle: 'monthly', current_period_end: '2024-02-01', created_at: '2024-01-01' },
        { id: '2', user_email: 'user2@example.com', plan_version: { name: 'Starter Tier', version: 1 }, status: 'TRIAL', billing_cycle: 'monthly', current_period_end: '2024-01-15', created_at: '2024-01-01' }
      ]
      
      setMetrics(mockMetrics)
      setPlanVersions(mockPlans)
      setSubscriptions(mockSubscriptions)
    } catch (err: any) {
      setError(err?.message || 'Failed to load dashboard data')
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors = {
      ACTIVE: 'bg-green-500/20 text-green-400 border-green-500/30',
      TRIAL: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      PAST_DUE: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      SUSPENDED: 'bg-red-500/20 text-red-400 border-red-500/30',
      CANCELED: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      EXPIRED: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
    }
    return colors[status as keyof typeof colors] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  }

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-och-mint border-t-transparent rounded-full animate-spin" />
          <p className="text-och-steel text-sm">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full py-6 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold mb-2 text-och-mint">Enhanced Billing Administration</h1>
          <p className="text-och-steel">Manage subscription plans, billing, and analytics</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={loadDashboardData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Card className="p-4 bg-red-500/10 border-red-500/30">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-4 h-4" />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {/* Metrics Overview */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-och-steel mb-1">Total Subscriptions</p>
                <p className="text-3xl font-bold text-white">{metrics.subscription_metrics.total.toLocaleString()}</p>
              </div>
              <Users className="w-8 h-8 text-och-mint" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-och-steel mb-1">Monthly Revenue</p>
                <p className="text-3xl font-bold text-white">${metrics.revenue_metrics.monthly_revenue.toLocaleString()}</p>
              </div>
              <DollarSign className="w-8 h-8 text-och-mint" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-och-steel mb-1">Active Subscriptions</p>
                <p className="text-3xl font-bold text-white">{metrics.subscription_metrics.active.toLocaleString()}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-och-mint" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-och-steel mb-1">Issues Requiring Attention</p>
                <p className="text-3xl font-bold text-white">
                  {(metrics.subscription_metrics.past_due + metrics.subscription_metrics.suspended).toLocaleString()}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-yellow-400" />
            </div>
          </Card>
        </div>
      )}

      {/* Subscription Status Breakdown */}
      {metrics && (
        <Card className="p-6">
          <h2 className="text-xl font-bold text-white mb-4">Subscription Status Breakdown</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">{metrics.subscription_metrics.active}</p>
              <p className="text-sm text-och-steel">Active</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-400">{metrics.subscription_metrics.trial}</p>
              <p className="text-sm text-och-steel">Trial</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-yellow-400">{metrics.subscription_metrics.past_due}</p>
              <p className="text-sm text-och-steel">Past Due</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-400">{metrics.subscription_metrics.suspended}</p>
              <p className="text-sm text-och-steel">Suspended</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-och-mint">{metrics.dunning_metrics.successful_recoveries}</p>
              <p className="text-sm text-och-steel">Recovered</p>
            </div>
          </div>
        </Card>
      )}

      {/* Plan Versions Management */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white">Plan Versions</h2>
          <Button variant="mint">
            <Plus className="w-4 h-4 mr-2" />
            Create Plan Version
          </Button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-och-steel/20">
                <th className="text-left py-3 px-4 text-och-steel">Plan</th>
                <th className="text-left py-3 px-4 text-och-steel">Version</th>
                <th className="text-left py-3 px-4 text-och-steel">Monthly Price</th>
                <th className="text-left py-3 px-4 text-och-steel">Annual Price</th>
                <th className="text-left py-3 px-4 text-och-steel">Status</th>
                <th className="text-left py-3 px-4 text-och-steel">Created</th>
                <th className="text-left py-3 px-4 text-och-steel">Actions</th>
              </tr>
            </thead>
            <tbody>
              {planVersions.map(plan => (
                <tr key={plan.id} className="border-b border-och-steel/10">
                  <td className="py-3 px-4 text-white font-medium">{plan.name}</td>
                  <td className="py-3 px-4 text-och-steel">v{plan.version}</td>
                  <td className="py-3 px-4 text-white">${plan.price_monthly}</td>
                  <td className="py-3 px-4 text-white">${plan.price_annual || 'N/A'}</td>
                  <td className="py-3 px-4">
                    <Badge variant={plan.status === 'active' ? 'mint' : 'steel'}>
                      {plan.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-4 text-och-steel">
                    {new Date(plan.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <Button variant="ghost" size="sm">
                        <Edit className="w-3 h-3" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recent Subscriptions */}
      <Card className="p-6">
        <h2 className="text-xl font-bold text-white mb-4">Recent Subscriptions</h2>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-och-steel/20">
                <th className="text-left py-3 px-4 text-och-steel">User</th>
                <th className="text-left py-3 px-4 text-och-steel">Plan</th>
                <th className="text-left py-3 px-4 text-och-steel">Status</th>
                <th className="text-left py-3 px-4 text-och-steel">Billing</th>
                <th className="text-left py-3 px-4 text-och-steel">Period End</th>
                <th className="text-left py-3 px-4 text-och-steel">Created</th>
                <th className="text-left py-3 px-4 text-och-steel">Actions</th>
              </tr>
            </thead>
            <tbody>
              {subscriptions.slice(0, 10).map(subscription => (
                <tr key={subscription.id} className="border-b border-och-steel/10">
                  <td className="py-3 px-4 text-white">{subscription.user_email}</td>
                  <td className="py-3 px-4 text-och-steel">
                    {subscription.plan_version.name} v{subscription.plan_version.version}
                  </td>
                  <td className="py-3 px-4">
                    <div className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(subscription.status)}`}>
                      {subscription.status}
                    </div>
                  </td>
                  <td className="py-3 px-4 text-och-steel capitalize">{subscription.billing_cycle}</td>
                  <td className="py-3 px-4 text-och-steel">
                    {new Date(subscription.current_period_end).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-och-steel">
                    {new Date(subscription.created_at).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <Button variant="ghost" size="sm">
                      <Eye className="w-3 h-3" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}