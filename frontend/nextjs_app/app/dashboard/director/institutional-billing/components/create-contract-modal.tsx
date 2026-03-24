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
import { Calculator, Building2, Users, DollarSign } from 'lucide-react';

interface Organization {
  id: string;
  name: string;
  contactEmail: string;
}

interface PricingTier {
  minSeats: number;
  maxSeats: number | null;
  pricePerStudent: number;
  tierName: string;
}

interface CreateContractModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const PRICING_TIERS: PricingTier[] = [
  { minSeats: 1, maxSeats: 50, pricePerStudent: 15, tierName: 'Starter' },
  { minSeats: 51, maxSeats: 200, pricePerStudent: 12, tierName: 'Professional' },
  { minSeats: 201, maxSeats: 500, pricePerStudent: 9, tierName: 'Enterprise' },
  { minSeats: 501, maxSeats: null, pricePerStudent: 7, tierName: 'Premium' }
];

export function CreateContractModal({ isOpen, onClose, onSuccess }: CreateContractModalProps) {
  const [loading, setLoading] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentTier, setCurrentTier] = useState<PricingTier | null>(null);
  
  const [formData, setFormData] = useState({
    organizationId: '',
    studentSeatCount: '',
    billingCycle: 'monthly',
    billingContactName: '',
    billingContactEmail: '',
    billingContactPhone: '',
    billingAddress: '',
    purchaseOrderRequired: false,
    customDiscount: '',
    startDate: '',
    endDate: '',
    // Academic calendar options
    academicCalendarAlignment: false,
    semesterStart: '',
    fiscalYearAlignment: false,
    fiscalYearStart: 'july'
  });

  useEffect(() => {
    if (isOpen) {
      fetchOrganizations();
      // Set default dates
      const today = new Date();
      const nextYear = new Date(today);
      nextYear.setFullYear(today.getFullYear() + 1);
      
      setFormData(prev => ({
        ...prev,
        startDate: today.toISOString().split('T')[0],
        endDate: nextYear.toISOString().split('T')[0]
      }));
    }
  }, [isOpen]);

  useEffect(() => {
    if (formData.studentSeatCount) {
      const seatCount = parseInt(formData.studentSeatCount);
      const tier = PRICING_TIERS.find(t => 
        seatCount >= t.minSeats && (t.maxSeats === null || seatCount <= t.maxSeats)
      );
      setCurrentTier(tier || null);
    } else {
      setCurrentTier(null);
    }
  }, [formData.studentSeatCount]);

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('/api/organizations/');
      const data = await response.json();
      setOrganizations(data.results || []);
    } catch (error) {
      console.error('Failed to fetch organizations:', error);
    }
  };

  const calculatePricing = () => {
    if (!currentTier || !formData.studentSeatCount) return null;
    
    const seatCount = parseInt(formData.studentSeatCount);
    const monthlyAmount = seatCount * currentTier.pricePerStudent;
    const annualAmount = monthlyAmount * 12;
    
    // Apply custom discount
    let discountAmount = 0;
    if (formData.customDiscount) {
      const discountPercent = parseFloat(formData.customDiscount);
      discountAmount = annualAmount * (discountPercent / 100);
    }
    
    // Apply annual payment discount
    let annualDiscount = 0;
    if (formData.billingCycle === 'annual') {
      annualDiscount = annualAmount * 0.025; // 2.5% annual discount
    }
    
    const finalAnnualAmount = annualAmount - discountAmount - annualDiscount;
    const finalMonthlyAmount = finalAnnualAmount / 12;
    
    return {
      seatCount,
      monthlyAmount,
      annualAmount,
      discountAmount,
      annualDiscount,
      finalMonthlyAmount,
      finalAnnualAmount,
      pricePerStudent: currentTier.pricePerStudent,
      tierName: currentTier.tierName
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        organization_id: formData.organizationId,
        student_seat_count: parseInt(formData.studentSeatCount),
        billing_cycle: formData.billingCycle,
        billing_contact_name: formData.billingContactName,
        billing_contact_email: formData.billingContactEmail,
        billing_contact_phone: formData.billingContactPhone,
        billing_address: formData.billingAddress,
        purchase_order_required: formData.purchaseOrderRequired,
        custom_discount: formData.customDiscount ? parseFloat(formData.customDiscount) : 0,
        start_date: formData.startDate,
        end_date: formData.endDate,
        // Academic calendar settings
        academic_calendar_alignment: formData.academicCalendarAlignment,
        semester_start: formData.semesterStart,
        fiscal_year_alignment: formData.fiscalYearAlignment,
        fiscal_year_start: formData.fiscalYearStart
      };

      const response = await fetch('/api/v1/institutional/contracts/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
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

  const pricing = calculatePricing();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Create Institutional Contract
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Contract Details */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Contract Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="organization">Organization *</Label>
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
                    <Label htmlFor="studentSeatCount">Student Seat Count *</Label>
                    <Input
                      id="studentSeatCount"
                      type="number"
                      min="1"
                      value={formData.studentSeatCount}
                      onChange={(e) => setFormData(prev => ({ ...prev, studentSeatCount: e.target.value }))}
                      placeholder="Number of student licenses"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="billingCycle">Billing Cycle</Label>
                    <Select
                      value={formData.billingCycle}
                      onValueChange={(value) => setFormData(prev => ({ ...prev, billingCycle: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="quarterly">Quarterly</SelectItem>
                        <SelectItem value="annual">Annual (2.5% discount)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="startDate">Start Date *</Label>
                      <Input
                        id="startDate"
                        type="date"
                        value={formData.startDate}
                        onChange={(e) => setFormData(prev => ({ ...prev, startDate: e.target.value }))}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="endDate">End Date *</Label>
                      <Input
                        id="endDate"
                        type="date"
                        value={formData.endDate}
                        onChange={(e) => setFormData(prev => ({ ...prev, endDate: e.target.value }))}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="customDiscount">Custom Discount (%)</Label>
                    <Input
                      id="customDiscount"
                      type="number"
                      min="0"
                      max="50"
                      step="0.1"
                      value={formData.customDiscount}
                      onChange={(e) => setFormData(prev => ({ ...prev, customDiscount: e.target.value }))}
                      placeholder="Additional discount percentage"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Academic Calendar Alignment */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Academic Calendar Options</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Switch
                      id="academicCalendarAlignment"
                      checked={formData.academicCalendarAlignment}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, academicCalendarAlignment: checked }))}
                    />
                    <Label htmlFor="academicCalendarAlignment">Align to Academic Calendar</Label>
                  </div>

                  {formData.academicCalendarAlignment && (
                    <div>
                      <Label htmlFor="semesterStart">Semester Start</Label>
                      <Select
                        value={formData.semesterStart}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, semesterStart: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select semester start" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="january">January (Spring)</SelectItem>
                          <SelectItem value="august">August (Fall)</SelectItem>
                          <SelectItem value="september">September (Fall)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="fiscalYearAlignment"
                      checked={formData.fiscalYearAlignment}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, fiscalYearAlignment: checked }))}
                    />
                    <Label htmlFor="fiscalYearAlignment">Align to Fiscal Year</Label>
                  </div>

                  {formData.fiscalYearAlignment && (
                    <div>
                      <Label htmlFor="fiscalYearStart">Fiscal Year Start</Label>
                      <Select
                        value={formData.fiscalYearStart}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, fiscalYearStart: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="july">July</SelectItem>
                          <SelectItem value="january">January</SelectItem>
                          <SelectItem value="october">October</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right Column - Billing & Pricing */}
            <div className="space-y-6">
              {/* Pricing Calculator */}
              {pricing && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Calculator className="h-5 w-5" />
                      Pricing Calculator
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Pricing Tier</span>
                      <Badge variant="secondary">{pricing.tierName}</Badge>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm">Base Rate</span>
                        <span className="font-medium">{formatCurrency(pricing.pricePerStudent)}/student/month</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Monthly Amount</span>
                        <span className="font-medium">{formatCurrency(pricing.monthlyAmount)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm">Annual Amount</span>
                        <span className="font-medium">{formatCurrency(pricing.annualAmount)}</span>
                      </div>
                      
                      {pricing.discountAmount > 0 && (
                        <div className="flex justify-between text-green-600">
                          <span className="text-sm">Custom Discount</span>
                          <span className="font-medium">-{formatCurrency(pricing.discountAmount)}</span>
                        </div>
                      )}
                      
                      {pricing.annualDiscount > 0 && (
                        <div className="flex justify-between text-green-600">
                          <span className="text-sm">Annual Payment Discount</span>
                          <span className="font-medium">-{formatCurrency(pricing.annualDiscount)}</span>
                        </div>
                      )}
                      
                      <div className="border-t pt-2">
                        <div className="flex justify-between font-semibold">
                          <span>Final Monthly</span>
                          <span>{formatCurrency(pricing.finalMonthlyAmount)}</span>
                        </div>
                        <div className="flex justify-between font-semibold text-lg">
                          <span>Final Annual</span>
                          <span>{formatCurrency(pricing.finalAnnualAmount)}</span>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Billing Contact */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Billing Contact</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="billingContactName">Contact Name *</Label>
                    <Input
                      id="billingContactName"
                      value={formData.billingContactName}
                      onChange={(e) => setFormData(prev => ({ ...prev, billingContactName: e.target.value }))}
                      placeholder="Primary billing contact"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="billingContactEmail">Contact Email *</Label>
                    <Input
                      id="billingContactEmail"
                      type="email"
                      value={formData.billingContactEmail}
                      onChange={(e) => setFormData(prev => ({ ...prev, billingContactEmail: e.target.value }))}
                      placeholder="billing@organization.edu"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="billingContactPhone">Contact Phone</Label>
                    <Input
                      id="billingContactPhone"
                      type="tel"
                      value={formData.billingContactPhone}
                      onChange={(e) => setFormData(prev => ({ ...prev, billingContactPhone: e.target.value }))}
                      placeholder="Phone number"
                    />
                  </div>

                  <div>
                    <Label htmlFor="billingAddress">Billing Address</Label>
                    <Textarea
                      id="billingAddress"
                      value={formData.billingAddress}
                      onChange={(e) => setFormData(prev => ({ ...prev, billingAddress: e.target.value }))}
                      placeholder="Complete billing address"
                      rows={3}
                    />
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="purchaseOrderRequired"
                      checked={formData.purchaseOrderRequired}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, purchaseOrderRequired: checked }))}
                    />
                    <Label htmlFor="purchaseOrderRequired">Purchase Order Required</Label>
                  </div>
                </CardContent>
              </Card>
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