'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';
import { apiGateway } from '@/services/apiGateway';
import { ArrowLeft, Calendar, Loader2 } from 'lucide-react';

interface MyCohortApplication {
  id: string;
  cohort_id: string;
  cohort_name?: string | null;
  applicant_type: string;
  status: string;
  created_at?: string | null;
}

export default function StudentCohortApplicationsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  const [applications, setApplications] = useState<MyCohortApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const focusedCohortId = searchParams.get('cohortId');

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await apiGateway.get<MyCohortApplication[]>('/public/my-applications/');
        setApplications((res as any) || []);
      } catch (err: any) {
        setError(err?.data?.error || 'Failed to load applications');
      } finally {
        setLoading(false);
      }
    };
    if (user) {
      load();
    } else {
      setLoading(false);
    }
  }, [user]);

  const filteredApps = focusedCohortId
    ? applications.filter((a) => a.cohort_id === focusedCohortId)
    : applications;

  return (
    <div className="min-h-screen bg-och-midnight text-slate-200 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <button
          onClick={() => router.push('/dashboard/student/cohorts')}
          className="inline-flex items-center gap-2 text-och-steel hover:text-och-gold transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Cohorts
        </button>

        <div>
          <h1 className="text-3xl font-black text-white uppercase tracking-tighter">
            Cohort Applications
          </h1>
          <p className="text-och-steel text-sm mt-2">
            Track the status of your cohort applications.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-och-gold animate-spin" />
          </div>
        ) : error ? (
          <Card className="p-6 bg-och-midnight/60 border border-rose-500/40">
            <p className="text-rose-300 text-sm">{error}</p>
          </Card>
        ) : filteredApps.length === 0 ? (
          <Card className="p-6 bg-och-midnight/60 border border-och-steel/20">
            <p className="text-sm text-och-steel">
              You have not submitted any cohort applications yet.
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredApps.map((app) => (
              <Card
                key={app.id}
                className="p-5 bg-och-midnight/60 border border-och-steel/20 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
              >
                <div>
                  <h2 className="text-lg font-bold text-white">
                    {app.cohort_name || 'Cohort'}
                  </h2>
                  <div className="flex items-center gap-3 mt-1 text-xs text-och-steel">
                    <span className="uppercase tracking-widest font-black">
                      {app.applicant_type}
                    </span>
                    {app.created_at && (
                      <span className="inline-flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        Applied{' '}
                        {new Date(app.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-start sm:items-end gap-2">
                  <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest border border-och-steel/40 text-och-steel">
                    Status: {app.status}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

