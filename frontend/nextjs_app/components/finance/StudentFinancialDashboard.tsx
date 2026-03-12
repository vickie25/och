import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  CreditCard, 
  Wallet, 
  GraduationCap, 
  Calendar,
  CheckCircle,
  Clock,
  AlertTriangle,
  DollarSign,
  History
} from 'lucide-react';

interface StudentDashboardProps {
  userId: string;
}

interface Subscription {
  plan: string;
  status: string;
  current_period_end: string;
  enhanced_access_expires_at?: string;
}

interface WalletData {
  balance: number;
  currency: string;
  last_transaction_at?: string;
  recent_transactions: Array<{
    type: string;
    amount: number;
    description: string;
    created_at: string;
  }>;
}

interface Enrollment {
  cohort_name: string;
  seat_type: string;
  payment_status: string;
  joined_at: string;
}

interface PaymentHistory {
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

export const StudentFinancialDashboard: React.FC<StudentDashboardProps> = ({ userId }) => {
  const [dashboardData, setDashboardData] = useState<{
    subscription: Subscription | null;
    wallet: WalletData | null;
    enrollments: Enrollment[];
    payment_history: PaymentHistory[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/finance/dashboard/student/', {
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

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'text-green-600 bg-green-50';
      case 'trial': return 'text-blue-600 bg-blue-50';
      case 'past_due': return 'text-orange-600 bg-orange-50';
      case 'canceled': return 'text-red-600 bg-red-50';
      case 'completed': return 'text-green-600 bg-green-50';
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getPaymentStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'paid':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
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

  const { subscription, wallet, enrollments, payment_history } = dashboardData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">My Financial Dashboard</h1>
        <p className="text-muted-foreground">
          Manage your subscription, wallet, and payment history
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* Subscription Status */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Subscription</CardTitle>
            <CreditCard className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {subscription ? (
              <div className="space-y-2">
                <div className="text-2xl font-bold">{subscription.plan}</div>
                <Badge className={getStatusColor(subscription.status)}>
                  {subscription.status}
                </Badge>
                {subscription.current_period_end && (
                  <p className="text-xs text-muted-foreground">
                    Renews: {new Date(subscription.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No active subscription</div>
            )}
          </CardContent>
        </Card>

        {/* Wallet Balance */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Wallet Balance</CardTitle>
            <Wallet className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {wallet ? (
              <div className="space-y-2">
                <div className="text-2xl font-bold">
                  {formatCurrency(wallet.balance, wallet.currency)}
                </div>
                {wallet.last_transaction_at && (
                  <p className="text-xs text-muted-foreground">
                    Last activity: {new Date(wallet.last_transaction_at).toLocaleDateString()}
                  </p>
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No wallet found</div>
            )}
          </CardContent>
        </Card>

        {/* Active Enrollments */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Enrollments</CardTitle>
            <GraduationCap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{enrollments.length}</div>
            <p className="text-xs text-muted-foreground">
              {enrollments.filter(e => e.payment_status === 'paid').length} paid enrollments
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Wallet Transactions */}
        {wallet && wallet.recent_transactions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Wallet Activity</CardTitle>
              <CardDescription>Your latest wallet transactions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {wallet.recent_transactions.map((transaction, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">{transaction.description}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(transaction.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className={`text-sm font-medium ${
                      transaction.type === 'credit' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {transaction.type === 'credit' ? '+' : '-'}
                      {formatCurrency(transaction.amount, wallet.currency)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Cohort Enrollments */}
        {enrollments.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Cohort Enrollments</CardTitle>
              <CardDescription>Your active cohort participations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {enrollments.map((enrollment, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{enrollment.cohort_name}</span>
                      <Badge className={getStatusColor(enrollment.payment_status)}>
                        {enrollment.payment_status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span>Seat: {enrollment.seat_type}</span>
                      <span>Joined: {new Date(enrollment.joined_at).toLocaleDateString()}</span>
                    </div>
                    {index < enrollments.length - 1 && <Separator />}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Payment History */}
      {payment_history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Payment History
            </CardTitle>
            <CardDescription>Your recent payment transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {payment_history.slice(0, 10).map((payment, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getPaymentStatusIcon(payment.status)}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {formatCurrency(payment.amount, payment.currency)}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {payment.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {new Date(payment.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
              
              {payment_history.length > 10 && (
                <Button variant="outline" className="w-full">
                  View All Payment History
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Enhanced Access Info */}
      {subscription?.enhanced_access_expires_at && (
        <Card>
          <CardHeader>
            <CardTitle>Enhanced Access</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span className="text-sm">
                Enhanced access expires on {new Date(subscription.enhanced_access_expires_at).toLocaleDateString()}
              </span>
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
          <div className="grid gap-2 md:grid-cols-3">
            <Button variant="outline" className="flex items-center gap-2">
              <CreditCard className="h-4 w-4" />
              Manage Subscription
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Wallet className="h-4 w-4" />
              Add Credits
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <History className="h-4 w-4" />
              Download Receipts
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};