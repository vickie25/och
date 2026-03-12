import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { AlertTriangle, Clock, CreditCard } from 'lucide-react';

interface GracePeriodCountdownProps {
  gracePeriodEnd: string;
  billingCycle: 'monthly' | 'annual' | 'quarterly';
  amountDue: number;
  currency?: string;
  onPayNow: () => void;
  onUpdatePaymentMethod: () => void;
}

export const GracePeriodCountdown: React.FC<GracePeriodCountdownProps> = ({
  gracePeriodEnd,
  billingCycle,
  amountDue,
  currency = 'USD',
  onPayNow,
  onUpdatePaymentMethod
}) => {
  const [timeRemaining, setTimeRemaining] = useState<{
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
    totalHours: number;
    percentage: number;
  }>({ days: 0, hours: 0, minutes: 0, seconds: 0, totalHours: 0, percentage: 0 });

  const gracePeriodDays = {
    monthly: 3,
    quarterly: 5,
    annual: 7
  };

  const totalGracePeriodHours = gracePeriodDays[billingCycle] * 24;

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date().getTime();
      const endTime = new Date(gracePeriodEnd).getTime();
      const timeDiff = endTime - now;

      if (timeDiff > 0) {
        const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
        
        const totalHours = Math.floor(timeDiff / (1000 * 60 * 60));
        const percentage = Math.max(0, Math.min(100, ((totalGracePeriodHours - totalHours) / totalGracePeriodHours) * 100));

        setTimeRemaining({ days, hours, minutes, seconds, totalHours, percentage });
      } else {
        setTimeRemaining({ days: 0, hours: 0, minutes: 0, seconds: 0, totalHours: 0, percentage: 100 });
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [gracePeriodEnd, totalGracePeriodHours]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const getUrgencyLevel = () => {
    if (timeRemaining.totalHours <= 24) return 'critical';
    if (timeRemaining.totalHours <= 48) return 'high';
    return 'medium';
  };

  const getProgressColor = () => {
    const urgency = getUrgencyLevel();
    switch (urgency) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      default: return 'bg-yellow-500';
    }
  };

  const getAlertVariant = () => {
    const urgency = getUrgencyLevel();
    return urgency === 'critical' ? 'destructive' : 'default';
  };

  if (timeRemaining.totalHours <= 0) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-800 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Grace Period Expired
          </CardTitle>
          <CardDescription className="text-red-700">
            Your account has been suspended due to non-payment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Your subscription has been suspended. Please pay the outstanding amount to reactivate your account.
            </AlertDescription>
          </Alert>
          <div className="mt-4 space-y-2">
            <Button onClick={onPayNow} className="w-full" size="lg">
              Pay {formatCurrency(amountDue)} to Reactivate
            </Button>
            <Button onClick={onUpdatePaymentMethod} variant="outline" className="w-full">
              Update Payment Method
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-orange-200 bg-orange-50">
      <CardHeader>
        <CardTitle className="text-orange-800 flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Grace Period Active
        </CardTitle>
        <CardDescription className="text-orange-700">
          Payment failed - {gracePeriodDays[billingCycle]} day grace period
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <Alert variant={getAlertVariant()}>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Your payment failed. Please update your payment method or pay manually to avoid service interruption.
          </AlertDescription>
        </Alert>

        {/* Countdown Display */}
        <div className="text-center space-y-2">
          <div className="text-2xl font-bold text-orange-800">
            {timeRemaining.days > 0 && (
              <span>{timeRemaining.days}d </span>
            )}
            <span>{timeRemaining.hours.toString().padStart(2, '0')}:</span>
            <span>{timeRemaining.minutes.toString().padStart(2, '0')}:</span>
            <span>{timeRemaining.seconds.toString().padStart(2, '0')}</span>
          </div>
          <div className="text-sm text-orange-700">
            {timeRemaining.days > 0 ? 'Days' : 'Hours'} remaining until suspension
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-orange-700">
            <span>Grace period progress</span>
            <span>{Math.round(timeRemaining.percentage)}%</span>
          </div>
          <div className="w-full bg-orange-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-1000 ${getProgressColor()}`}
              style={{ width: `${timeRemaining.percentage}%` }}
            />
          </div>
        </div>

        {/* Amount Due */}
        <div className="bg-white rounded-lg p-3 border border-orange-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Amount Due:</span>
            <span className="text-lg font-semibold text-gray-900">
              {formatCurrency(amountDue)}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          <Button 
            onClick={onPayNow} 
            className="w-full" 
            size="lg"
            variant={getUrgencyLevel() === 'critical' ? 'destructive' : 'default'}
          >
            <CreditCard className="h-4 w-4 mr-2" />
            Pay {formatCurrency(amountDue)} Now
          </Button>
          <Button 
            onClick={onUpdatePaymentMethod} 
            variant="outline" 
            className="w-full"
          >
            Update Payment Method
          </Button>
        </div>

        {/* Additional Information */}
        <div className="text-xs text-orange-600 space-y-1">
          <div>• Your account will be suspended if payment is not received before the grace period ends</div>
          <div>• You will lose access to all premium features upon suspension</div>
          <div>• Late fees may apply after the grace period</div>
        </div>
      </CardContent>
    </Card>
  );
};