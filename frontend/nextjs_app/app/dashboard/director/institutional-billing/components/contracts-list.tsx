'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Eye, Edit, MoreHorizontal, Users, DollarSign, Calendar, AlertTriangle } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ContractDetailsModal } from './contract-details-modal';
import { SeatAdjustmentModal } from './seat-adjustment-modal';
import { RenewalQuoteModal } from './renewal-quote-modal';

interface Contract {
  id: string;
  contractNumber: string;
  organization: {
    id: string;
    name: string;
  };
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
}

interface ContractsListProps {
  onRefresh: () => void;
}

export function ContractsList({ onRefresh }: ContractsListProps) {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedContract, setSelectedContract] = useState<Contract | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showSeatAdjustmentModal, setShowSeatAdjustmentModal] = useState(false);
  const [showRenewalModal, setShowRenewalModal] = useState(false);

  useEffect(() => {
    fetchContracts();
  }, [currentPage, statusFilter, searchTerm]);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20',
        ...(statusFilter !== 'all' && { status: statusFilter }),
        ...(searchTerm && { search: searchTerm })
      });

      const response = await fetch(`/api/v1/institutional/contracts/?${params}`);
      const data = await response.json();
      
      setContracts(data.contracts || []);
      setTotalPages(data.pagination?.total_pages || 1);
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleActivateContract = async (contractId: string) => {
    try {
      const response = await fetch(`/api/v1/institutional/contracts/${contractId}/activate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        fetchContracts();
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to activate contract:', error);
    }
  };

  const handleViewDetails = (contract: Contract) => {
    setSelectedContract(contract);
    setShowDetailsModal(true);
  };

  const handleAdjustSeats = (contract: Contract) => {
    setSelectedContract(contract);
    setShowSeatAdjustmentModal(true);
  };

  const handleRenewalQuote = (contract: Contract) => {
    setSelectedContract(contract);
    setShowRenewalModal(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'pending_renewal': return 'bg-blue-100 text-blue-800';
      case 'expired': return 'bg-red-100 text-red-800';
      case 'terminated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Institutional Contracts</CardTitle>
            <div className="flex items-center space-x-4">
              <Input
                placeholder="Search contracts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-64"
              />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="pending_renewal">Pending Renewal</SelectItem>
                  <SelectItem value="expired">Expired</SelectItem>
                  <SelectItem value="terminated">Terminated</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {contracts.map((contract) => (
              <div key={contract.id} className="border rounded-lg p-6 hover:bg-gray-50">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center space-x-4">
                    <div>
                      <h3 className="font-semibold text-lg">{contract.organization.name}</h3>
                      <p className="text-sm text-gray-600">{contract.contractNumber}</p>
                    </div>
                    <Badge className={getStatusColor(contract.status)}>
                      {contract.status.replace('_', ' ')}
                    </Badge>
                    {contract.daysUntilExpiry <= 60 && contract.status === 'active' && (
                      <Badge variant="outline" className="text-orange-600 border-orange-600">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Expires in {contract.daysUntilExpiry} days
                      </Badge>
                    )}
                  </div>
                  
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleViewDetails(contract)}>
                        <Eye className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      {contract.status === 'active' && (
                        <DropdownMenuItem onClick={() => handleAdjustSeats(contract)}>
                          <Users className="h-4 w-4 mr-2" />
                          Adjust Seats
                        </DropdownMenuItem>
                      )}
                      {contract.isRenewable && (
                        <DropdownMenuItem onClick={() => handleRenewalQuote(contract)}>
                          <Calendar className="h-4 w-4 mr-2" />
                          Renewal Quote
                        </DropdownMenuItem>
                      )}
                      {contract.status === 'draft' && (
                        <DropdownMenuItem onClick={() => handleActivateContract(contract.id)}>
                          Activate Contract
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="flex items-center space-x-3">
                    <Users className="h-5 w-5 text-blue-600" />
                    <div>
                      <p className="text-sm text-gray-600">Seat Utilization</p>
                      <p className="font-semibold">
                        {contract.activeStudents}/{contract.studentSeatCount} 
                        <span className="text-sm text-gray-500 ml-1">
                          ({contract.seatUtilization.toFixed(1)}%)
                        </span>
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <DollarSign className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm text-gray-600">Monthly Revenue</p>
                      <p className="font-semibold">{formatCurrency(contract.monthlyAmount)}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <Calendar className="h-5 w-5 text-purple-600" />
                    <div>
                      <p className="text-sm text-gray-600">Contract Period</p>
                      <p className="font-semibold text-sm">
                        {formatDate(contract.startDate)} - {formatDate(contract.endDate)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <div className="h-5 w-5 bg-indigo-600 rounded flex items-center justify-center">
                      <span className="text-white text-xs font-bold">$</span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Total Invoiced</p>
                      <p className="font-semibold">{formatCurrency(contract.totalInvoiced)}</p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t">
                  <div className="flex justify-between items-center text-sm">
                    <div className="flex items-center space-x-4">
                      <span className="text-gray-600">
                        Billing: <span className="font-medium capitalize">{contract.billingCycle}</span>
                      </span>
                      <span className="text-gray-600">
                        Rate: <span className="font-medium">{formatCurrency(contract.perStudentRate)}/student/month</span>
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      {contract.seatUtilization < 50 && (
                        <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                          Low Utilization
                        </Badge>
                      )}
                      {contract.seatUtilization > 90 && (
                        <Badge variant="outline" className="text-red-600 border-red-600">
                          Near Capacity
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-between items-center mt-6">
              <p className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modals */}
      {showDetailsModal && selectedContract && (
        <ContractDetailsModal
          contract={selectedContract}
          isOpen={showDetailsModal}
          onClose={() => setShowDetailsModal(false)}
          onRefresh={() => {
            fetchContracts();
            onRefresh();
          }}
        />
      )}

      {showSeatAdjustmentModal && selectedContract && (
        <SeatAdjustmentModal
          contract={selectedContract}
          isOpen={showSeatAdjustmentModal}
          onClose={() => setShowSeatAdjustmentModal(false)}
          onSuccess={() => {
            setShowSeatAdjustmentModal(false);
            fetchContracts();
            onRefresh();
          }}
        />
      )}

      {showRenewalModal && selectedContract && (
        <RenewalQuoteModal
          contract={selectedContract}
          isOpen={showRenewalModal}
          onClose={() => setShowRenewalModal(false)}
          onSuccess={() => {
            setShowRenewalModal(false);
            fetchContracts();
            onRefresh();
          }}
        />
      )}
    </>
  );
}