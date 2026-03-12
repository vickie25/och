'use client';

import { useParams } from 'next/navigation';
import { CohortDashboard } from '@/components/student/CohortDashboard';

export default function StudentCohortDashboardPage() {
  const params = useParams();
  const enrollmentId = params.enrollmentId as string;

  if (!enrollmentId) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-black text-white uppercase tracking-tighter mb-4">
            Invalid Enrollment
          </h1>
          <p className="text-och-steel">No enrollment ID provided.</p>
        </div>
      </div>
    );
  }

  return <CohortDashboard enrollmentId={enrollmentId} />;
}