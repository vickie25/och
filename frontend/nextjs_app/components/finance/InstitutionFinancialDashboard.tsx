import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Building2, 
  FileText, 
  Users, 
  Calendar,
  CheckCircle,
  Clock,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Download
} from 'lucide-react';

interface InstitutionDashboardProps {
  userId: string;
}

interface Organization {
  name: string;
  total_contract_value: number;
}

interface Contract {
  id: string;
  type: string;
  total_value: number;
  start_date: string;
  end_date: string;
  days_until_expiry: number;
}

interface EnrollmentMetrics {
  total_enrollments: number;
  active_enrollments: number;
  completed_enrollments: number;
}

interface Invoice {
  invoice_number: string;
  total: number;
  status: string;
  due_date: string;
  created_at: string;
}

export const InstitutionFinancialDashboard: React.FC<InstitutionDashboardProps> = ({ userId }) => {
  const [dashboardData, setDashboardData] = useState<{
    organization: Organization;
    contracts: Contract[];
    enrollment_metrics: EnrollmentMetrics;
    recent_invoices: Invoice[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/finance/dashboard/institution/', {
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid': return 'text-green-600 bg-green-50';
      case 'sent': return 'text-blue-600 bg-blue-50';
      case 'overdue': return 'text-red-600 bg-red-50';
      case 'draft': return 'text-gray-600 bg-gray-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getContractStatusColor = (daysUntilExpiry: number) => {
    if (daysUntilExpiry < 30) return 'text-red-600 bg-red-50';
    if (daysUntilExpiry < 90) return 'text-orange-600 bg-orange-50';
    return 'text-green-600 bg-green-50';
  };

  const getInvoiceStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'sent':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'overdue':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <FileText className="h-4 w-4 text-gray-600" />;
    }
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

  const { organization, contracts, enrollment_metrics, recent_invoices } = dashboardData;
  const completionRate = enrollment_metrics.total_enrollments > 0 
    ? (enrollment_metrics.completed_enrollments / enrollment_metrics.total_enrollments) * 100 
    : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Institution Dashboard</h1>
        <p className="text-muted-foreground">
          Financial overview for {organization.name}
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Contract Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(organization.total_contract_value)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Contracts</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{contracts.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Enrollments</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{enrollment_metrics.total_enrollments}</div>
            <p className="text-xs text-muted-foreground">
              {enrollment_metrics.active_enrollments} currently active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completion Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completionRate.toFixed(1)}%</div>
            <Progress value={completionRate} className="mt-2 h-2" />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Active Contracts */}
        <Card>
          <CardHeader>
            <CardTitle>Active Contracts</CardTitle>
            <CardDescription>Your current institutional agreements</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {contracts.map((contract) => (
                <div key={contract.id} className="space-y-3 p-4 border rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="font-medium capitalize">{contract.type} Contract</span>
                    <Badge className={getContractStatusColor(contract.days_until_expiry)}>
                      {contract.days_until_expiry < 30 ? 'Expiring Soon' : 
                       contract.days_until_expiry < 90 ? 'Renewal Due' : 'Active'}
                    </Badge>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Contract Value:</span>
                      <span className="font-medium">{formatCurrency(contract.total_value)}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Start Date:</span>
                      <span>{new Date(contract.start_date).toLocaleDateString()}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">End Date:</span>
                      <span>{new Date(contract.end_date).toLocaleDateString()}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Days Until Expiry:</span>
                      <span className={contract.days_until_expiry < 30 ? 'text-red-600 font-medium' : ''}>
                        {contract.days_until_expiry} days
                      </span>
                    </div>
                  </div>
                  
                  {contract.days_until_expiry < 90 && (
                    <Alert>
                      <Calendar className="h-4 w-4" />
                      <AlertDescription>
                        Contract renewal required within {contract.days_until_expiry} days
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Enrollment Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Enrollment Overview</CardTitle>
            <CardDescription>Student enrollment statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div className="grid gap-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Enrollments</span>
                  <span className="text-2xl font-bold">{enrollment_metrics.total_enrollments}</span>
                </div>
                
                <Separator />
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Active Students</span>
                    <span className="font-medium">{enrollment_metrics.active_enrollments}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Completed Programs</span>
                    <span className="font-medium">{enrollment_metrics.completed_enrollments}</span>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Completion Rate</span>
                    <span className="font-medium">{completionRate.toFixed(1)}%</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Progress Overview</span>
                  <span>{completionRate.toFixed(1)}%</span>
                </div>
                <Progress value={completionRate} className="h-3" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Invoices */}
      {recent_invoices.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Invoices</CardTitle>
            <CardDescription>Your latest billing statements</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recent_invoices.map((invoice, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getInvoiceStatusIcon(invoice.status)}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{invoice.invoice_number}</span>
                        <Badge className={getStatusColor(invoice.status)}>
                          {invoice.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>Due: {new Date(invoice.due_date).toLocaleDateString()}</span>
                        <span>Created: {new Date(invoice.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-medium">{formatCurrency(invoice.total)}</div>
                    <Button variant="ghost" size="sm" className="h-6 px-2">
                      <Download className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-4">
            <Button variant="outline" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              View All Contracts
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Manage Enrollments
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Billing History
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Download Reports
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Contract Renewal Alerts */}
      {contracts.some(c => c.days_until_expiry < 90) && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            You have {contracts.filter(c => c.days_until_expiry < 90).length} contract(s) 
            requiring renewal within the next 90 days. Please contact your account manager 
            to discuss renewal terms.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};