/**
 * Cohorts Dashboard - Main cohort learning hub
 */

'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  GraduationCap, 
  Calendar, 
  Users, 
  BookOpen, 
  Award,
  TrendingUp,
  Clock,
  Target,
  MessageSquare,
  FileText,
  ArrowRight,
  MapPin,
  DollarSign,
  Shield
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { useAuth } from '@/hooks/useAuth';
import { apiGateway } from '@/services/apiGateway';
import clsx from 'clsx';

interface CohortEnrollment {
  id: string;
  cohort: {
    id: string;
    name: string;
    start_date: string;
    end_date: string;
    status: string;
  };
  status: string;
  payment_status: string;
}

interface CohortProgress {
  total_materials: number;
  completed: number;
  completion_percentage: number;
  total_time_hours: number;
}

interface CohortGrade {
  overall_score: number;
  letter_grade: string;
  rank: number | null;
}

interface AvailableCohort {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  mode: string;
  seat_cap: number;
  enrolled_count: number;
  enrollment_fee: number;
  currency: string;
  track_name: string;
  description?: string;
  profile_image?: string;
}

export default function CohortsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [enrollment, setEnrollment] = useState<CohortEnrollment | null>(null);
  const [progress, setProgress] = useState<CohortProgress | null>(null);
  const [grade, setGrade] = useState<CohortGrade | null>(null);
  const [availableCohorts, setAvailableCohorts] = useState<AvailableCohort[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCohortData();
  }, []);

  const fetchCohortData = async () => {
    try {
      setIsLoading(true);
      
      // Fetch user's cohort enrollment
      const enrollmentRes = await apiGateway.get('/programs/cohorts/my-enrollment');
      if (enrollmentRes?.enrollment) {
        setEnrollment(enrollmentRes.enrollment);
        
        // Fetch progress
        const progressRes = await apiGateway.get(
          `/cohorts/materials/progress?enrollment_id=${enrollmentRes.enrollment.id}`
        );
        setProgress(progressRes);
        
        // Fetch grades
        const gradeRes = await apiGateway.get(
          `/cohorts/grades?enrollment_id=${enrollmentRes.enrollment.id}`
        );
        setGrade(gradeRes);
      } else {
        // If not enrolled, fetch available cohorts
        const cohortsRes = await apiGateway.get('/public/cohorts/', { skipAuth: true });
        setAvailableCohorts(cohortsRes || []);
      }
    } catch (error) {
      console.error('Failed to fetch cohort data:', error);
      // If enrollment fetch fails, try to fetch available cohorts
      try {
        const cohortsRes = await apiGateway.get('/public/cohorts/', { skipAuth: true });
        setAvailableCohorts(cohortsRes || []);
      } catch (cohortError) {
        console.error('Failed to fetch available cohorts:', cohortError);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleApply = (cohortId: string) => {
    router.push(`/cohorts/apply/${cohortId}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-och-gold/30 border-t-och-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-och-steel font-black uppercase tracking-widest text-sm">Loading Cohort...</p>
        </div>
      </div>
    );
  }

  if (!enrollment) {
    return (
      <div className="min-h-screen bg-och-midnight text-slate-200 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-12">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 rounded-2xl bg-och-gold/10 border border-och-gold/30 flex items-center justify-center">
                <GraduationCap className="w-8 h-8 text-och-gold" />
              </div>
              <div>
                <h1 className="text-5xl font-black text-white uppercase tracking-tighter">
                  Available Cohorts
                </h1>
                <p className="text-och-steel text-lg mt-2">
                  Join a structured, time-bound learning experience with dedicated mentorship
                </p>
              </div>
            </div>
          </div>

          {/* Available Cohorts */}
          {availableCohorts.length === 0 ? (
            <div className="text-center py-20">
              <GraduationCap className="w-16 h-16 text-och-steel/30 mx-auto mb-4" />
              <h3 className="text-2xl font-black text-white uppercase tracking-tighter mb-2">
                No Cohorts Available
              </h3>
              <p className="text-och-steel mb-8">
                Check back soon for upcoming cohorts or contact support for more information.
              </p>
              <button
                onClick={() => router.push('/support')}
                className="px-8 py-4 bg-och-midnight border border-och-steel/20 text-white font-black uppercase tracking-widest rounded-2xl hover:bg-och-steel/10 transition-all"
              >
                Contact Support
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {availableCohorts.map((cohort, index) => (
                <motion.div
                  key={cohort.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="bg-och-midnight/60 border border-och-steel/10 rounded-3xl p-6 hover:border-och-gold/30 transition-all group"
                >
                  {/* Cohort Image */}
                  {cohort.profile_image ? (
                    <div className="w-full h-40 rounded-2xl overflow-hidden mb-4">
                      <img 
                        src={cohort.profile_image} 
                        alt={cohort.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <div className="w-full h-40 rounded-2xl bg-och-gold/10 border border-och-gold/30 flex items-center justify-center mb-4">
                      <Shield className="w-16 h-16 text-och-gold/50" />
                    </div>
                  )}

                  {/* Cohort Info */}
                  <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2 group-hover:text-och-gold transition-colors">
                    {cohort.name}
                  </h3>

                  {cohort.track_name && (
                    <p className="text-sm text-och-steel mb-4">
                      Track: {cohort.track_name}
                    </p>
                  )}

                  {/* Details */}
                  <div className="space-y-3 mb-6">
                    <div className="flex items-center gap-2 text-sm text-och-steel">
                      <Calendar className="w-4 h-4" />
                      <span>
                        {new Date(cohort.start_date).toLocaleDateString()} - {new Date(cohort.end_date).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-och-steel">
                      <MapPin className="w-4 h-4" />
                      <span className="capitalize">{cohort.mode}</span>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-och-steel">
                      <Users className="w-4 h-4" />
                      <span>
                        {cohort.enrolled_count || 0} / {cohort.seat_cap} enrolled
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <DollarSign className="w-4 h-4 text-och-gold" />
                      <span className="text-och-gold font-bold">
                        {cohort.currency} {cohort.enrollment_fee}
                      </span>
                    </div>
                  </div>

                  {/* Apply Button */}
                  <button
                    onClick={() => handleApply(cohort.id)}
                    className="w-full bg-och-gold text-black font-black uppercase tracking-widest rounded-xl py-3 hover:bg-och-gold/90 transition-all flex items-center justify-center gap-2 group-hover:gap-3"
                  >
                    Apply Now
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  const cohort = enrollment.cohort;
  const quickActions = [
    {
      label: 'Learning Materials',
      icon: BookOpen,
      href: `/dashboard/student/cohorts/${cohort.id}/materials`,
      color: 'och-mint'
    },
    {
      label: 'Missions',
      icon: Target,
      href: `/dashboard/student/cohorts/${cohort.id}/missions`,
      color: 'och-defender'
    },
    {
      label: 'Exams',
      icon: FileText,
      href: `/dashboard/student/cohorts/${cohort.id}/exams`,
      color: 'och-orange'
    },
    {
      label: 'Grades',
      icon: Award,
      href: `/dashboard/student/cohorts/${cohort.id}/grades`,
      color: 'och-gold'
    },
    {
      label: 'Peers',
      icon: Users,
      href: `/dashboard/student/cohorts/${cohort.id}/peers`,
      color: 'och-grc'
    },
    {
      label: 'Mentors',
      icon: MessageSquare,
      href: `/dashboard/student/cohorts/${cohort.id}/mentors`,
      color: 'och-offensive'
    }
  ];

  return (
    <div className="min-h-screen bg-och-midnight text-slate-200 p-8">
      <div className="max-w-[1600px] mx-auto">
        
        {/* HEADER */}
        <div className="mb-12">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-2xl bg-och-gold/10 border border-och-gold/30 flex items-center justify-center">
              <GraduationCap className="w-8 h-8 text-och-gold" />
            </div>
            <div>
              <h1 className="text-5xl font-black text-white uppercase tracking-tighter">
                {cohort.name}
              </h1>
              <div className="flex items-center gap-4 mt-2">
                <Badge variant="mint" className="text-xs font-black">
                  {cohort.status.toUpperCase()}
                </Badge>
                <span className="text-och-steel text-sm font-bold">
                  {new Date(cohort.start_date).toLocaleDateString()} - {new Date(cohort.end_date).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* STATS GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Progress Card */}
          <Card className="p-6 bg-och-midnight/60 border border-och-steel/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-black text-och-steel uppercase tracking-widest">
                Overall Progress
              </h3>
              <TrendingUp className="w-5 h-5 text-och-mint" />
            </div>
            <div className="mb-4">
              <div className="text-4xl font-black text-white mb-2">
                {progress?.completion_percentage.toFixed(0) || 0}%
              </div>
              <ProgressBar
                value={progress?.completion_percentage || 0}
                max={100}
                variant="mint"
                className="h-2"
              />
            </div>
            <div className="text-sm text-och-steel">
              {progress?.completed || 0} of {progress?.total_materials || 0} materials completed
            </div>
          </Card>

          {/* Grade Card */}
          <Card className="p-6 bg-och-midnight/60 border border-och-steel/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-black text-och-steel uppercase tracking-widest">
                Current Grade
              </h3>
              <Award className="w-5 h-5 text-och-gold" />
            </div>
            <div className="mb-4">
              <div className="text-4xl font-black text-white mb-2">
                {grade?.letter_grade || 'N/A'}
              </div>
              <div className="text-2xl font-bold text-och-gold">
                {grade?.overall_score.toFixed(1) || 0}%
              </div>
            </div>
            {grade?.rank && (
              <div className="text-sm text-och-steel">
                Rank #{grade.rank} in cohort
              </div>
            )}
          </Card>

          {/* Time Card */}
          <Card className="p-6 bg-och-midnight/60 border border-och-steel/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-black text-och-steel uppercase tracking-widest">
                Time Invested
              </h3>
              <Clock className="w-5 h-5 text-och-defender" />
            </div>
            <div className="mb-4">
              <div className="text-4xl font-black text-white mb-2">
                {progress?.total_time_hours.toFixed(1) || 0}
              </div>
              <div className="text-sm text-och-steel">hours</div>
            </div>
          </Card>
        </div>

        {/* QUICK ACTIONS */}
        <div className="mb-12">
          <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-6">
            Quick Access
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {quickActions.map((action) => (
              <motion.button
                key={action.label}
                onClick={() => router.push(action.href)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={clsx(
                  "p-6 rounded-2xl border border-och-steel/10 bg-och-midnight/60",
                  "hover:border-och-gold/30 transition-all group"
                )}
              >
                <action.icon className={`w-8 h-8 text-${action.color} mb-3 mx-auto`} />
                <div className="text-xs font-black text-white uppercase tracking-widest text-center">
                  {action.label}
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* UPCOMING EVENTS */}
        <div>
          <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-6">
            Upcoming Events
          </h2>
          <Card className="p-6 bg-och-midnight/60 border border-och-steel/10">
            <div className="flex items-center gap-4 text-och-steel">
              <Calendar className="w-6 h-6" />
              <span className="text-sm">No upcoming events scheduled</span>
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
