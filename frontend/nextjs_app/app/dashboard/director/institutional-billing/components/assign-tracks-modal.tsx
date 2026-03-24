'use client';

import React, { useMemo, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface AssignTracksModalProps {
  isOpen: boolean;
  selectedStudents: string[];
  onClose: () => void;
  onSuccess: () => void;
}

export function AssignTracksModal({
  isOpen,
  selectedStudents,
  onClose,
  onSuccess,
}: AssignTracksModalProps) {
  const [trackId, setTrackId] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const count = useMemo(() => selectedStudents.length, [selectedStudents]);

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await fetch('/api/v1/institutional/students/assign-tracks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_ids: selectedStudents,
          track_id: trackId,
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data?.detail || 'Failed to assign tracks.');
      }

      setTrackId('');
      onSuccess();
    } catch (err: any) {
      setError(err?.message || 'Failed to assign tracks.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Assign Tracks</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleAssign} className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Assign a track to {count} selected student{count === 1 ? '' : 's'}.
          </p>
          <div>
            <Label htmlFor="track-id">Track ID</Label>
            <Input
              id="track-id"
              value={trackId}
              onChange={(e) => setTrackId(e.target.value)}
              placeholder="Enter track ID"
              required
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting || count === 0}>
              {submitting ? 'Assigning...' : 'Assign'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
