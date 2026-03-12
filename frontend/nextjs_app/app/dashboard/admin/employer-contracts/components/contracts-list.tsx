'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Eye, Edit, MoreHorizontal, Filter } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

interface Contract {
  id: string;
  contractNumber: string;
  organization: {
    name: string;
    id: string;
  };
  retainerTier: {
    name: string;
    monthlyRetainer: number;
  };
  status: string;
  startDate: string;
  endDate: string;
  activeRequirementsCount: number;
  totalPlacements: number;
  totalRevenue: number;
}

interface ContractsListProps {
  onRefresh: () => void;
}

export function ContractsList({ onRefresh }: ContractsListProps) {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tierFilter, setTierFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchContracts();
  }, [currentPage, statusFilter, tierFilter, searchTerm]);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        ...(statusFilter !== 'all' && { status: statusFilter }),
        ...(tierFilter !== 'all' && { tier: tierFilter }),
        ...(searchTerm && { search: searchTerm })
      });

      const response = await fetch(`/api/marketplace/employer-contracts/contracts/?${params}`);
      const data = await response.json();
      
      setContracts(data.results || []);
      setTotalPages(Math.ceil(data.count / 20));
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusTransition = async (contractId: string, newStatus: string) => {
    try {
      const response = await fetch(`/api/marketplace/employer-contracts/contracts/${contractId}/transition/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          new_status: newStatus,
          notes: `Status changed to ${newStatus} via admin dashboard`
        })
      });

      if (response.ok) {
        fetchContracts();
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to update contract status:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'expired': return 'bg-red-100 text-red-800';
      case 'terminated': return 'bg-gray-100 text-gray-800';
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
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>All Contracts</CardTitle>
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
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
                <SelectItem value="terminated">Terminated</SelectItem>
              </SelectContent>
            </Select>
            <Select value={tierFilter} onValueChange={setTierFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Tier" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tiers</SelectItem>
                <SelectItem value="starter">Starter</SelectItem>
                <SelectItem value="professional">Professional</SelectItem>
                <SelectItem value="enterprise">Enterprise</SelectItem>
                <SelectItem value="premium">Premium</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left p-4 font-medium">Contract</th>
                <th className="text-left p-4 font-medium">Organization</th>
                <th className="text-left p-4 font-medium">Tier</th>
                <th className="text-left p-4 font-medium">Status</th>
                <th className="text-left p-4 font-medium">Period</th>
                <th className="text-left p-4 font-medium">Performance</th>
                <th className="text-left p-4 font-medium">Revenue</th>
                <th className="text-right p-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {contracts.map((contract) => (
                <tr key={contract.id} className="border-b hover:bg-gray-50">
                  <td className="p-4">
                    <div>
                      <p className="font-medium">{contract.contractNumber}</p>
                      <p className="text-sm text-gray-600">ID: {contract.id.slice(0, 8)}...</p>
                    </div>
                  </td>
                  <td className="p-4">
                    <p className="font-medium">{contract.organization.name}</p>
                  </td>
                  <td className="p-4">
                    <div>
                      <p className="font-medium">{contract.retainerTier.name}</p>
                      <p className="text-sm text-gray-600">
                        {formatCurrency(contract.retainerTier.monthlyRetainer)}/mo
                      </p>
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge className={getStatusColor(contract.status)}>
                      {contract.status}
                    </Badge>
                  </td>
                  <td className="p-4">
                    <div className="text-sm">
                      <p>{formatDate(contract.startDate)}</p>
                      <p className="text-gray-600">to {formatDate(contract.endDate)}</p>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="text-sm">
                      <p>{contract.activeRequirementsCount} active</p>
                      <p className="text-gray-600">{contract.totalPlacements} placed</p>
                    </div>
                  </td>
                  <td className="p-4">
                    <p className="font-medium">{formatCurrency(contract.totalRevenue)}</p>
                  </td>
                  <td className="p-4 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Edit className="h-4 w-4 mr-2" />
                          Edit Contract
                        </DropdownMenuItem>
                        {contract.status === 'pending' && (
                          <DropdownMenuItem onClick={() => handleStatusTransition(contract.id, 'active')}>
                            Activate Contract
                          </DropdownMenuItem>
                        )}
                        {contract.status === 'active' && (
                          <DropdownMenuItem onClick={() => handleStatusTransition(contract.id, 'terminated')}>
                            Terminate Contract
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
  );
}