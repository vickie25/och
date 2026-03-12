'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TrendingUp, TrendingDown, Target, Clock, DollarSign, Users } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface ContractPerformanceData {
  contractId: string;
  contractNumber: string;
  organization: string;
  tier: string;
  metrics: {
    totalRequirements: number;
    activeRequirements: number;
    totalPresentations: number;
    totalPlacements: number;
    placementRate: number;
    avgTimeToShortlist: number;
    avgTimeToPlacement: number;
    totalRevenue: number;
    slaComplianceRate: number;
    replacementRate: number;
  };
  monthlyTrends: Array<{
    month: string;
    placements: number;
    revenue: number;
    complianceRate: number;
  }>;
  renewalProbability: number;
  riskFactors: string[];
}

export function ContractPerformance() {
  const [performanceData, setPerformanceData] = useState<ContractPerformanceData[]>([]);
  const [selectedContract, setSelectedContract] = useState<string>('all');
  const [timeRange, setTimeRange] = useState('6months');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPerformanceData();
  }, [selectedContract, timeRange]);

  const fetchPerformanceData = async () => {
    try {
      setLoading(true);
      
      // Fetch all active contracts
      const contractsResponse = await fetch('/api/marketplace/employer-contracts/contracts/?status=active');
      const contractsData = await contractsResponse.json();
      
      // Fetch performance data for each contract
      const performancePromises = contractsData.results.map(async (contract: any) => {
        const perfResponse = await fetch(`/api/marketplace/employer-contracts/contracts/${contract.id}/performance/`);
        const perfData = await perfResponse.json();
        
        return {
          contractId: contract.id,
          contractNumber: contract.contractNumber,
          organization: contract.organization.name,
          tier: contract.retainerTier.name,
          metrics: perfData.performance_metrics,
          monthlyTrends: perfData.monthly_trends || [],
          renewalProbability: perfData.renewal_pricing?.renewal_probability || 0.5,
          riskFactors: perfData.risk_factors || []
        };
      });
      
      const allPerformanceData = await Promise.all(performancePromises);
      setPerformanceData(allPerformanceData);
    } catch (error) {
      console.error('Failed to fetch performance data:', error);
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
    return `${(value * 100).toFixed(1)}%`;
  };

  const getRiskColor = (probability: number) => {
    if (probability > 0.8) return 'text-green-600';
    if (probability > 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPerformanceIcon = (rate: number, threshold: number = 0.8) => {
    if (rate >= threshold) return <TrendingUp className="h-4 w-4 text-green-600" />;
    return <TrendingDown className="h-4 w-4 text-red-600" />;
  };

  const selectedData = selectedContract === 'all' 
    ? performanceData 
    : performanceData.filter(d => d.contractId === selectedContract);

  if (loading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Contract Performance Analysis</h2>
        <div className="flex space-x-4">
          <Select value={selectedContract} onValueChange={setSelectedContract}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select contract" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Contracts</SelectItem>
              {performanceData.map((contract) => (
                <SelectItem key={contract.contractId} value={contract.contractId}>
                  {contract.organization} - {contract.contractNumber}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="3months">3 Months</SelectItem>
              <SelectItem value="6months">6 Months</SelectItem>
              <SelectItem value="12months">12 Months</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Performance Overview */}
      {selectedData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                  <p className="text-2xl font-bold">
                    {formatCurrency(selectedData.reduce((sum, d) => sum + d.metrics.totalRevenue, 0))}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Placement Rate</p>
                  <p className="text-2xl font-bold">
                    {formatPercentage(selectedData.reduce((sum, d) => sum + d.metrics.placementRate, 0) / selectedData.length)}
                  </p>
                </div>
                <Target className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Placements</p>
                  <p className="text-2xl font-bold">
                    {selectedData.reduce((sum, d) => sum + d.metrics.totalPlacements, 0)}
                  </p>
                </div>
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg SLA Compliance</p>
                  <p className="text-2xl font-bold">
                    {formatPercentage(selectedData.reduce((sum, d) => sum + d.metrics.slaComplianceRate, 0) / selectedData.length)}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Individual Contract Performance */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {selectedData.map((contract) => (
          <Card key={contract.contractId}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{contract.organization}</CardTitle>
                  <p className="text-sm text-gray-600">{contract.contractNumber} • {contract.tier}</p>
                </div>
                <Badge className={getRiskColor(contract.renewalProbability)}>
                  {formatPercentage(contract.renewalProbability)} renewal probability
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Placement Rate</span>
                    <div className="flex items-center space-x-1">
                      {getPerformanceIcon(contract.metrics.placementRate)}
                      <span className="font-medium">{formatPercentage(contract.metrics.placementRate)}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">SLA Compliance</span>
                    <div className="flex items-center space-x-1">
                      {getPerformanceIcon(contract.metrics.slaComplianceRate, 0.9)}
                      <span className="font-medium">{formatPercentage(contract.metrics.slaComplianceRate)}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Total Revenue</span>
                    <span className="font-medium">{formatCurrency(contract.metrics.totalRevenue)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Avg Time to Place</span>
                    <span className="font-medium">{contract.metrics.avgTimeToPlacement.toFixed(1)} days</span>
                  </div>
                </div>

                {/* Risk Factors */}
                {contract.riskFactors.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Risk Factors:</p>
                    <div className="flex flex-wrap gap-1">
                      {contract.riskFactors.map((risk, index) => (
                        <Badge key={index} variant="outline" className="text-xs">
                          {risk}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Monthly Trend Chart */}
                {contract.monthlyTrends.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">Monthly Performance</p>
                    <ResponsiveContainer width="100%" height={150}>
                      <LineChart data={contract.monthlyTrends}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="placements" stroke="#8884d8" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Comparative Analysis */}
      {selectedContract === 'all' && performanceData.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="organization" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="metrics.placementRate" fill="#8884d8" name="Placement Rate" />
                <Bar dataKey="metrics.slaComplianceRate" fill="#82ca9d" name="SLA Compliance" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  );
}