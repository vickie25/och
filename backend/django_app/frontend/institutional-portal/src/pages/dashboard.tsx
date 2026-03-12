/**
 * Institutional Portal Dashboard
 * Main dashboard showing seat utilization, student metrics, and analytics
 */
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import {
  ChartBarIcon,
  UserGroupIcon,
  AcademicCapIcon,
  CurrencyDollarIcon,
  ClockIcon,
  TrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';
import toast from 'react-hot-toast';
import apiService, { DashboardAnalytics, Contract } from '../services/api';
import Layout from '../components/Layout';
import MetricCard from '../components/MetricCard';
import LoadingSpinner from '../components/LoadingSpinner';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

interface DashboardProps {}

const Dashboard: React.FC<DashboardProps> = () => {
  const router = useRouter();
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedContract, setSelectedContract] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadContracts();
  }, []);

  useEffect(() => {
    if (selectedContract) {
      loadAnalytics();
    }
  }, [selectedContract]);

  const loadContracts = async () => {
    try {
      const response = await apiService.getContracts();
      setContracts(response.contracts);
      
      // Auto-select first contract
      if (response.contracts.length > 0 && !selectedContract) {
        setSelectedContract(response.contracts[0].id);
      }
    } catch (error) {
      toast.error('Failed to load contracts');
      console.error('Error loading contracts:', error);
    }
  };

  const loadAnalytics = async () => {
    if (!selectedContract) return;
    
    try {
      setLoading(true);
      const data = await apiService.getDashboardAnalytics(selectedContract);
      setAnalytics(data);
    } catch (error) {
      toast.error('Failed to load dashboard analytics');
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalytics();
    setRefreshing(false);
    toast.success('Dashboard refreshed');
  };

  const handleContractChange = (contractId: string) => {
    setSelectedContract(contractId);
  };

  if (loading && !analytics) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </Layout>
    );
  }

  const selectedContractData = contracts.find(c => c.id === selectedContract);

  // Chart configurations
  const seatUtilizationData = {
    labels: analytics?.seat_utilization.pools.map(p => p.name) || [],
    datasets: [
      {
        label: 'Allocated Seats',
        data: analytics?.seat_utilization.pools.map(p => p.allocated) || [],
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
      {
        label: 'Active Seats',
        data: analytics?.seat_utilization.pools.map(p => p.active) || [],
        backgroundColor: 'rgba(34, 197, 94, 0.5)',
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 1,
      },
    ],
  };

  const studentStatusData = {
    labels: ['Active', 'Completed', 'Withdrawn'],
    datasets: [
      {
        data: [
          analytics?.student_metrics.active_students || 0,
          analytics?.student_metrics.completed_students || 0,
          analytics?.student_metrics.withdrawn_students || 0,
        ],
        backgroundColor: [
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2,
      },
    ],
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Institutional Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                Manage your institutional contract and student allocations
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Contract Selector */}
              <select
                value={selectedContract}
                onChange={(e) => handleContractChange(e.target.value)}
                className="rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
              >
                <option value="">Select Contract</option>
                {contracts.map((contract) => (
                  <option key={contract.id} value={contract.id}>
                    {contract.contract_number} - {contract.organization.name}
                  </option>
                ))}
              </select>
              
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
              >
                {refreshing ? (
                  <LoadingSpinner size="sm" className="mr-2" />
                ) : (
                  <ChartBarIcon className="h-4 w-4 mr-2" />
                )}
                Refresh
              </button>
            </div>
          </div>
        </div>

        {analytics && (
          <>
            {/* Contract Info */}
            <div className="bg-white shadow rounded-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Contract Information
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Organization</p>
                  <p className="font-semibold">{analytics.contract_info.organization}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Contract Period</p>
                  <p className="font-semibold">
                    {new Date(analytics.contract_info.start_date).toLocaleDateString()} - {' '}
                    {new Date(analytics.contract_info.end_date).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Licensed Seats</p>
                  <p className="font-semibold">{analytics.contract_info.licensed_seats}</p>
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                title="Seat Utilization"
                value={`${analytics.seat_utilization.utilization_rate.toFixed(1)}%`}
                subtitle={`${analytics.seat_utilization.total_active} of ${analytics.seat_utilization.total_allocated} seats`}
                icon={UserGroupIcon}
                color="primary"
                trend={analytics.seat_utilization.utilization_rate > 75 ? 'up' : 'down'}
              />
              
              <MetricCard
                title="Active Students"
                value={analytics.student_metrics.active_students.toString()}
                subtitle={`${analytics.student_metrics.completion_rate.toFixed(1)}% completion rate`}
                icon={AcademicCapIcon}
                color="success"
                trend="up"
              />
              
              <MetricCard
                title="Monthly Cost"
                value={`$${analytics.contract_info.monthly_cost.toLocaleString()}`}
                subtitle={`$${analytics.roi_metrics.cost_per_student.toFixed(0)} per student`}
                icon={CurrencyDollarIcon}
                color="warning"
              />
              
              <MetricCard
                title="ROI"
                value={`${analytics.roi_metrics.roi_percentage.toFixed(0)}%`}
                subtitle={`${analytics.roi_metrics.certification_rate.toFixed(1)}% certification rate`}
                icon={TrendingUpIcon}
                color="success"
                trend="up"
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Seat Utilization Chart */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Seat Pool Utilization
                </h3>
                <div className="h-64">
                  <Bar
                    data={seatUtilizationData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top' as const,
                        },
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                        },
                      },
                    }}
                  />
                </div>
              </div>

              {/* Student Status Distribution */}
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Student Status Distribution
                </h3>
                <div className="h-64">
                  <Doughnut
                    data={studentStatusData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'bottom' as const,
                        },
                      },
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Track Assignments Overview */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Track Assignments Overview
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-600">
                    {analytics.track_assignments.mandatory_assignments}
                  </div>
                  <div className="text-sm text-gray-500">Total Assignments</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-success-600">
                    {analytics.track_assignments.completed_assignments}
                  </div>
                  <div className="text-sm text-gray-500">Completed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-danger-600">
                    {analytics.track_assignments.overdue_assignments}
                  </div>
                  <div className="text-sm text-gray-500">Overdue</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary-600">
                    {analytics.track_assignments.completion_rate.toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500">Completion Rate</div>
                </div>
              </div>
            </div>

            {/* Seat Pool Details */}
            <div className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Seat Pool Details
                </h3>
                <button
                  onClick={() => router.push('/seat-pools')}
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  Manage Pools →
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Pool Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Allocated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Active
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Available
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Utilization
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {analytics.seat_utilization.pools.map((pool) => (
                      <tr key={pool.name} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {pool.name}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                            {pool.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {pool.allocated}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {pool.active}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {pool.available}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                              <div
                                className={`h-2 rounded-full ${
                                  pool.utilization > 90
                                    ? 'bg-danger-500'
                                    : pool.utilization > 75
                                    ? 'bg-warning-500'
                                    : 'bg-success-500'
                                }`}
                                style={{ width: `${Math.min(pool.utilization, 100)}%` }}
                              />
                            </div>
                            <span className="text-sm text-gray-900">
                              {pool.utilization.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Quick Actions
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => router.push('/students/import')}
                  className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <UserGroupIcon className="h-5 w-5 mr-2" />
                  Import Students
                </button>
                
                <button
                  onClick={() => router.push('/students')}
                  className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <AcademicCapIcon className="h-5 w-5 mr-2" />
                  Manage Students
                </button>
                
                <button
                  onClick={() => router.push('/reports')}
                  className="flex items-center justify-center px-4 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  View Reports
                </button>
              </div>
            </div>

            {/* Alerts */}
            {analytics.track_assignments.overdue_assignments > 0 && (
              <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-warning-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-warning-800">
                      Overdue Assignments
                    </h3>
                    <p className="text-sm text-warning-700 mt-1">
                      {analytics.track_assignments.overdue_assignments} students have overdue track assignments.{' '}
                      <button
                        onClick={() => router.push('/students?filter=overdue')}
                        className="font-medium underline hover:no-underline"
                      >
                        View details
                      </button>
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {!selectedContract && contracts.length === 0 && (
          <div className="text-center py-12">
            <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No contracts found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Contact your OCH representative to set up an institutional contract.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Dashboard;