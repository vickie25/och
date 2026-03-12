import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  CreditCard, 
  Calendar, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  GraduationCap,
  Percent,
  Gift
} from 'lucide-react';

import { PromoCodeInput } from './PromoCodeInput';
import { TrialPeriodManager } from './TrialPeriodManager';
import { AcademicDiscountModal } from './AcademicDiscountModal';

interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  currency: string;
  billing_cycle: 'monthly' | 'annual';
  features: string[];
  trial_days: number;
  requires_credit_card: boolean;
}

interface Subscription {
  id: string;
  plan: SubscriptionPlan;
  status: 'trial' | 'active' | 'past_due' | 'suspended' | 'canceled' | 'expired';
  current_period_start: string;
  current_period_end: string;
  trial_start?: string;
  trial_end?: string;
  grace_period_end?: string;
  next_billing_date: string;
  amount_due: number;
  dunning_status?: 'none' | 'soft_decline' | 'hard_decline' | 'final_notice';
}

interface EnhancedSubscriptionClientProps {
  userId: string;
  onSubscriptionChange?: (subscription: Subscription) => void;
}

export const EnhancedSubscriptionClient: React.FC<EnhancedSubscriptionClientProps> = ({
  userId,
  onSubscriptionChange
}) => {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [availablePlans, setAvailablePlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [academicDiscount, setAcademicDiscount] = useState<any>(null);
  const [appliedPromoCode, setAppliedPromoCode] = useState<any>(null);
  const [showAcademicModal, setShowAcademicModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    fetchSubscriptionData();
    fetchAvailablePlans();
    checkAcademicDiscount();
  }, [userId]);

  const fetchSubscriptionData = async () => {
    try {
      const response = await fetch(`/api/billing/subscription/${userId}/`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSubscription(data);
      }
    } catch (error) {
      console.error('Failed to fetch subscription:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailablePlans = async () => {
    try {
      const response = await fetch('/api/billing/plans/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setAvailablePlans(data);
      }
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    }
  };

  const checkAcademicDiscount = async () => {
    try {
      const response = await fetch(`/api/billing/academic-discount/${userId}/`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.eligible) {
          setAcademicDiscount(data);
        }
      }
    } catch (error) {
      console.error('Failed to check academic discount:', error);
    }
  };

  const calculatePrice = (basePrice: number) => {
    let finalPrice = basePrice;
    
    // Apply academic discount first
    if (academicDiscount?.verified) {
      finalPrice = finalPrice * (1 - academicDiscount.discount_rate / 100);
    }
    
    // Apply promo code discount
    if (appliedPromoCode) {
      if (appliedPromoCode.discountType === 'percentage') {
        finalPrice = finalPrice * (1 - appliedPromoCode.discountValue / 100);
      } else {
        finalPrice = Math.max(0, finalPrice - appliedPromoCode.discountValue);
      }
    }
    
    return finalPrice;
  };

  const handlePlanChange = async (planId: string) => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/billing/change-plan/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: userId,
          new_plan_id: planId,
          promo_code: appliedPromoCode?.code,
          academic_discount: academicDiscount?.verified
        })
      });

      if (response.ok) {
        const updatedSubscription = await response.json();
        setSubscription(updatedSubscription);
        onSubscriptionChange?.(updatedSubscription);
      }
    } catch (error) {
      console.error('Failed to change plan:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleTrialConversion = async () => {
    if (!subscription) return;
    
    setIsProcessing(true);
    try {
      const response = await fetch('/api/billing/convert-trial/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          subscription_id: subscription.id,
          promo_code: appliedPromoCode?.code,
          academic_discount: academicDiscount?.verified
        })
      });

      if (response.ok) {
        const updatedSubscription = await response.json();
        setSubscription(updatedSubscription);
        onSubscriptionChange?.(updatedSubscription);
      }
    } catch (error) {
      console.error('Failed to convert trial:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      trial: { variant: 'secondary' as const, icon: Clock, label: 'Trial' },
      active: { variant: 'default' as const, icon: CheckCircle, label: 'Active' },
      past_due: { variant: 'destructive' as const, icon: AlertTriangle, label: 'Past Due' },
      suspended: { variant: 'destructive' as const, icon: AlertTriangle, label: 'Suspended' },
      canceled: { variant: 'outline' as const, icon: AlertTriangle, label: 'Canceled' },
      expired: { variant: 'destructive' as const, icon: AlertTriangle, label: 'Expired' }
    };

    const config = statusConfig[status as keyof typeof statusConfig];
    if (!config) return null;

    const Icon = config.icon;
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  if (loading) {
    return <div className="flex justify-center p-8">Loading subscription data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Current Subscription Status */}
      {subscription && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{subscription.plan.name}</CardTitle>
                <CardDescription>
                  ${subscription.plan.price}/{subscription.plan.billing_cycle}
                </CardDescription>
              </div>
              {getStatusBadge(subscription.status)}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Trial Period Manager */}
            {subscription.status === 'trial' && (
              <TrialPeriodManager
                planType={subscription.plan.name.toLowerCase() as 'basic' | 'pro' | 'premium'}
                trialStatus="active"
                trialStartDate={subscription.trial_start}
                trialEndDate={subscription.trial_end}
                gracePeriodEndDate={subscription.grace_period_end}
                onConvertTrial={handleTrialConversion}
                requiresCreditCard={subscription.plan.requires_credit_card}
              />
            )}

            {/* Dunning Status Alert */}
            {subscription.dunning_status && subscription.dunning_status !== 'none' && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Payment issue detected. Please update your payment method to avoid service interruption.
                </AlertDescription>
              </Alert>
            )}

            {/* Billing Information */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Current Period:</span>
                <div>{new Date(subscription.current_period_start).toLocaleDateString()} - {new Date(subscription.current_period_end).toLocaleDateString()}</div>
              </div>
              <div>
                <span className="text-muted-foreground">Next Billing:</span>
                <div>{new Date(subscription.next_billing_date).toLocaleDateString()}</div>
              </div>
            </div>

            {subscription.amount_due > 0 && (
              <Alert>
                <CreditCard className="h-4 w-4" />
                <AlertDescription>
                  Amount due: ${subscription.amount_due.toFixed(2)}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Academic Discount Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5" />
            Academic Discount
          </CardTitle>
          <CardDescription>
            Students and educators get 30% off all plans
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {academicDiscount?.verified ? (
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription>
                Academic discount verified! You're saving 30% on your subscription.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Verify your academic status to receive a 30% discount on all plans.
              </p>
              <Button 
                onClick={() => setShowAcademicModal(true)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <Percent className="h-4 w-4" />
                Verify Academic Status
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Promotional Code Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gift className="h-5 w-5" />
            Promotional Code
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <PromoCodeInput
            onCodeApplied={setAppliedPromoCode}
            onCodeRemoved={() => setAppliedPromoCode(null)}
            appliedCode={appliedPromoCode?.code}
            planId={subscription?.plan.id}
          />
        </CardContent>
      </Card>

      {/* Available Plans */}
      <Card>
        <CardHeader>
          <CardTitle>Available Plans</CardTitle>
          <CardDescription>
            Choose the plan that best fits your needs
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            {availablePlans.map((plan) => {
              const originalPrice = plan.price;
              const finalPrice = calculatePrice(originalPrice);
              const hasDiscount = finalPrice < originalPrice;
              
              return (
                <Card key={plan.id} className={subscription?.plan.id === plan.id ? 'ring-2 ring-primary' : ''}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg">{plan.name}</CardTitle>
                    <div className="space-y-1">
                      {hasDiscount && (
                        <div className="text-sm text-muted-foreground line-through">
                          ${originalPrice.toFixed(2)}/{plan.billing_cycle}
                        </div>
                      )}
                      <div className="text-2xl font-bold">
                        ${finalPrice.toFixed(2)}
                        <span className="text-sm font-normal text-muted-foreground">
                          /{plan.billing_cycle}
                        </span>
                      </div>
                      {hasDiscount && (
                        <Badge variant="secondary" className="text-xs">
                          Save ${(originalPrice - finalPrice).toFixed(2)}
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  
                  <CardContent className="space-y-4">
                    <ul className="space-y-2 text-sm">
                      {plan.features.map((feature, index) => (
                        <li key={index} className="flex items-center gap-2">
                          <CheckCircle className="h-4 w-4 text-green-500" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    
                    {plan.trial_days > 0 && (
                      <div className="text-xs text-muted-foreground">
                        {plan.trial_days}-day free trial
                        {plan.requires_credit_card && ' (credit card required)'}
                      </div>
                    )}
                    
                    <Button
                      onClick={() => handlePlanChange(plan.id)}
                      disabled={subscription?.plan.id === plan.id || isProcessing}
                      className="w-full"
                      variant={subscription?.plan.id === plan.id ? 'outline' : 'default'}
                    >
                      {subscription?.plan.id === plan.id ? 'Current Plan' : 'Select Plan'}
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Academic Discount Modal */}
      <AcademicDiscountModal
        isOpen={showAcademicModal}
        onClose={() => setShowAcademicModal(false)}
        onVerified={(discount) => {
          setAcademicDiscount(discount);
          setShowAcademicModal(false);
        }}
        userId={userId}
      />
    </div>
  );
};