'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Plus, Building2, Users, DollarSign, TrendingUp, AlertTriangle, GraduationCap, Calendar } from 'lucide-react';
import { ContractsList } from './components/contracts-list';
import { StudentManagement } from './components/student-management';
import { BillingAnalytics } from './components/billing-analytics';
import { CreateContractModal } from './components/create-contract-modal';
import { BulkImportModal } from './components/bulk-import-modal';

interface DashboardStats {
  totalContracts: number;
  activeContracts: number;
  totalLicensedSeats: number;
  activeStudents: number;
  seatUtilization: number;
  monthlyRecurringRevenue: number;
  annualRecurringRevenue: number;
  totalOverdue: number;
  expiringContracts: number;
}

interface RecentContract {
  id: string;
  contractNumber: string;
  organizationName: string;
  status: string;
  studentSeatCount: number;
  activeStudents: number;
  monthlyAmount: number;
  daysUntilExpiry: number;
}

export default function InstitutionalBillingDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentContracts, setRecentContracts] = useState<RecentContract[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showBulkImportModal, setShowBulkImportModal] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch analytics
      const analyticsResponse = await fetch('/api/v1/institutional/analytics/');
      const analyticsData = await analyticsResponse.json();
      
      // Fetch recent contracts
      const contractsResponse = await fetch('/api/v1/institutional/contracts/?page_size=5');
      const contractsData = await contractsResponse.json();
      
      setStats({
        totalContracts: analyticsData.contracts.total_contracts,
        activeContracts: analyticsData.contracts.active_contracts,
        totalLicensedSeats: analyticsData.students.total_licensed_seats,
        activeStudents: analyticsData.students.active_students,
        seatUtilization: analyticsData.students.seat_utilization,
        monthlyRecurringRevenue: analyticsData.revenue.monthly_recurring_revenue,
        annualRecurringRevenue: analyticsData.revenue.annual_recurring_revenue,
        totalOverdue: analyticsData.revenue.total_overdue,
        expiringContracts: analyticsData.contracts.expiring_soon
      });
      
      setRecentContracts(contractsData.contracts || []);
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
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Institutional Billing</h1>
          <p className="text-gray-600 mt-2">Manage educational institution contracts and student licensing</p>
        </div>
        <div className="flex space-x-3">
          <Button 
            onClick={() => setShowBulkImportModal(true)} 
            variant="outline"
            className="flex items-center gap-2"
          >
            <Users className="h-4 w-4" />
            Bulk Import
          </Button>
          <Button onClick={() => setShowCreateModal(true)} className="flex items-center gap-2">
            <Plus className="h-4 w-4" />
            New Contract
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Contracts</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.activeContracts}</p>
                  <p className="text-xs text-gray-500">of {stats.totalContracts} total</p>
                </div>
                <Building2 className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Licensed Seats</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalLicensedSeats.toLocaleString()}</p>
                  <p className="text-xs text-gray-500">{stats.activeStudents} active</p>
                </div>
                <GraduationCap className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Seat Utilization</p>
                  <p className="text-2xl font-bold text-gray-900">{formatPercentage(stats.seatUtilization)}</p>
                  <p className="text-xs text-gray-500">{stats.totalLicensedSeats - stats.activeStudents} available</p>
                </div>
                <Users className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Monthly Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.monthlyRecurringRevenue)}</p>
                  <p className="text-xs text-gray-500">MRR</p>
                </div>
                <DollarSign className="h-8 w-8 text-emerald-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Annual Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.annualRecurringRevenue)}</p>
                  <p className="text-xs text-gray-500">ARR</p>
                </div>
                <TrendingUp className="h-8 w-8 text-indigo-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Expiring Soon</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.expiringContracts}</p>
                  <p className="text-xs text-gray-500">within 60 days</p>
                </div>
                <Calendar className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Alert for Overdue Invoices */}
      {stats && stats.totalOverdue > 0 && (
        <Card className="mb-6 border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="font-medium text-red-800">
                    {formatCurrency(stats.totalOverdue)} in overdue invoices
                  </p>
                  <p className="text-sm text-red-600">Immediate attention required for payment collection</p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={() => setActiveTab('billing')}>
                View Invoices
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="contracts">Contracts</TabsTrigger>
          <TabsTrigger value="students">Students</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Recent Contracts */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Contract Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentContracts.map((contract) => (
                  <div key={contract.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div>
                        <p className="font-medium">{contract.organizationName}</p>
                        <p className="text-sm text-gray-600">{contract.contractNumber}</p>
                      </div>
                      <Badge variant={contract.status === 'active' ? 'default' : 'secondary'}>
                        {contract.status}
                      </Badge>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{formatCurrency(contract.monthlyAmount)}/mo</p>
                      <p className="text-sm text-gray-600">
                        {contract.activeStudents}/{contract.studentSeatCount} seats
                      </p>
                      {contract.daysUntilExpiry <= 60 && (
                        <p className="text-xs text-orange-600">
                          Expires in {contract.daysUntilExpiry} days
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button
                  variant="outline"
                  className="flex items-center justify-center p-6 h-auto"
                  onClick={() => setShowCreateModal(true)}
                >
                  <div className="text-center">
                    <Plus className="h-8 w-8 mx-auto mb-2" />
                    <p className="font-medium">Create Contract</p>
                    <p className="text-sm text-gray-600">New institutional agreement</p>
                  </div>
                </Button>
                
                <Button
                  variant="outline"
                  className="flex items-center justify-center p-6 h-auto"
                  onClick={() => setShowBulkImportModal(true)}
                >
                  <div className="text-center">
                    <Users className="h-8 w-8 mx-auto mb-2" />
                    <p className="font-medium">Import Students</p>
                    <p className="text-sm text-gray-600">Bulk CSV upload</p>
                  </div>
                </Button>
                
                <Button
                  variant="outline"
                  className="flex items-center justify-center p-6 h-auto"
                  onClick={() => setActiveTab('analytics')}
                >
                  <div className="text-center">
                    <TrendingUp className="h-8 w-8 mx-auto mb-2" />
                    <p className="font-medium">View Analytics</p>
                    <p className="text-sm text-gray-600">Revenue & utilization</p>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="contracts">
          <ContractsList onRefresh={fetchDashboardData} />
        </TabsContent>

        <TabsContent value="students">
          <StudentManagement />
        </TabsContent>

        <TabsContent value="billing">
          <BillingAnalytics showInvoices={true} />
        </TabsContent>

        <TabsContent value="analytics">
          <BillingAnalytics showInvoices={false} />
        </TabsContent>
      </Tabs>

      {/* Modals */}
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

      {showBulkImportModal && (
        <BulkImportModal
          isOpen={showBulkImportModal}
          onClose={() => setShowBulkImportModal(false)}
          onSuccess={() => {
            setShowBulkImportModal(false);
            fetchDashboardData();
          }}
        />
      )}
    </div>
  );
}