'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Upload, Download, Users, AlertCircle, CheckCircle, X } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface Contract {
  id: string;
  contractNumber: string;
  organizationName: string;
  studentSeatCount: number;
  activeStudents: number;
  availableSeats: number;
}

interface ImportResult {
  totalRows: number;
  successfulImports: number;
  duplicates: number;
  errors: string[];
  importedStudents: Array<{
    email: string;
    firstName: string;
    lastName: string;
    status: string;
  }>;
}

interface BulkImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function BulkImportModal({ isOpen, onClose, onSuccess }: BulkImportModalProps) {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [selectedContract, setSelectedContract] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [step, setStep] = useState<'select' | 'upload' | 'preview' | 'result'>('select');
  const [previewData, setPreviewData] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen) {
      fetchContracts();
      resetState();
    }
  }, [isOpen]);

  const resetState = () => {
    setSelectedContract('');
    setFile(null);
    setImporting(false);
    setImportResult(null);
    setUploadProgress(0);
    setStep('select');
    setPreviewData([]);
  };

  const fetchContracts = async () => {
    try {
      const response = await fetch('/api/v1/institutional/contracts/?status=active');
      const data = await response.json();
      
      const contractsWithSeats = data.contracts.map((contract: any) => ({
        id: contract.id,
        contractNumber: contract.contract_number,
        organizationName: contract.organization.name,
        studentSeatCount: contract.student_seat_count,
        activeStudents: contract.active_students,
        availableSeats: contract.student_seat_count - contract.active_students
      }));
      
      setContracts(contractsWithSeats);
    } catch (error) {
      console.error('Failed to fetch contracts:', error);
    }
  };

  const downloadTemplate = () => {
    const csvContent = [
      'first_name,last_name,email,department,student_id,track_assignments',
      'John,Doe,john.doe@university.edu,Computer Science,12345,"Web Development,Data Science"',
      'Jane,Smith,jane.smith@university.edu,Business,12346,"Digital Marketing"',
      'Mike,Johnson,mike.johnson@university.edu,Engineering,12347,"Full Stack Development"'
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'student_import_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      previewFile(selectedFile);
    }
  };

  const previewFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split('\n');
      const headers = lines[0].split(',');
      const preview = lines.slice(1, 6).map(line => {
        const values = line.split(',');
        const row: any = {};
        headers.forEach((header, index) => {
          row[header.trim()] = values[index]?.trim() || '';
        });
        return row;
      }).filter(row => row.email); // Filter out empty rows
      
      setPreviewData(preview);
      setStep('preview');
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!file || !selectedContract) return;

    setImporting(true);
    setStep('result');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('contract_id', selectedContract);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('/api/v1/institutional/students/bulk-import/', {
        method: 'POST',
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const result = await response.json();
      
      if (response.ok) {
        setImportResult(result);
      } else {
        setImportResult({
          totalRows: 0,
          successfulImports: 0,
          duplicates: 0,
          errors: [result.error || 'Import failed'],
          importedStudents: []
        });
      }
    } catch (error) {
      setImportResult({
        totalRows: 0,
        successfulImports: 0,
        duplicates: 0,
        errors: ['Network error occurred during import'],
        importedStudents: []
      });
    } finally {
      setImporting(false);
    }
  };

  const selectedContractData = contracts.find(c => c.id === selectedContract);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Bulk Import Students
          </DialogTitle>
        </DialogHeader>

        {step === 'select' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Select Contract</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label>Institutional Contract</Label>
                    <Select value={selectedContract} onValueChange={setSelectedContract}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a contract" />
                      </SelectTrigger>
                      <SelectContent>
                        {contracts.map((contract) => (
                          <SelectItem key={contract.id} value={contract.id}>
                            {contract.organizationName} - {contract.contractNumber}
                            <span className="ml-2 text-sm text-gray-500">
                              ({contract.availableSeats} seats available)
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedContractData && (
                    <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div className="text-center">
                        <p className="text-2xl font-bold text-blue-600">{selectedContractData.studentSeatCount}</p>
                        <p className="text-sm text-gray-600">Total Seats</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">{selectedContractData.activeStudents}</p>
                        <p className="text-sm text-gray-600">Active Students</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-orange-600">{selectedContractData.availableSeats}</p>
                        <p className="text-sm text-gray-600">Available Seats</p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Import Instructions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">1</div>
                  <div>
                    <p className="font-medium">Download Template</p>
                    <p className="text-sm text-gray-600">Use our CSV template with the correct column headers</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">2</div>
                  <div>
                    <p className="font-medium">Fill Student Data</p>
                    <p className="text-sm text-gray-600">Include first_name, last_name, email (required), department, student_id, track_assignments</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">3</div>
                  <div>
                    <p className="font-medium">Upload CSV</p>
                    <p className="text-sm text-gray-600">System will validate and import students automatically</p>
                  </div>
                </div>

                <Button onClick={downloadTemplate} variant="outline" className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Download CSV Template
                </Button>
              </CardContent>
            </Card>

            <div className="flex justify-end space-x-4">
              <Button variant="outline" onClick={onClose}>Cancel</Button>
              <Button 
                onClick={() => setStep('upload')} 
                disabled={!selectedContract}
              >
                Continue
              </Button>
            </div>
          </div>
        )}

        {step === 'upload' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Upload CSV File</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="csvFile">Select CSV File</Label>
                    <Input
                      id="csvFile"
                      type="file"
                      accept=".csv"
                      onChange={handleFileSelect}
                      className="mt-1"
                    />
                  </div>

                  {file && (
                    <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <div>
                          <p className="font-medium text-green-800">{file.name}</p>
                          <p className="text-sm text-green-600">
                            {(file.size / 1024).toFixed(1)} KB • Ready for preview
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end space-x-4">
              <Button variant="outline" onClick={() => setStep('select')}>Back</Button>
              <Button onClick={onClose}>Cancel</Button>
            </div>
          </div>
        )}

        {step === 'preview' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Preview Import Data</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p className="text-sm text-gray-600">
                    Preview of first 5 rows. Total rows to import: {previewData.length}
                  </p>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full border-collapse border border-gray-300">
                      <thead>
                        <tr className="bg-gray-50">
                          <th className="border border-gray-300 px-4 py-2 text-left">First Name</th>
                          <th className="border border-gray-300 px-4 py-2 text-left">Last Name</th>
                          <th className="border border-gray-300 px-4 py-2 text-left">Email</th>
                          <th className="border border-gray-300 px-4 py-2 text-left">Department</th>
                          <th className="border border-gray-300 px-4 py-2 text-left">Student ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {previewData.map((row, index) => (
                          <tr key={index}>
                            <td className="border border-gray-300 px-4 py-2">{row.first_name}</td>
                            <td className="border border-gray-300 px-4 py-2">{row.last_name}</td>
                            <td className="border border-gray-300 px-4 py-2">{row.email}</td>
                            <td className="border border-gray-300 px-4 py-2">{row.department}</td>
                            <td className="border border-gray-300 px-4 py-2">{row.student_id}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {selectedContractData && previewData.length > selectedContractData.availableSeats && (
                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <AlertCircle className="h-5 w-5 text-yellow-600" />
                        <div>
                          <p className="font-medium text-yellow-800">Seat Limit Warning</p>
                          <p className="text-sm text-yellow-600">
                            You're trying to import {previewData.length} students, but only {selectedContractData.availableSeats} seats are available.
                            Only the first {selectedContractData.availableSeats} students will be imported.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end space-x-4">
              <Button variant="outline" onClick={() => setStep('upload')}>Back</Button>
              <Button onClick={onClose}>Cancel</Button>
              <Button onClick={handleImport}>
                Import Students
              </Button>
            </div>
          </div>
        )}

        {step === 'result' && (
          <div className="space-y-6">
            {importing ? (
              <Card>
                <CardContent className="p-6">
                  <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="font-medium">Importing students...</p>
                    <Progress value={uploadProgress} className="w-full" />
                    <p className="text-sm text-gray-600">{uploadProgress}% complete</p>
                  </div>
                </CardContent>
              </Card>
            ) : importResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {importResult.errors.length === 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-yellow-600" />
                    )}
                    Import Results
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">{importResult.successfulImports}</p>
                      <p className="text-sm text-gray-600">Successfully Imported</p>
                    </div>
                    <div className="text-center p-4 bg-yellow-50 rounded-lg">
                      <p className="text-2xl font-bold text-yellow-600">{importResult.duplicates}</p>
                      <p className="text-sm text-gray-600">Duplicates Skipped</p>
                    </div>
                    <div className="text-center p-4 bg-red-50 rounded-lg">
                      <p className="text-2xl font-bold text-red-600">{importResult.errors.length}</p>
                      <p className="text-sm text-gray-600">Errors</p>
                    </div>
                  </div>

                  {importResult.errors.length > 0 && (
                    <div className="space-y-2">
                      <p className="font-medium text-red-800">Errors:</p>
                      <ul className="list-disc list-inside space-y-1">
                        {importResult.errors.map((error, index) => (
                          <li key={index} className="text-sm text-red-600">{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {importResult.importedStudents.length > 0 && (
                    <div className="space-y-2">
                      <p className="font-medium">Successfully Imported Students:</p>
                      <div className="max-h-40 overflow-y-auto">
                        <ul className="space-y-1">
                          {importResult.importedStudents.map((student, index) => (
                            <li key={index} className="text-sm flex items-center justify-between">
                              <span>{student.firstName} {student.lastName} ({student.email})</span>
                              <Badge variant="secondary">{student.status}</Badge>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {!importing && (
              <div className="flex justify-end space-x-4">
                <Button variant="outline" onClick={resetState}>Import More</Button>
                <Button onClick={() => { onSuccess(); onClose(); }}>
                  Done
                </Button>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}