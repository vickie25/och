'use client';

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Upload, GraduationCap, Mail, FileText, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface AcademicDiscount {
  id: string;
  status: 'pending' | 'verified' | 'expired' | 'rejected';
  discountRate: number;
  verificationMethod: string;
  institutionName?: string;
  expiresAt?: string;
  daysUntilExpiry?: number;
  isValid: boolean;
}

interface AcademicDiscountModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (discount: AcademicDiscount) => void;
}

export function AcademicDiscountModal({ isOpen, onClose, onSuccess }: AcademicDiscountModalProps) {
  const [step, setStep] = useState<'check' | 'email' | 'upload' | 'result'>('check');
  const [loading, setLoading] = useState(false);
  const [existingDiscount, setExistingDiscount] = useState<AcademicDiscount | null>(null);
  
  const [emailForm, setEmailForm] = useState({
    eduEmail: ''
  });
  
  const [uploadForm, setUploadForm] = useState({
    institutionName: '',
    documentType: '',
    document: null as File | null
  });
  
  const [result, setResult] = useState<{
    success: boolean;
    message: string;
    discount?: AcademicDiscount;
  } | null>(null);

  useEffect(() => {
    if (isOpen) {
      checkExistingDiscount();
    }
  }, [isOpen]);

  const checkExistingDiscount = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/enhanced-billing/academic/status/');
      const data = await response.json();
      
      if (data.has_discount) {
        setExistingDiscount(data.discount);
        setStep('result');
        setResult({
          success: true,
          message: getStatusMessage(data.discount.status),
          discount: data.discount
        });
      } else {
        setStep('email');
      }
    } catch (error) {
      console.error('Failed to check academic discount status:', error);
      setStep('email');
    } finally {
      setLoading(false);
    }
  };

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'verified':
        return 'Your academic discount is active! You receive 30% off all subscription plans.';
      case 'pending':
        return 'Your academic discount application is under review. We\'ll notify you within 1-2 business days.';
      case 'rejected':
        return 'Your academic discount application was not approved. You can reapply with additional documentation.';
      case 'expired':
        return 'Your academic discount has expired. Please reverify your student status to continue receiving the discount.';
      default:
        return 'Academic discount status unknown.';
    }
  };

  const handleEmailVerification = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/enhanced-billing/academic/verify-email/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          edu_email: emailForm.eduEmail
        })
      });

      const data = await response.json();
      
      if (response.ok) {
        setResult({
          success: true,
          message: data.message,
          discount: data.discount
        });
        setStep('result');
        
        if (data.discount.status === 'verified') {
          onSuccess(data.discount);
        }
      } else {
        if (data.error.includes('manual')) {
          setStep('upload');
        } else {
          setResult({
            success: false,
            message: data.error
          });
          setStep('result');
        }
      }
    } catch (error) {
      setResult({
        success: false,
        message: 'Failed to verify educational email. Please try again.'
      });
      setStep('result');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new FormData();
      if (uploadForm.document) {
        formData.append('document', uploadForm.document);
      }
      formData.append('document_type', uploadForm.documentType);
      formData.append('institution_name', uploadForm.institutionName);

      const response = await fetch('/api/enhanced-billing/academic/upload-document/', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      setResult({
        success: response.ok,
        message: data.message || data.error,
        discount: data.discount
      });
      setStep('result');
      
    } catch (error) {
      setResult({
        success: false,
        message: 'Failed to upload document. Please try again.'
      });
      setStep('result');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
        return <CheckCircle className="h-8 w-8 text-green-600" />;
      case 'pending':
        return <Clock className="h-8 w-8 text-yellow-600" />;
      case 'rejected':
        return <AlertCircle className="h-8 w-8 text-red-600" />;
      case 'expired':
        return <AlertCircle className="h-8 w-8 text-orange-600" />;
      default:
        return <GraduationCap className="h-8 w-8 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'verified':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5" />
            Academic Discount Verification
          </DialogTitle>
        </DialogHeader>

        {step === 'check' && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {step === 'email' && (
          <form onSubmit={handleEmailVerification} className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Verify Educational Email</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <GraduationCap className="h-5 w-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-blue-800">Get 30% Off Student Discount</p>
                      <p className="text-sm text-blue-600 mt-1">
                        Verify your student status to receive a 30% discount on all subscription plans.
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <Label htmlFor="eduEmail">Educational Email Address</Label>
                  <Input
                    id="eduEmail"
                    type="email"
                    value={emailForm.eduEmail}
                    onChange={(e) => setEmailForm(prev => ({ ...prev, eduEmail: e.target.value }))}
                    placeholder="your.name@university.edu"
                    required
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    Enter your official educational email address ending in .edu
                  </p>
                </div>

                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-2">What qualifies for academic discount:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Current students at accredited institutions</li>
                    <li>Valid .edu email address</li>
                    <li>Alternative: Upload student ID or enrollment verification</li>
                  </ul>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end space-x-4">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Verifying...' : 'Verify Email'}
              </Button>
            </div>
          </form>
        )}

        {step === 'upload' && (
          <form onSubmit={handleDocumentUpload} className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Upload Verification Document</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <FileText className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-yellow-800">Manual Verification Required</p>
                      <p className="text-sm text-yellow-600 mt-1">
                        Please upload a document to verify your student status. Review typically takes 1-2 business days.
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <Label htmlFor="institutionName">Institution Name</Label>
                  <Input
                    id="institutionName"
                    value={uploadForm.institutionName}
                    onChange={(e) => setUploadForm(prev => ({ ...prev, institutionName: e.target.value }))}
                    placeholder="University of Example"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="documentType">Document Type</Label>
                  <Select
                    value={uploadForm.documentType}
                    onValueChange={(value) => setUploadForm(prev => ({ ...prev, documentType: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select document type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="student_id">Student ID Card</SelectItem>
                      <SelectItem value="transcript">Official Transcript</SelectItem>
                      <SelectItem value="enrollment_letter">Enrollment Verification Letter</SelectItem>
                      <SelectItem value="class_schedule">Current Class Schedule</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="document">Upload Document</Label>
                  <Input
                    id="document"
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={(e) => setUploadForm(prev => ({ ...prev, document: e.target.files?.[0] || null }))}
                    required
                  />
                  <p className="text-xs text-gray-600 mt-1">
                    Accepted formats: PDF, JPG, PNG (max 5MB)
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end space-x-4">
              <Button type="button" variant="outline" onClick={() => setStep('email')}>
                Back
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={loading || !uploadForm.document}>
                {loading ? 'Uploading...' : 'Upload Document'}
              </Button>
            </div>
          </form>
        )}

        {step === 'result' && result && (
          <div className="space-y-6">
            <Card>
              <CardContent className="p-6">
                <div className="text-center space-y-4">
                  {existingDiscount && getStatusIcon(existingDiscount.status)}
                  
                  <div>
                    <p className={`text-lg font-medium ${result.success ? 'text-green-800' : 'text-red-800'}`}>
                      {result.success ? 'Success!' : 'Error'}
                    </p>
                    <p className="text-sm text-gray-600 mt-2">
                      {result.message}
                    </p>
                  </div>

                  {existingDiscount && (
                    <div className="space-y-3">
                      <Badge className={getStatusColor(existingDiscount.status)}>
                        {existingDiscount.status.toUpperCase()}
                      </Badge>
                      
                      {existingDiscount.status === 'verified' && (
                        <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                          <div className="text-center">
                            <p className="text-2xl font-bold text-green-600">
                              {existingDiscount.discountRate}% OFF
                            </p>
                            <p className="text-sm text-green-700">
                              All subscription plans
                            </p>
                            {existingDiscount.expiresAt && (
                              <p className="text-xs text-green-600 mt-2">
                                Valid until {new Date(existingDiscount.expiresAt).toLocaleDateString()}
                                {existingDiscount.daysUntilExpiry && existingDiscount.daysUntilExpiry <= 30 && (
                                  <span className="text-orange-600 ml-1">
                                    (expires in {existingDiscount.daysUntilExpiry} days)
                                  </span>
                                )}
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {existingDiscount.status === 'pending' && (
                        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                          <div className="text-center">
                            <Clock className="h-6 w-6 text-yellow-600 mx-auto mb-2" />
                            <p className="text-sm text-yellow-700">
                              Your application is under review. We'll email you within 1-2 business days.
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end space-x-4">
              {existingDiscount?.status === 'rejected' && (
                <Button onClick={() => setStep('upload')}>
                  Try Again
                </Button>
              )}
              <Button onClick={() => {
                if (result.success && result.discount) {
                  onSuccess(result.discount);
                }
                onClose();
              }}>
                {result.success ? 'Continue' : 'Close'}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}