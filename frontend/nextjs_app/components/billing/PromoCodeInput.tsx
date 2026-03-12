import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface PromoCodeInputProps {
  onCodeApplied: (discount: { code: string; discountType: string; discountValue: number; description: string }) => void;
  onCodeRemoved: () => void;
  appliedCode?: string;
  planId?: string;
}

export const PromoCodeInput: React.FC<PromoCodeInputProps> = ({
  onCodeApplied,
  onCodeRemoved,
  appliedCode,
  planId
}) => {
  const [code, setCode] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const validatePromoCode = async () => {
    if (!code.trim()) return;
    
    setIsValidating(true);
    setError('');
    setSuccess('');

    try {
      const response = await fetch('/api/billing/validate-promo-code/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ 
          code: code.trim().toUpperCase(),
          plan_id: planId 
        })
      });

      const data = await response.json();

      if (response.ok && data.valid) {
        setSuccess(`Code applied! ${data.description}`);
        onCodeApplied({
          code: data.code,
          discountType: data.discount_type,
          discountValue: data.discount_value,
          description: data.description
        });
        setCode('');
      } else {
        setError(data.error || 'Invalid promo code');
      }
    } catch (err) {
      setError('Failed to validate promo code');
    } finally {
      setIsValidating(false);
    }
  };

  const removeCode = () => {
    setSuccess('');
    setError('');
    onCodeRemoved();
  };

  if (appliedCode) {
    return (
      <div className="space-y-2">
        <Label>Promotional Code</Label>
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="flex items-center justify-between">
            <span>Code <strong>{appliedCode}</strong> applied successfully!</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={removeCode}
              className="text-green-700 hover:text-green-800"
            >
              Remove
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Label htmlFor="promo-code">Promotional Code (Optional)</Label>
      <div className="flex gap-2">
        <Input
          id="promo-code"
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          placeholder="Enter promo code"
          className="flex-1"
          disabled={isValidating}
        />
        <Button
          onClick={validatePromoCode}
          disabled={!code.trim() || isValidating}
          variant="outline"
        >
          {isValidating ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            'Apply'
          )}
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
    </div>
  );
};