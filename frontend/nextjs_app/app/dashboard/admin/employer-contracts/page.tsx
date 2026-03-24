'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Building2, Users, TrendingUp, AlertTriangle } from 'lucide-react';
import { ContractsList } from './components/contracts-list';
import { RequirementsList } from './components/requirements-list';
import { AnalyticsDashboard } from './components/analytics-dashboard';
import { CreateContractModal } from './components/create-contract-modal';
import { SLADashboard } from './components/sla-dashboard';

interface DashboardStats {
  activeContracts: number;
  totalAnnualValue: number;
  avgSuccessRate: number;
  avgSLACompliance: number;
  totalPlacementsYTD: number;
  overdueRequirements: number;
}

interface ContractSummary {
  id: string;
  contractNumber: string;
  organization: string;
  status: string;
  retainerTier: string;
  activeRequirements: number;
  totalPlacements: number;
  totalRevenue: number;
}

export default function EmployerContractsDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentContracts, setRecentContracts] = useState<ContractSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch dashboard analytics
      const analyticsResponse = await fetch('/api/marketplace/employer-contracts/analytics/dashboard/');
      const analyticsData = await analyticsResponse.json();
      
      // Fetch recent contracts
      const contractsResponse = await fetch('/api/marketplace/employer-contracts/contracts/?limit=5');
      const contractsData = await contractsResponse.json();
      
      setStats({
        activeContracts: analyticsData.active_contracts_count,
        totalAnnualValue: analyticsData.total_annual_contract_value,
        avgSuccessRate: analyticsData.performance_summary.avg_placement_success_rate,
        avgSLACompliance: analyticsData.performance_summary.avg_sla_compliance_rate,
        totalPlacementsYTD: analyticsData.performance_summary.total_placements_ytd,
        overdueRequirements: 0 // Will be fetched from SLA endpoint
      });
      
      setRecentContracts(contractsData.results || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Employer Contracts</h1>
          <p className="text-gray-600 mt-2">Manage talent supply contracts and performance</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          New Contract
        </Button>
      </div>

      {/* Key Metrics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Contracts</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.activeContracts}</p>
                </div>
                <Building2 className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Annual Contract Value</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.totalAnnualValue)}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPercentage(stats.avgSuccessRate)}</p>
                </div>
                <Users className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">SLA Compliance</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPercentage(stats.avgSLACompliance)}</p>
                </div>
                <AlertTriangle className={`h-8 w-8 ${stats.avgSLACompliance > 0.9 ? 'text-green-600' : 'text-yellow-600'}`} />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="contracts">Contracts</TabsTrigger>
          <TabsTrigger value="requirements">Requirements</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="sla">SLA Monitor</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Recent Contracts */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Contracts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentContracts.map((contract) => (
                  <div key={contract.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div>
                        <p className="font-medium">{contract.organization}</p>
                        <p className="text-sm text-gray-600">{contract.contractNumber}</p>
                      </div>
                      <Badge variant={contract.status === 'active' ? 'default' : 'secondary'}>
                        {contract.status}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{contract.retainerTier}</p>
                      <p className="text-sm text-gray-600">
                        {contract.activeRequirements} active • {contract.totalPlacements} placed
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="contracts">
          <ContractsList onRefresh={fetchDashboardData} />
        </TabsContent>

        <TabsContent value="requirements">
          <RequirementsList />
        </TabsContent>

        <TabsContent value="analytics">
          <AnalyticsDashboard />
        </TabsContent>

        <TabsContent value="sla">
          <SLADashboard />
        </TabsContent>
      </Tabs>

      {/* Create Contract Modal */}
      {showCreateModal && (
        <CreateContractModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchDashboardData();
          }}
        />
      )}
    </div>
  );
}