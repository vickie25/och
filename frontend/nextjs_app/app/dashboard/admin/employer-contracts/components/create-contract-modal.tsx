'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/Badge';

interface RetainerTier {
  id: string;
  name: string;
  monthlyRetainer: number;
  candidatesPerQuarter: number;
  placementFeePerCandidate: number;
  timeToShortlistDays: number;
  replacementGuaranteeDays: number;
  features: string[];
}

interface Organization {
  id: string;
  name: string;
  email: string;
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
    endDate: '',
    hasExclusivity: false,
    exclusivityDurationMonths: 6,
    customSLADays: '',
    customGuaranteeDays: '',
    specialRequirements: [] as string[]
  });

  const [newRequirement, setNewRequirement] = useState('');

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

  const addSpecialRequirement = () => {
    if (newRequirement.trim()) {
      setFormData(prev => ({
        ...prev,
        specialRequirements: [...prev.specialRequirements, newRequirement.trim()]
      }));
      setNewRequirement('');
    }
  };

  const removeSpecialRequirement = (index: number) => {
    setFormData(prev => ({
      ...prev,
      specialRequirements: prev.specialRequirements.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/marketplace/employer-contracts/contracts/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          organization_id: formData.organizationId,
          tier_name: formData.tierName,
          start_date: formData.startDate,
          end_date: formData.endDate,
          has_exclusivity: formData.hasExclusivity,
          exclusivity_duration_months: formData.exclusivityDurationMonths,
          custom_sla_days: formData.customSLADays ? parseInt(formData.customSLADays) : null,
          custom_guarantee_days: formData.customGuaranteeDays ? parseInt(formData.customGuaranteeDays) : null,
          special_requirements: formData.specialRequirements
        })
      });

      if (response.ok) {
        onSuccess();
      } else {
        const errorData = await response.json();
        console.error('Failed to create contract:', errorData);
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
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Employer Contract</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
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
                <Select
                  value={formData.tierName}
                  onValueChange={handleTierChange}
                >
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

            {/* Tier Details */}
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
                  <div className="flex justify-between">
                    <span>SLA (Shortlist):</span>
                    <span className="font-medium">{selectedTier.timeToShortlistDays} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Replacement Guarantee:</span>
                    <span className="font-medium">{selectedTier.replacementGuaranteeDays} days</span>
                  </div>
                  <div className="pt-2">
                    <p className="text-sm font-medium mb-2">Features:</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedTier.features.map((feature, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Custom Terms */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Custom Terms</h3>
            
            <div className="flex items-center space-x-2">
              <Switch
                id="exclusivity"
                checked={formData.hasExclusivity}
                onCheckedChange={(checked) => setFormData(prev => ({ ...prev, hasExclusivity: checked }))}
              />
              <Label htmlFor="exclusivity">Exclusivity Agreement</Label>
            </div>

            {formData.hasExclusivity && (
              <div>
                <Label htmlFor="exclusivityDuration">Exclusivity Duration (months)</Label>
                <Input
                  id="exclusivityDuration"
                  type="number"
                  min="1"
                  max="24"
                  value={formData.exclusivityDurationMonths}
                  onChange={(e) => setFormData(prev => ({ ...prev, exclusivityDurationMonths: parseInt(e.target.value) }))}
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="customSLA">Custom SLA Days (optional)</Label>
                <Input
                  id="customSLA"
                  type="number"
                  min="1"
                  max="30"
                  value={formData.customSLADays}
                  onChange={(e) => setFormData(prev => ({ ...prev, customSLADays: e.target.value }))}
                  placeholder={selectedTier ? `Default: ${selectedTier.timeToShortlistDays}` : ''}
                />
              </div>
              <div>
                <Label htmlFor="customGuarantee">Custom Guarantee Days (optional)</Label>
                <Input
                  id="customGuarantee"
                  type="number"
                  min="30"
                  max="180"
                  value={formData.customGuaranteeDays}
                  onChange={(e) => setFormData(prev => ({ ...prev, customGuaranteeDays: e.target.value }))}
                  placeholder={selectedTier ? `Default: ${selectedTier.replacementGuaranteeDays}` : ''}
                />
              </div>
            </div>

            <div>
              <Label>Special Requirements</Label>
              <div className="flex space-x-2 mt-1">
                <Input
                  value={newRequirement}
                  onChange={(e) => setNewRequirement(e.target.value)}
                  placeholder="Add special requirement..."
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSpecialRequirement())}
                />
                <Button type="button" onClick={addSpecialRequirement} variant="outline">
                  Add
                </Button>
              </div>
              {formData.specialRequirements.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.specialRequirements.map((req, index) => (
                    <Badge key={index} variant="outline" className="cursor-pointer" onClick={() => removeSpecialRequirement(index)}>
                      {req} ×
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
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