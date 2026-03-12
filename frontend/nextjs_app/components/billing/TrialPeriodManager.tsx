import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Clock, CreditCard, CheckCircle, AlertTriangle } from 'lucide-react';

interface TrialPeriodManagerProps {
  planType: 'basic' | 'pro' | 'premium';
  trialStatus: 'active' | 'expired' | 'converted' | 'none';
  trialStartDate?: string;
  trialEndDate?: string;
  gracePeriodEndDate?: string;
  onConvertTrial: () => void;
  onExtendTrial?: () => void;
  requiresCreditCard?: boolean;
}

const TRIAL_PERIODS = {
  basic: { days: 7, requiresCard: false, description: '7-day free trial' },
  pro: { days: 14, requiresCard: false, description: '14-day free trial' },
  premium: { days: 7, requiresCard: true, description: '7-day trial (credit card required)' }
};

const GRACE_PERIODS = {
  monthly: 3,
  annual: 7
};

export const TrialPeriodManager: React.FC<TrialPeriodManagerProps> = ({
  planType,
  trialStatus,
  trialStartDate,
  trialEndDate,
  gracePeriodEndDate,
  onConvertTrial,
  onExtendTrial,
  requiresCreditCard = false
}) => {
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  const [isInGracePeriod, setIsInGracePeriod] = useState(false);

  const trialConfig = TRIAL_PERIODS[planType];

  useEffect(() => {
    if (trialStatus === 'active' && trialEndDate) {
      const updateTimer = () => {
        const now = new Date();
        const endDate = new Date(trialEndDate);
        const graceEnd = gracePeriodEndDate ? new Date(gracePeriodEndDate) : null;
        
        if (now > endDate && graceEnd && now <= graceEnd) {
          setIsInGracePeriod(true);
          const timeDiff = graceEnd.getTime() - now.getTime();
          const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
          const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          setTimeRemaining(`${days}d ${hours}h grace period remaining`);
        } else if (now <= endDate) {
          setIsInGracePeriod(false);
          const timeDiff = endDate.getTime() - now.getTime();
          const days = Math.floor(timeDiff / (1000 * 60 * 60 * 24));
          const hours = Math.floor((timeDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          setTimeRemaining(`${days}d ${hours}h remaining`);
        } else {
          setTimeRemaining('Trial expired');
        }
      };

      updateTimer();
      const interval = setInterval(updateTimer, 60000); // Update every minute
      return () => clearInterval(interval);
    }
  }, [trialStatus, trialEndDate, gracePeriodEndDate]);

  const getTrialStatusBadge = () => {
    switch (trialStatus) {
      case 'active':
        return isInGracePeriod ? (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            Grace Period
          </Badge>
        ) : (
          <Badge variant="secondary" className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Trial Active
          </Badge>
        );
      case 'expired':
        return (
          <Badge variant="destructive">
            Trial Expired
          </Badge>
        );
      case 'converted':
        return (
          <Badge variant="default" className="flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            Converted
          </Badge>
        );
      default:
        return null;
    }
  };

  const getTrialMessage = () => {
    if (trialStatus === 'active') {
      if (isInGracePeriod) {
        return {
          type: 'warning' as const,
          message: 'Your trial has expired but you have a grace period to convert to a paid plan.',
          action: 'Convert Now'
        };
      }
      return {
        type: 'info' as const,
        message: `You're currently on a ${trialConfig.description}. Convert anytime to continue after trial ends.`,
        action: 'Convert to Paid Plan'
      };
    }
    
    if (trialStatus === 'expired') {
      return {
        type: 'error' as const,
        message: 'Your trial has expired. Please upgrade to continue using premium features.',
        action: 'Upgrade Now'
      };
    }
    
    return null;
  };

  const trialMessage = getTrialMessage();

  if (trialStatus === 'none' || trialStatus === 'converted') {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Trial Status</CardTitle>
            <CardDescription>
              {planType.charAt(0).toUpperCase() + planType.slice(1)} Plan Trial
            </CardDescription>
          </div>
          {getTrialStatusBadge()}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {trialStatus === 'active' && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{timeRemaining}</span>
          </div>
        )}

        {trialMessage && (
          <Alert variant={trialMessage.type === 'warning' ? 'destructive' : 'default'}>
            {trialMessage.type === 'warning' && <AlertTriangle className="h-4 w-4" />}
            {trialMessage.type === 'info' && <Clock className="h-4 w-4" />}
            <AlertDescription>{trialMessage.message}</AlertDescription>
          </Alert>
        )}

        {requiresCreditCard && trialStatus === 'active' && (
          <Alert>
            <CreditCard className="h-4 w-4" />
            <AlertDescription>
              Credit card required for this trial. You won't be charged until the trial ends.
            </AlertDescription>
          </Alert>
        )}

        <div className="flex gap-2">
          <Button 
            onClick={onConvertTrial}
            variant={isInGracePeriod ? "destructive" : "default"}
            className="flex-1"
          >
            {trialMessage?.action || 'Convert Trial'}
          </Button>
          
          {onExtendTrial && trialStatus === 'active' && !isInGracePeriod && (
            <Button 
              onClick={onExtendTrial}
              variant="outline"
            >
              Extend Trial
            </Button>
          )}
        </div>

        {trialStartDate && trialEndDate && (
          <div className="text-xs text-muted-foreground space-y-1">
            <div>Started: {new Date(trialStartDate).toLocaleDateString()}</div>
            <div>Ends: {new Date(trialEndDate).toLocaleDateString()}</div>
            {gracePeriodEndDate && (
              <div>Grace period until: {new Date(gracePeriodEndDate).toLocaleDateString()}</div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};