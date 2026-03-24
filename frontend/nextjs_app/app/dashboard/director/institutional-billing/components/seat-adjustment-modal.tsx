'use client';

import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface SeatAdjustmentModalProps {
  contract: {
    id: string;
    studentSeatCount: number;
  };
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function SeatAdjustmentModal({ contract, isOpen, onClose, onSuccess }: SeatAdjustmentModalProps) {
  const [seatCount, setSeatCount] = useState(String(contract.studentSeatCount));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await fetch(`/api/v1/institutional/contracts/${contract.id}/adjust-seats/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_seat_count: Number(seatCount) }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to adjust seats.');
      }
      onSuccess();
    } catch (err: any) {
      setError(err?.message || 'Failed to adjust seats.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Adjust Seats</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="seat-count">Seat Count</Label>
            <Input
              id="seat-count"
              type="number"
              min={1}
              value={seatCount}
              onChange={(e) => setSeatCount(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
