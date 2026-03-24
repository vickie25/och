'use client';

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface RenewalQuoteModalProps {
  contract: {
    id: string;
    annualAmount: number;
    endDate: string;
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function RenewalQuoteModal({ contract, isOpen, onClose, onSuccess }: RenewalQuoteModalProps) {
  const [quotedAmount, setQuotedAmount] = useState(String(contract.annualAmount || 0));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await fetch(`/api/v1/institutional/contracts/${contract.id}/renewal-quote/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quoted_amount: Number(quotedAmount) }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to generate renewal quote.');
      }
      onSuccess();
    } catch (err: any) {
      setError(err?.message || 'Failed to generate renewal quote.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Renewal Quote</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Contract ends on {contract.endDate}. Enter the annual quote for renewal.
          </p>
          <div>
            <Label htmlFor="quoted-amount">Quoted Annual Amount</Label>
            <Input
              id="quoted-amount"
              type="number"
              min={0}
              step="0.01"
              value={quotedAmount}
              onChange={(e) => setQuotedAmount(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Generating...' : 'Generate Quote'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
