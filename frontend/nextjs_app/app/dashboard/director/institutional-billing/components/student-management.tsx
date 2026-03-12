'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Users, Search, Download, Upload, GraduationCap, Mail, Phone } from 'lucide-react';
import { EnrollStudentModal } from './enroll-student-modal';
import { AssignTracksModal } from './assign-tracks-modal';

interface Student {
  id: string;
  user: {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
  };
  contract: {
    id: string;
    contractNumber: string;
    organizationName: string;
  };
  enrolledAt: string;
  enrollmentType: string;
  isActive: boolean;
  trackAssignments: Array<{
    trackName: string;
    status: string;
    completionPercentage: number;
    isOverdue: boolean;
  }>;
}

export function StudentManagement() {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [contractFilter, setContractFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [showAssignTracksModal, setShowAssignTracksModal] = useState(false);
  const [selectedStudents, setSelectedStudents] = useState<string[]>([]);
  const [contracts, setContracts] = useState<any[]>([]);

  useEffect(() => {
    fetchStudents();
    fetchContracts();
  }, [currentPage, contractFilter, statusFilter, searchTerm]);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: '20',
        ...(contractFilter !== 'all' && { contract_id: contractFilter }),
        ...(statusFilter !== 'all' && { status: statusFilter }),
        ...(searchTerm && { search: searchTerm })
      });

      const response = await fetch(`/api/v1/institutional/students/?${params}`);
      const data = await response.json();
      
      setStudents(data.students || []);
      setTotalPages(data.pagination?.total_pages || 1);
    } catch (error) {
      console.error('Failed to fetch students:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchContracts = async () => {
    try {
      const response = await fetch('/api/v1/institutional/contracts/?status=active');
      const data = await response.json();
      setContracts(data.contracts || []);
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    }
  };

  const handleDeactivateStudent = async (studentId: string) => {
    try {
      const response = await fetch(`/api/v1/institutional/students/${studentId}/deactivate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Deactivated by administrator' })
      });

      if (response.ok) {
        fetchStudents();
      }
    } catch (error) {
      console.error('Failed to deactivate student:', error);
    }
  };

  const handleReactivateStudent = async (studentId: string) => {
    try {
      const response = await fetch(`/api/v1/institutional/students/${studentId}/reactivate/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        fetchStudents();
      }
    } catch (error) {
      console.error('Failed to reactivate student:', error);
    }
  };

  const handleSelectStudent = (studentId: string) => {
    setSelectedStudents(prev => 
      prev.includes(studentId) 
        ? prev.filter(id => id !== studentId)
        : [...prev, studentId]
    );
  };

  const handleSelectAll = () => {
    if (selectedStudents.length === students.length) {
      setSelectedStudents([]);
    } else {
      setSelectedStudents(students.map(s => s.id));
    }
  };

  const exportStudents = () => {
    const csvContent = [
      'First Name,Last Name,Email,Contract,Enrollment Date,Status,Active Tracks',
      ...students.map(student => [
        student.user.firstName,
        student.user.lastName,
        student.user.email,
        student.contract.contractNumber,
        new Date(student.enrolledAt).toLocaleDateString(),
        student.isActive ? 'Active' : 'Inactive',
        student.trackAssignments.map(t => t.trackName).join('; ')
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'institutional_students.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
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
            <CardTitle>Student Management</CardTitle>
            <div className="flex items-center space-x-3">
              <Button onClick={exportStudents} variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button onClick={() => setShowEnrollModal(true)} size="sm">
                <Users className="h-4 w-4 mr-2" />
                Enroll Student
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search students..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={contractFilter} onValueChange={setContractFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Contracts" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Contracts</SelectItem>
                {contracts.map((contract) => (
                  <SelectItem key={contract.id} value={contract.id}>
                    {contract.organization.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Bulk Actions */}
          {selectedStudents.length > 0 && (
            <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg mb-4">
              <span className="text-sm font-medium text-blue-800">
                {selectedStudents.length} student{selectedStudents.length > 1 ? 's' : ''} selected
              </span>
              <div className="flex space-x-2">
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => setShowAssignTracksModal(true)}
                >
                  Assign Tracks
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => setSelectedStudents([])}
                >
                  Clear Selection
                </Button>
              </div>
            </div>
          )}

          {/* Students Table */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2 pb-2 border-b">
              <input
                type="checkbox"
                checked={selectedStudents.length === students.length && students.length > 0}
                onChange={handleSelectAll}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-600">Select All</span>
            </div>

            {students.map((student) => (
              <div key={student.id} className="flex items-center space-x-4 p-4 border rounded-lg hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={selectedStudents.includes(student.id)}
                  onChange={() => handleSelectStudent(student.id)}
                  className="rounded"
                />
                
                <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div>
                    <p className="font-medium">{student.user.firstName} {student.user.lastName}</p>
                    <p className="text-sm text-gray-600 flex items-center">
                      <Mail className="h-3 w-3 mr-1" />
                      {student.user.email}
                    </p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Contract</p>
                    <p className="font-medium">{student.contract.organizationName}</p>
                    <p className="text-xs text-gray-500">{student.contract.contractNumber}</p>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Enrollment</p>
                    <p className="font-medium">{new Date(student.enrolledAt).toLocaleDateString()}</p>
                    <Badge variant="secondary" className="text-xs">
                      {student.enrollmentType.replace('_', ' ')}
                    </Badge>
                  </div>
                  
                  <div>
                    <p className="text-sm text-gray-600">Track Progress</p>
                    <div className="flex flex-wrap gap-1">
                      {student.trackAssignments.slice(0, 2).map((track, index) => (
                        <Badge 
                          key={index}
                          variant={track.isOverdue ? 'destructive' : track.status === 'completed' ? 'default' : 'secondary'}
                          className="text-xs"
                        >
                          {track.trackName} ({track.completionPercentage}%)
                        </Badge>
                      ))}
                      {student.trackAssignments.length > 2 && (
                        <Badge variant="outline" className="text-xs">
                          +{student.trackAssignments.length - 2} more
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Badge variant={student.isActive ? 'default' : 'secondary'}>
                    {student.isActive ? 'Active' : 'Inactive'}
                  </Badge>
                  
                  {student.isActive ? (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeactivateStudent(student.id)}
                    >
                      Deactivate
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleReactivateStudent(student.id)}
                    >
                      Reactivate
                    </Button>
                  )}
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
      {showEnrollModal && (
        <EnrollStudentModal
          isOpen={showEnrollModal}
          onClose={() => setShowEnrollModal(false)}
          onSuccess={() => {
            setShowEnrollModal(false);
            fetchStudents();
          }}
        />
      )}

      {showAssignTracksModal && (
        <AssignTracksModal
          isOpen={showAssignTracksModal}
          selectedStudents={selectedStudents}
          onClose={() => setShowAssignTracksModal(false)}
          onSuccess={() => {
            setShowAssignTracksModal(false);
            setSelectedStudents([]);
            fetchStudents();
          }}
        />
      )}
    </>
  );
}