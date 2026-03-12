'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BookOpen, 
  Calendar, 
  Users, 
  Trophy, 
  Clock, 
  CheckCircle, 
  PlayCircle,
  MessageSquare,
  BarChart3,
  Target,
  Video,
  FileText,
  Lab,
  Award
} from 'lucide-react';
import { apiGateway } from '@/services/apiGateway';

interface CohortDashboardProps {
  enrollmentId: string;
}

interface MaterialProgress {
  status: 'not_started' | 'in_progress' | 'completed';
  started_at?: string;
  completed_at?: string;
  time_spent_minutes: number;
}

interface Material {
  id: string;
  title: string;
  material_type: 'video' | 'article' | 'quiz' | 'assignment' | 'lab' | 'workshop';
  estimated_minutes: number;
  is_required: boolean;
  is_unlocked: boolean;
  progress_status: string;
}

interface DashboardData {
  enrollment_info: {
    id: string;
    status: string;
    seat_type: string;
    joined_at: string;
  };
  cohort_info: {
    id: string;
    name: string;
    start_date: string;
    end_date: string;
    mode: string;
    track_name: string;
  };
  progress_summary: {
    total_materials: number;
    completed: number;
    in_progress: number;
    not_started: number;
    completion_percentage: number;
    total_time_hours: number;
  };
  materials_by_day: Record<string, Material[]>;
  upcoming_events: Array<{
    id: string;
    title: string;
    type: string;
    start_ts: string;
    location: string;
    link: string;
  }>;
  mentors: Array<{
    id: string;
    name: string;
    email: string;
    role: string;
  }>;
}

export function CohortDashboard({ enrollmentId }: CohortDashboardProps) {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [selectedDay, setSelectedDay] = useState<string>('1');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, [enrollmentId]);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const data = await apiGateway.get(`/cohorts/dashboard/${enrollmentId}/`);
      setDashboardData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartMaterial = async (materialId: string) => {
    try {
      await apiGateway.post('/cohorts/materials/start/', {
        enrollment_id: enrollmentId,
        material_id: materialId
      });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      console.error('Failed to start material:', err);
    }
  };

  const handleCompleteMaterial = async (materialId: string, timeSpent: number) => {
    try {
      await apiGateway.post('/cohorts/materials/complete/', {
        enrollment_id: enrollmentId,
        material_id: materialId,
        time_spent_minutes: timeSpent
      });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      console.error('Failed to complete material:', err);
    }
  };

  const getMaterialIcon = (type: string) => {
    switch (type) {
      case 'video': return <Video className="w-5 h-5" />;
      case 'article': return <FileText className="w-5 h-5" />;
      case 'lab': return <Lab className="w-5 h-5" />;
      case 'quiz': return <Target className="w-5 h-5" />;
      default: return <BookOpen className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30';
      case 'in_progress': return 'text-amber-400 bg-amber-400/10 border-amber-400/30';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/30';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-och-gold/30 border-t-och-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-och-steel font-black uppercase tracking-widest text-sm">Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center p-8">
        <div className="text-center">
          <Trophy className="w-16 h-16 text-och-steel/30 mx-auto mb-4" />
          <h1 className="text-2xl font-black text-white uppercase tracking-tighter mb-4">
            Dashboard Error
          </h1>
          <p className="text-och-steel mb-8">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-6 py-3 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { cohort_info, progress_summary, materials_by_day, upcoming_events, mentors } = dashboardData;
  const dayNumbers = Object.keys(materials_by_day).sort((a, b) => parseInt(a) - parseInt(b));

  return (
    <div className="min-h-screen bg-och-midnight text-slate-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-och-midnight to-och-midnight/95 border-b border-och-steel/10 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h1 className="text-3xl font-black text-white uppercase tracking-tighter mb-2">
                {cohort_info.name}
              </h1>
              <div className="flex items-center gap-4 text-och-steel">
                <span className="flex items-center gap-2">
                  <Trophy className="w-4 h-4" />
                  {cohort_info.track_name}
                </span>
                <span className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  {new Date(cohort_info.start_date).toLocaleDateString()} - {new Date(cohort_info.end_date).toLocaleDateString()}
                </span>
                <span className="capitalize">{cohort_info.mode}</span>
              </div>
            </div>

            {/* Progress Overview */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-och-midnight/60 rounded-xl border border-och-steel/10">
                <div className="text-2xl font-black text-emerald-400 mb-1">
                  {progress_summary.completion_percentage.toFixed(0)}%
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Complete</div>
              </div>
              <div className="text-center p-4 bg-och-midnight/60 rounded-xl border border-och-steel/10">
                <div className="text-2xl font-black text-och-gold mb-1">
                  {progress_summary.completed}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Finished</div>
              </div>
              <div className="text-center p-4 bg-och-midnight/60 rounded-xl border border-och-steel/10">
                <div className="text-2xl font-black text-amber-400 mb-1">
                  {progress_summary.in_progress}
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">In Progress</div>
              </div>
              <div className="text-center p-4 bg-och-midnight/60 rounded-xl border border-och-steel/10">
                <div className="text-2xl font-black text-och-steel mb-1">
                  {progress_summary.total_time_hours.toFixed(1)}h
                </div>
                <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Time Spent</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Day Navigation */}
            <div className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6">
              <h2 className="text-xl font-black text-white uppercase tracking-tighter mb-4">
                Learning Materials
              </h2>
              
              {/* Day Selector */}
              <div className="flex flex-wrap gap-2 mb-6">
                {dayNumbers.map((day) => (
                  <button
                    key={day}
                    onClick={() => setSelectedDay(day)}
                    className={`px-4 py-2 rounded-xl font-bold text-sm transition-all ${
                      selectedDay === day
                        ? 'bg-och-gold text-black'
                        : 'bg-och-steel/10 text-och-steel hover:bg-och-steel/20'
                    }`}
                  >
                    Day {day}
                  </button>
                ))}
              </div>

              {/* Materials for Selected Day */}
              <div className="space-y-4">
                {materials_by_day[selectedDay]?.map((material) => (
                  <motion.div
                    key={material.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-4 rounded-xl border transition-all ${getStatusColor(material.progress_status)}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getMaterialIcon(material.material_type)}
                        <div>
                          <h3 className="font-bold text-white">{material.title}</h3>
                          <div className="flex items-center gap-4 text-sm text-och-steel">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {material.estimated_minutes}min
                            </span>
                            <span className="capitalize">{material.material_type}</span>
                            {material.is_required && (
                              <span className="px-2 py-1 bg-och-defender/20 text-och-defender text-xs rounded-lg font-bold">
                                Required
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {material.progress_status === 'not_started' && material.is_unlocked && (
                          <button
                            onClick={() => handleStartMaterial(material.id)}
                            className="px-4 py-2 bg-och-gold text-black font-bold rounded-lg hover:bg-och-gold/90 transition-all"
                          >
                            <PlayCircle className="w-4 h-4" />
                          </button>
                        )}
                        {material.progress_status === 'in_progress' && (
                          <button
                            onClick={() => handleCompleteMaterial(material.id, material.estimated_minutes)}
                            className="px-4 py-2 bg-emerald-500 text-white font-bold rounded-lg hover:bg-emerald-600 transition-all"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                        {material.progress_status === 'completed' && (
                          <div className="px-4 py-2 bg-emerald-500/20 text-emerald-400 font-bold rounded-lg">
                            <CheckCircle className="w-4 h-4" />
                          </div>
                        )}
                        {!material.is_unlocked && (
                          <div className="px-4 py-2 bg-och-steel/20 text-och-steel font-bold rounded-lg">
                            Locked
                          </div>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Upcoming Events */}
            <div className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6">
              <h3 className="text-lg font-black text-white uppercase tracking-tighter mb-4">
                Upcoming Events
              </h3>
              <div className="space-y-3">
                {upcoming_events.slice(0, 3).map((event) => (
                  <div key={event.id} className="p-3 bg-och-steel/5 rounded-xl border border-och-steel/10">
                    <h4 className="font-bold text-white text-sm">{event.title}</h4>
                    <p className="text-xs text-och-steel capitalize">{event.type}</p>
                    <p className="text-xs text-och-gold">
                      {new Date(event.start_ts).toLocaleDateString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Mentors */}
            <div className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6">
              <h3 className="text-lg font-black text-white uppercase tracking-tighter mb-4">
                Your Mentors
              </h3>
              <div className="space-y-3">
                {mentors.map((mentor) => (
                  <div key={mentor.id} className="flex items-center gap-3 p-3 bg-och-steel/5 rounded-xl border border-och-steel/10">
                    <div className="w-10 h-10 bg-och-gold/20 rounded-full flex items-center justify-center">
                      <Users className="w-5 h-5 text-och-gold" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-white text-sm">{mentor.name}</h4>
                      <p className="text-xs text-och-steel capitalize">{mentor.role} Mentor</p>
                    </div>
                    <button className="p-2 bg-och-gold/10 text-och-gold rounded-lg hover:bg-och-gold/20 transition-all">
                      <MessageSquare className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Progress Chart */}
            <div className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6">
              <h3 className="text-lg font-black text-white uppercase tracking-tighter mb-4">
                Progress Overview
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-och-steel">Completion</span>
                  <span className="text-sm font-bold text-emerald-400">
                    {progress_summary.completion_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-och-steel/20 rounded-full h-2">
                  <div 
                    className="bg-emerald-400 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${progress_summary.completion_percentage}%` }}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-lg font-black text-emerald-400">
                      {progress_summary.completed}
                    </div>
                    <div className="text-xs text-och-steel">Completed</div>
                  </div>
                  <div>
                    <div className="text-lg font-black text-amber-400">
                      {progress_summary.in_progress}
                    </div>
                    <div className="text-xs text-och-steel">In Progress</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}