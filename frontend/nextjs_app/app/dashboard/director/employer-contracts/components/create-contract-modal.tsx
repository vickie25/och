'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface RetainerTier {
  id: string;
  name: string;
  monthlyRetainer: number;
  candidatesPerQuarter: number;
  placementFeePerCandidate: number;
}

interface Organization {
  id: string;
  name: string;
}

interface CreateContractModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function CreateContractModal({ isOpen, onClose, onSuccess }: CreateContractModalProps) {
  const [loading, setLoading] = useState(false);
  const [tiers, setTiers] = useState<RetainerTier[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedTier, setSelectedTier] = useState<RetainerTier | null>(null);
  
  const [formData, setFormData] = useState({
    organizationId: '',
    tierName: '',
    startDate: '',
    endDate: ''
  });

  useEffect(() => {
    if (isOpen) {
      fetchTiers();
      fetchOrganizations();
    }
  }, [isOpen]);

  const fetchTiers = async () => {
    try {
      const response = await fetch('/api/marketplace/employer-contracts/tiers/');
      const data = await response.json();
      setTiers(data.tiers || []);
    } catch (error) {
      console.error('Failed to fetch tiers:', error);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('/api/organizations/');
      const data = await response.json();
      setOrganizations(data.results || []);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const handleTierChange = (tierName: string) => {
    const tier = tiers.find(t => t.name === tierName);
    setSelectedTier(tier || null);
    setFormData(prev => ({ ...prev, tierName }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/marketplace/employer-contracts/contracts/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          organization_id: formData.organizationId,
          tier_name: formData.tierName,
          start_date: formData.startDate,
          end_date: formData.endDate
        })
      });

      if (response.ok) {
        onSuccess();
      }
    } catch (error) {
      console.error('Failed to create contract:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create New Employer Contract</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <Label htmlFor="organization">Organization</Label>
                <Select
                  value={formData.organizationId}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, organizationId: value }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
                  </SelectTrigger>
                  <SelectContent>
                    {organizations.map((org) => (
                      <SelectItem key={org.id} value={org.id}>
                        {org.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="tier">Retainer Tier</Label>
                <Select value={formData.tierName} onValueChange={handleTierChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select tier" />
                  </SelectTrigger>
                  <SelectContent>
                    {tiers.map((tier) => (
                      <SelectItem key={tier.id} value={tier.name}>
                        {tier.name} - {formatCurrency(tier.monthlyRetainer)}/mo
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="startDate">Start Date</Label>
                  <Input
                    id="startDate"
                    type="date"
                    value={formData.startDate}
                    onChange={(e) => setFormData(prev => ({ ...prev, startDate: e.target.value }))}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="endDate">End Date</Label>
                  <Input
                    id="endDate"
                    type="date"
                    value={formData.endDate}
                    onChange={(e) => setFormData(prev => ({ ...prev, endDate: e.target.value }))}
                    required
                  />
                </div>
              </div>
            </div>

            {selectedTier && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{selectedTier.name} Tier</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>Monthly Retainer:</span>
                    <span className="font-medium">{formatCurrency(selectedTier.monthlyRetainer)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Candidates/Quarter:</span>
                    <span className="font-medium">{selectedTier.candidatesPerQuarter}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Placement Fee:</span>
                    <span className="font-medium">{formatCurrency(selectedTier.placementFeePerCandidate)}</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="flex justify-end space-x-4 pt-4 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Creating...' : 'Create Contract'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}