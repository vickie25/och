import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  FileText, 
  Download, 
  Calendar as CalendarIcon,
  Clock,
  CheckCircle,
  AlertTriangle,
  BarChart3,
  PieChart,
  TrendingUp,
  Users,
  DollarSign
} from 'lucide-react';
import { format } from 'date-fns';

interface FinancialReportsProps {
  userId: string;
}

interface Report {
  id: string;
  report_type: string;
  title: string;
  status: string;
  created_at: string;
  completed_at?: string;
  file_url?: string;
  generated_by_email: string;
}

export const FinancialReports: React.FC<FinancialReportsProps> = ({ userId }) => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState('');
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();

  const reportTypes = [
    { value: 'revenue_summary', label: 'Revenue Summary', icon: DollarSign },
    { value: 'subscription_analytics', label: 'Subscription Analytics', icon: Users },
    { value: 'cohort_financials', label: 'Cohort Financials', icon: BarChart3 },
    { value: 'mentor_compensation', label: 'Mentor Compensation', icon: TrendingUp },
    { value: 'cash_flow', label: 'Cash Flow Report', icon: PieChart },
    { value: 'audit_report', label: 'Audit Report', icon: FileText }
  ];

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch('/api/finance/reports/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setReports(data.reports || []);
      }
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    if (!selectedReportType || !startDate || !endDate) {
      return;
    }

    setGenerating(true);
    try {
      const response = await fetch('/api/finance/reports/generate/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          report_type: selectedReportType,
          period_start: format(startDate, 'yyyy-MM-dd'),
          period_end: format(endDate, 'yyyy-MM-dd')
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Refresh reports list
        fetchReports();
        // Reset form
        setSelectedReportType('');
        setStartDate(undefined);
        setEndDate(undefined);
      }
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setGenerating(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'generating':
        return <Clock className="h-4 w-4 text-blue-600" />;
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'generating': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getReportTypeIcon = (reportType: string) => {
    const type = reportTypes.find(t => t.value === reportType);
    if (type) {
      const Icon = type.icon;
      return <Icon className="h-4 w-4" />;
    }
    return <FileText className="h-4 w-4" />;
  };

  const getReportTypeLabel = (reportType: string) => {
    const type = reportTypes.find(t => t.value === reportType);
    return type ? type.label : reportType;
  };

  const downloadReport = (report: Report) => {
    if (report.file_url) {
      window.open(report.file_url, '_blank');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Financial Reports</h1>
        <p className="text-muted-foreground">
          Generate and download comprehensive financial reports
        </p>
      </div>

      {/* Generate New Report */}
      <Card>
        <CardHeader>
          <CardTitle>Generate New Report</CardTitle>
          <CardDescription>Create a custom financial report for any date range</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="report-type">Report Type</Label>
              <Select value={selectedReportType} onValueChange={setSelectedReportType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select report type" />
                </SelectTrigger>
                <SelectContent>
                  {reportTypes.map((type) => {
                    const Icon = type.icon;
                    return (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4" />
                          {type.label}
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Start Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {startDate ? format(startDate, 'PPP') : 'Pick a date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={startDate}
                    onSelect={setStartDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2">
              <Label>End Date</Label>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-start text-left font-normal">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {endDate ? format(endDate, 'PPP') : 'Pick a date'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0">
                  <Calendar
                    mode="single"
                    selected={endDate}
                    onSelect={setEndDate}
                    initialFocus
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          <Button 
            onClick={generateReport} 
            disabled={!selectedReportType || !startDate || !endDate || generating}
            className="w-full"
          >
            {generating ? (
              <>
                <Clock className="mr-2 h-4 w-4 animate-spin" />
                Generating Report...
              </>
            ) : (
              <>
                <FileText className="mr-2 h-4 w-4" />
                Generate Report
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Recent Reports */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Reports</CardTitle>
          <CardDescription>Your generated financial reports</CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No reports generated yet</p>
              <p className="text-sm text-muted-foreground">Generate your first report using the form above</p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-3">
                    {getReportTypeIcon(report.report_type)}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{report.title}</span>
                        <Badge className={getStatusColor(report.status)}>
                          {report.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>Type: {getReportTypeLabel(report.report_type)}</span>
                        <span>Created: {new Date(report.created_at).toLocaleDateString()}</span>
                        {report.completed_at && (
                          <span>Completed: {new Date(report.completed_at).toLocaleDateString()}</span>
                        )}
                        <span>By: {report.generated_by_email}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {getStatusIcon(report.status)}
                    {report.status === 'completed' && report.file_url && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => downloadReport(report)}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Report Types Info */}
      <Card>
        <CardHeader>
          <CardTitle>Available Report Types</CardTitle>
          <CardDescription>Understanding different financial reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {reportTypes.map((type) => {
              const Icon = type.icon;
              return (
                <div key={type.value} className="flex items-start gap-3 p-3 border rounded-lg">
                  <Icon className="h-5 w-5 text-primary mt-0.5" />
                  <div className="space-y-1">
                    <span className="font-medium">{type.label}</span>
                    <p className="text-xs text-muted-foreground">
                      {type.value === 'revenue_summary' && 'Comprehensive overview of all revenue streams and key metrics'}
                      {type.value === 'subscription_analytics' && 'Detailed analysis of subscription performance and user behavior'}
                      {type.value === 'cohort_financials' && 'Financial performance metrics for cohort-based programs'}
                      {type.value === 'mentor_compensation' && 'Mentor payment tracking and compensation analysis'}
                      {type.value === 'cash_flow' && 'Cash flow analysis with projections and trends'}
                      {type.value === 'audit_report' && 'Comprehensive audit trail and compliance report'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};