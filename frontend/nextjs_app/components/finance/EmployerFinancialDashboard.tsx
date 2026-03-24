import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Building, 
  Briefcase, 
  Users, 
  Eye,
  Heart,
  UserCheck,
  Mail,
  TrendingUp,
  Calendar,
  AlertTriangle
} from 'lucide-react';

interface EmployerDashboardProps {
  userId: string;
}

interface Employer {
  company_name: string;
  sector: string;
}

interface JobPosting {
  title: string;
  applications_count: number;
  posted_at: string;
}

interface Interaction {
  action: string;
  candidate_email: string;
  created_at: string;
}

export const EmployerFinancialDashboard: React.FC<EmployerDashboardProps> = ({ userId }) => {
  const [dashboardData, setDashboardData] = useState<{
    employer: Employer;
    job_postings: JobPosting[];
    recent_interactions: Interaction[];
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/finance/dashboard/employer/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'view':
        return <Eye className="h-4 w-4 text-blue-600" />;
      case 'favorite':
        return <Heart className="h-4 w-4 text-red-600" />;
      case 'shortlist':
        return <UserCheck className="h-4 w-4 text-green-600" />;
      case 'contact_request':
        return <Mail className="h-4 w-4 text-purple-600" />;
      default:
        return <Eye className="h-4 w-4 text-gray-600" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'view': return 'text-blue-600 bg-blue-50';
      case 'favorite': return 'text-red-600 bg-red-50';
      case 'shortlist': return 'text-green-600 bg-green-50';
      case 'contact_request': return 'text-purple-600 bg-purple-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const formatActionLabel = (action: string) => {
    switch (action.toLowerCase()) {
      case 'view': return 'Viewed';
      case 'favorite': return 'Favorited';
      case 'shortlist': return 'Shortlisted';
      case 'contact_request': return 'Contact Requested';
      default: return action;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load dashboard data</AlertDescription>
      </Alert>
    );
  }

  const { employer, job_postings, recent_interactions } = dashboardData;
  const totalApplications = job_postings.reduce((sum, job) => sum + job.applications_count, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Employer Dashboard</h1>
        <p className="text-muted-foreground">
          Talent acquisition overview for {employer.company_name}
        </p>
      </div>

      {/* Company Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Company Profile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <span className="text-sm text-muted-foreground">Company Name</span>
              <div className="font-medium">{employer.company_name}</div>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Industry Sector</span>
              <div className="font-medium">{employer.sector || 'Not specified'}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Job Postings</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{job_postings.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Applications</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalApplications}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Recent Interactions</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recent_interactions.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Applications/Job</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {job_postings.length > 0 ? Math.round(totalApplications / job_postings.length) : 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Active Job Postings */}
        {job_postings.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Active Job Postings</CardTitle>
              <CardDescription>Your current job opportunities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {job_postings.map((job, index) => (
                  <div key={index} className="space-y-2 p-3 border rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{job.title}</span>
                      <Badge variant="outline">
                        {job.applications_count} applications
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Posted: {new Date(job.posted_at).toLocaleDateString()}
                      </span>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        View Applications
                      </Button>
                      <Button variant="ghost" size="sm">
                        Edit Posting
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Recent Talent Interactions */}
        {recent_interactions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recent Talent Interactions</CardTitle>
              <CardDescription>Your latest candidate activities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recent_interactions.map((interaction, index) => (
                  <div key={index} className="flex items-center gap-3 p-3 border rounded-lg">
                    {getActionIcon(interaction.action)}
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {interaction.candidate_email}
                        </span>
                        <Badge className={getActionColor(interaction.action)}>
                          {formatActionLabel(interaction.action)}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {new Date(interaction.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Empty States */}
      {job_postings.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>No Active Job Postings</CardTitle>
            <CardDescription>Start attracting talent by posting your first job</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-6">
              <Briefcase className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                You haven't posted any jobs yet. Create your first job posting to start finding qualified candidates.
              </p>
              <Button>
                Post Your First Job
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {recent_interactions.length === 0 && job_postings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>No Recent Interactions</CardTitle>
            <CardDescription>Start exploring our talent marketplace</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-6">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground mb-4">
                Browse our talent marketplace to discover qualified candidates for your open positions.
              </p>
              <Button>
                Browse Talent
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-4">
            <Button variant="outline" className="flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              Post New Job
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              Browse Talent
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Heart className="h-4 w-4" />
              View Favorites
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <UserCheck className="h-4 w-4" />
              Shortlisted Candidates
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Marketplace Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Marketplace Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
              <div>
                <p className="text-sm font-medium">Optimize Your Job Postings</p>
                <p className="text-xs text-muted-foreground">
                  Include specific skills and requirements to attract the right candidates
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-green-500 mt-2" />
              <div>
                <p className="text-sm font-medium">Engage with Talent</p>
                <p className="text-xs text-muted-foreground">
                  View profiles, favorite candidates, and send contact requests to build your pipeline
                </p>
              </div>
            </div>
            
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 rounded-full bg-purple-500 mt-2" />
              <div>
                <p className="text-sm font-medium">Track Your Success</p>
                <p className="text-xs text-muted-foreground">
                  Monitor application rates and candidate quality to refine your hiring strategy
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};