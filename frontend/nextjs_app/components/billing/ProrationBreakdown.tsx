import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Calculator, TrendingUp, TrendingDown, Calendar } from 'lucide-react';

interface ProrationBreakdownProps {
  currentPlan: {
    name: string;
    price: number;
    billingCycle: string;
  };
  newPlan: {
    name: string;
    price: number;
    billingCycle: string;
  };
  currentPeriodStart: string;
  currentPeriodEnd: string;
  prorationCredit: number;
  newPlanCost: number;
  immediateCharge: number;
  nextBillingDate: string;
  currency?: string;
  academicDiscount?: number;
  promoDiscount?: number;
}

export const ProrationBreakdown: React.FC<ProrationBreakdownProps> = ({
  currentPlan,
  newPlan,
  currentPeriodStart,
  currentPeriodEnd,
  prorationCredit,
  newPlanCost,
  immediateCharge,
  nextBillingDate,
  currency = 'USD',
  academicDiscount = 0,
  promoDiscount = 0
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateDaysRemaining = () => {
    const now = new Date();
    const periodEnd = new Date(currentPeriodEnd);
    const totalDays = Math.ceil((periodEnd.getTime() - new Date(currentPeriodStart).getTime()) / (1000 * 60 * 60 * 24));
    const remainingDays = Math.ceil((periodEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return { totalDays, remainingDays };
  };

  const { totalDays, remainingDays } = calculateDaysRemaining();
  const usagePercentage = Math.max(0, ((totalDays - remainingDays) / totalDays) * 100);

  const isUpgrade = newPlan.price > currentPlan.price;
  const totalDiscounts = academicDiscount + promoDiscount;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Proration Breakdown
        </CardTitle>
        <CardDescription>
          Detailed calculation for your plan change
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Plan Change Summary */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-3">
            {isUpgrade ? (
              <TrendingUp className="h-5 w-5 text-green-600" />
            ) : (
              <TrendingDown className="h-5 w-5 text-blue-600" />
            )}
            <div>
              <div className="font-medium">
                {currentPlan.name} → {newPlan.name}
              </div>
              <div className="text-sm text-gray-600">
                {formatCurrency(currentPlan.price)} → {formatCurrency(newPlan.price)} per {newPlan.billingCycle}
              </div>
            </div>
          </div>
          <Badge variant={isUpgrade ? 'default' : 'secondary'}>
            {isUpgrade ? 'Upgrade' : 'Downgrade'}
          </Badge>
        </div>

        {/* Current Period Usage */}
        <div className="space-y-3">
          <h4 className="font-medium flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Current Billing Period
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Period Start:</span>
              <div className="font-medium">{formatDate(currentPeriodStart)}</div>
            </div>
            <div>
              <span className="text-gray-600">Period End:</span>
              <div className="font-medium">{formatDate(currentPeriodEnd)}</div>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Usage Progress</span>
              <span>{Math.round(usagePercentage)}% used</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${usagePercentage}%` }}
              />
            </div>
            <div className="text-xs text-gray-600">
              {remainingDays} of {totalDays} days remaining
            </div>
          </div>
        </div>

        <Separator />

        {/* Proration Calculation */}
        <div className="space-y-3">
          <h4 className="font-medium">Proration Calculation</h4>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Current plan unused portion:</span>
              <span className="text-green-600">+{formatCurrency(prorationCredit)}</span>
            </div>
            
            <div className="flex justify-between">
              <span>New plan cost (remaining period):</span>
              <span className="text-red-600">-{formatCurrency(newPlanCost)}</span>
            </div>
            
            {totalDiscounts > 0 && (
              <>
                {academicDiscount > 0 && (
                  <div className="flex justify-between">
                    <span>Academic discount (30%):</span>
                    <span className="text-green-600">-{formatCurrency(academicDiscount)}</span>
                  </div>
                )}
                
                {promoDiscount > 0 && (
                  <div className="flex justify-between">
                    <span>Promotional discount:</span>
                    <span className="text-green-600">-{formatCurrency(promoDiscount)}</span>
                  </div>
                )}
              </>
            )}
            
            <Separator />
            
            <div className="flex justify-between font-medium">
              <span>Immediate charge:</span>
              <span className={immediateCharge >= 0 ? 'text-red-600' : 'text-green-600'}>
                {immediateCharge >= 0 ? '-' : '+'}{formatCurrency(Math.abs(immediateCharge))}
              </span>
            </div>
          </div>
        </div>

        <Separator />

        {/* Next Billing Information */}
        <div className="space-y-3">
          <h4 className="font-medium">Next Billing</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Next billing date:</span>
              <div className="font-medium">{formatDate(nextBillingDate)}</div>
            </div>
            <div>
              <span className="text-gray-600">Next charge:</span>
              <div className="font-medium">{formatCurrency(newPlan.price - totalDiscounts)}</div>
            </div>
          </div>
        </div>

        {/* Summary Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-blue-900">
                {immediateCharge >= 0 ? 'Amount to charge now:' : 'Credit applied:'}
              </div>
              <div className="text-sm text-blue-700">
                Effective immediately upon confirmation
              </div>
            </div>
            <div className="text-xl font-bold text-blue-900">
              {immediateCharge >= 0 ? '' : '+'}{formatCurrency(Math.abs(immediateCharge))}
            </div>
          </div>
        </div>

        {/* Additional Information */}
        <div className="text-xs text-gray-600 space-y-1">
          <div>• Proration is calculated based on the exact time remaining in your current billing period</div>
          <div>• Your new plan features will be available immediately after confirmation</div>
          <div>• The next full billing cycle will begin on {formatDate(nextBillingDate)}</div>
          {totalDiscounts > 0 && (
            <div>• Applied discounts will continue on your new plan</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};