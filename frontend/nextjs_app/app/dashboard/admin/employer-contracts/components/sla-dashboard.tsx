'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AlertTriangle, Clock, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface SLAData {
  overdueCount: number;
  alerts: Array<{
    id: string;
    type: string;
    message: string;
    severity: string;
    contractNumber: string;
    requirementTitle: string;
    daysSincePosted: number;
  }>;
  complianceByContract: Array<{
    contractId: string;
    contractNumber: string;
    organization: string;
    complianceRate: number;
    slaDays: number;
  }>;
  overallCompliance: number;
}

export function SLADashboard() {
  const [slaData, setSlaData] = useState<SLAData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchSLAData();
  }, []);

  const fetchSLAData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/marketplace/employer-contracts/analytics/sla/');
      const data = await response.json();
      setSlaData(data);
    } catch (error) {
      console.error('Failed to fetch SLA data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSLAData();
    setRefreshing(false);
  };

  const getComplianceColor = (rate: number) => {
    if (rate >= 0.95) return 'text-green-600';
    if (rate >= 0.85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getComplianceIcon = (rate: number) => {
    if (rate >= 0.95) return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (rate >= 0.85) return <Clock className="h-5 w-5 text-yellow-600" />;
    return <XCircle className="h-5 w-5 text-red-600" />;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (loading || !slaData) {
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
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">SLA Monitoring Dashboard</h2>
          <p className="text-gray-600">Track service level agreement compliance and alerts</p>
        </div>
        <Button onClick={handleRefresh} disabled={refreshing} variant="outline">
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overall Compliance</p>
                <p className={`text-2xl font-bold ${getComplianceColor(slaData.overallCompliance)}`}>
                  {formatPercentage(slaData.overallCompliance)}
                </p>
              </div>
              {getComplianceIcon(slaData.overallCompliance)}
            </div>
            <Progress 
              value={slaData.overallCompliance * 100} 
              className="mt-3"
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Overdue Requirements</p>
                <p className="text-2xl font-bold text-red-600">{slaData.overdueCount}</p>
                <p className="text-xs text-gray-600 mt-1">Require immediate attention</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-2xl font-bold text-orange-600">{slaData.alerts.length}</p>
                <p className="text-xs text-gray-600 mt-1">Notifications pending</p>
              </div>
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* SLA Alerts */}
      {slaData.alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 text-orange-600" />
              SLA Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {slaData.alerts.map((alert) => (
                <div key={alert.id} className="flex items-start justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <Badge className={getSeverityColor(alert.severity)}>
                        {alert.severity}
                      </Badge>
                      <span className="text-sm text-gray-600">{alert.contractNumber}</span>
                    </div>
                    <p className="font-medium mb-1">{alert.requirementTitle}</p>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {alert.daysSincePosted} days since posted
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Compliance by Contract */}
      <Card>
        <CardHeader>
          <CardTitle>SLA Compliance by Contract</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {slaData.complianceByContract.map((contract) => (
              <div key={contract.contractId} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-4 mb-2">
                    {getComplianceIcon(contract.complianceRate)}
                    <div>
                      <p className="font-medium">{contract.organization}</p>
                      <p className="text-sm text-gray-600">{contract.contractNumber}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm text-gray-600">Compliance Rate</span>
                        <span className={`text-sm font-medium ${getComplianceColor(contract.complianceRate)}`}>
                          {formatPercentage(contract.complianceRate)}
                        </span>
                      </div>
                      <Progress value={contract.complianceRate * 100} className="h-2" />
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">SLA Target</p>
                      <p className="text-sm font-medium">{contract.slaDays} days</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* SLA Performance Trends */}
      <Card>
        <CardHeader>
          <CardTitle>SLA Performance Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {slaData.complianceByContract.filter(c => c.complianceRate >= 0.95).length}
              </div>
              <p className="text-sm text-gray-600">Excellent Performance</p>
              <p className="text-xs text-gray-500">≥95% compliance</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600 mb-2">
                {slaData.complianceByContract.filter(c => c.complianceRate >= 0.85 && c.complianceRate < 0.95).length}
              </div>
              <p className="text-sm text-gray-600">Needs Improvement</p>
              <p className="text-xs text-gray-500">85-94% compliance</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600 mb-2">
                {slaData.complianceByContract.filter(c => c.complianceRate < 0.85).length}
              </div>
              <p className="text-sm text-gray-600">Critical Issues</p>
              <p className="text-xs text-gray-500">&lt;85% compliance</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}