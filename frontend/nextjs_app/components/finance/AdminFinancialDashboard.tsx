import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Users, 
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart,
  LineChart,
  Calendar,
  Download,
  RefreshCw
} from 'lucide-react';

interface AdminDashboardProps {
  userId: string;
}

interface RevenueMetrics {
  mrr: number;
  arr: number;
  breakdown: {
    subscription_revenue: number;
    cohort_revenue: number;
    institution_revenue: number;
    employer_revenue: number;
    total_revenue: number;
  };
}

interface KPI {
  name: string;
  category: string;
  current_value: number;
  target_value?: number;
  growth_rate: number;
  target_achievement: number;
  unit: string;
}

interface FinancialAlert {
  id: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  created_at: string;
}

interface CashFlow {
  total_revenue: number;
  total_expenses: number;
  net_cash_flow: number;
  confidence_score: number;
}

export const AdminFinancialDashboard: React.FC<AdminDashboardProps> = ({ userId }) => {
  const [dashboardData, setDashboardData] = useState<{
    revenue_metrics: RevenueMetrics;
    kpis: KPI[];
    alerts: FinancialAlert[];
    cash_flow: CashFlow | null;
    last_updated: string;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/finance/dashboard/admin/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshDashboard = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getKPIsByCategory = (kpis: KPI[]) => {
    return kpis.reduce((acc, kpi) => {
      if (!acc[kpi.category]) {
        acc[kpi.category] = [];
      }
      acc[kpi.category].push(kpi);
      return acc;
    }, {} as Record<string, KPI[]>);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load dashboard data</AlertDescription>
      </Alert>
    );
  }

  const { revenue_metrics, kpis, alerts, cash_flow } = dashboardData;
  const kpisByCategory = getKPIsByCategory(kpis);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Financial Dashboard</h1>
          <p className="text-muted-foreground">
            Last updated: {new Date(dashboardData.last_updated).toLocaleString()}
          </p>
        </div>
        <Button onClick={refreshDashboard} disabled={refreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Revenue Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Monthly Recurring Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(revenue_metrics.mrr)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Annual Recurring Revenue</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(revenue_metrics.arr)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue (30d)</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(revenue_metrics.breakdown.total_revenue)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{alerts.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Breakdown (Last 30 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Subscriptions</span>
                <span className="font-medium">
                  {formatCurrency(revenue_metrics.breakdown.subscription_revenue)}
                </span>
              </div>
              <Progress 
                value={(revenue_metrics.breakdown.subscription_revenue / revenue_metrics.breakdown.total_revenue) * 100} 
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Cohorts</span>
                <span className="font-medium">
                  {formatCurrency(revenue_metrics.breakdown.cohort_revenue)}
                </span>
              </div>
              <Progress 
                value={(revenue_metrics.breakdown.cohort_revenue / revenue_metrics.breakdown.total_revenue) * 100} 
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Institutions</span>
                <span className="font-medium">
                  {formatCurrency(revenue_metrics.breakdown.institution_revenue)}
                </span>
              </div>
              <Progress 
                value={(revenue_metrics.breakdown.institution_revenue / revenue_metrics.breakdown.total_revenue) * 100} 
                className="h-2"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Employers</span>
                <span className="font-medium">
                  {formatCurrency(revenue_metrics.breakdown.employer_revenue)}
                </span>
              </div>
              <Progress 
                value={(revenue_metrics.breakdown.employer_revenue / revenue_metrics.breakdown.total_revenue) * 100} 
                className="h-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* KPIs */}
        <Card>
          <CardHeader>
            <CardTitle>Key Performance Indicators</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue={Object.keys(kpisByCategory)[0]} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                {Object.keys(kpisByCategory).slice(0, 3).map((category) => (
                  <TabsTrigger key={category} value={category} className="capitalize">
                    {category}
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {Object.entries(kpisByCategory).map(([category, categoryKpis]) => (
                <TabsContent key={category} value={category} className="space-y-4">
                  {categoryKpis.map((kpi) => (
                    <div key={kpi.name} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{kpi.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-bold">
                            {kpi.unit === 'currency' 
                              ? formatCurrency(kpi.current_value)
                              : kpi.unit === 'percentage'
                              ? formatPercentage(kpi.current_value)
                              : kpi.current_value.toLocaleString()
                            }
                          </span>
                          {kpi.growth_rate !== 0 && (
                            <Badge variant={kpi.growth_rate > 0 ? 'default' : 'destructive'}>
                              {kpi.growth_rate > 0 ? (
                                <TrendingUp className="h-3 w-3 mr-1" />
                              ) : (
                                <TrendingDown className="h-3 w-3 mr-1" />
                              )}
                              {formatPercentage(Math.abs(kpi.growth_rate))}
                            </Badge>
                          )}
                        </div>
                      </div>
                      
                      {kpi.target_value && (
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>Target: {kpi.unit === 'currency' 
                              ? formatCurrency(kpi.target_value)
                              : kpi.target_value.toLocaleString()
                            }</span>
                            <span>{formatPercentage(kpi.target_achievement)} achieved</span>
                          </div>
                          <Progress value={kpi.target_achievement} className="h-1" />
                        </div>
                      )}
                    </div>
                  ))}
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        {/* Cash Flow */}
        {cash_flow && (
          <Card>
            <CardHeader>
              <CardTitle>Cash Flow Projection</CardTitle>
              <CardDescription>Monthly projection with {cash_flow.confidence_score}% confidence</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Revenue</span>
                  <span className="font-medium text-green-600">
                    +{formatCurrency(cash_flow.total_revenue)}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Expenses</span>
                  <span className="font-medium text-red-600">
                    -{formatCurrency(cash_flow.total_expenses)}
                  </span>
                </div>
                
                <div className="border-t pt-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Net Cash Flow</span>
                    <span className={`font-bold ${cash_flow.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {cash_flow.net_cash_flow >= 0 ? '+' : ''}{formatCurrency(cash_flow.net_cash_flow)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Confidence Score</span>
                  <span>{cash_flow.confidence_score}%</span>
                </div>
                <Progress value={cash_flow.confidence_score} className="h-2" />
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Financial Alerts</CardTitle>
            <CardDescription>{alerts.length} alerts require attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="flex items-start gap-3 p-3 border rounded-lg">
                  <div className={`w-2 h-2 rounded-full mt-2 ${getSeverityColor(alert.severity)}`} />
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{alert.title}</span>
                      <Badge variant="outline" className="text-xs">
                        {alert.severity}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{alert.description}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
              
              {alerts.length > 5 && (
                <Button variant="outline" className="w-full">
                  View All {alerts.length} Alerts
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};