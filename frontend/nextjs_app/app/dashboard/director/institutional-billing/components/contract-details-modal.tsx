'use client';

import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/button';

interface ContractDetailsModalProps {
  contract: {
    id: string;
    contractNumber: string;
    organization: { id: string; name: string };
    status: string;
    startDate: string;
    endDate: string;
    studentSeatCount: number;
    perStudentRate: number;
    billingCycle: string;
    monthlyAmount: number;
    annualAmount: number;
    activeStudents: number;
    seatUtilization: number;
    totalInvoiced: number;
    daysUntilExpiry: number;
    isRenewable: boolean;
  };
  isOpen: boolean;
  onClose: () => void;
  onRefresh: () => void;
}

export function ContractDetailsModal({ contract, isOpen, onClose }: ContractDetailsModalProps) {
  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Contract Details</DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Contract Number</span>
            <span className="font-medium">{contract.contractNumber}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Organization</span>
            <span className="font-medium">{contract.organization.name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Status</span>
            <Badge>{contract.status}</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Period</span>
            <span className="font-medium">{contract.startDate} to {contract.endDate}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Seat Utilization</span>
            <span className="font-medium">
              {contract.activeStudents}/{contract.studentSeatCount} ({contract.seatUtilization.toFixed(1)}%)
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Per Student Rate</span>
            <span className="font-medium">{formatCurrency(contract.perStudentRate)}/month</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Monthly Amount</span>
            <span className="font-medium">{formatCurrency(contract.monthlyAmount)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Annual Amount</span>
            <span className="font-medium">{formatCurrency(contract.annualAmount)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground">Total Invoiced</span>
            <span className="font-medium">{formatCurrency(contract.totalInvoiced)}</span>
          </div>
        </div>
        <div className="flex justify-end pt-2">
          <Button variant="outline" onClick={onClose}>Close</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
