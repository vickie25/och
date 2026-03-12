'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Plus, 
  Settings, 
  Users, 
  BarChart3, 
  Calendar,
  BookOpen,
  Trophy,
  Target,
  Clock
} from 'lucide-react';
import { ModuleManagement } from '@/components/director/ModuleManagement';
import { apiGateway } from '@/services/apiGateway';

interface Cohort {
  id: string;
  name: string;
  track_name: string;
  start_date: string;
  end_date: string;
  status: string;
  seat_cap: number;
  enrolled_count: number;
  completion_rate: number;
}

export default function DirectorCohortManagementPage() {
  const [cohorts, setCohorts] = useState<Cohort[]>([]);
  const [selectedCohort, setSelectedCohort] = useState<Cohort | null>(null);
  const [showModuleManagement, setShowModuleManagement] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCohorts();
  }, []);

  const fetchCohorts = async () => {
    try {
      setIsLoading(true);
      // This would be a director-specific endpoint
      const response = await apiGateway.get('/director/cohorts/');
      setCohorts(response.cohorts || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load cohorts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageModules = (cohort: Cohort) => {
    setSelectedCohort(cohort);
    setShowModuleManagement(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/30';
      case 'running': return 'text-blue-400 bg-blue-400/10 border-blue-400/30';
      case 'draft': return 'text-amber-400 bg-amber-400/10 border-amber-400/30';
      case 'closed': return 'text-slate-400 bg-slate-400/10 border-slate-400/30';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/30';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-och-gold/30 border-t-och-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-och-steel font-black uppercase tracking-widest text-sm">Loading Cohorts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-och-midnight text-slate-200">
      {/* Header */}
      <div className="bg-gradient-to-b from-och-midnight to-och-midnight/95 border-b border-och-steel/10 p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-4">
            Cohort Management
          </h1>
          <p className="text-och-steel text-lg">
            Manage cohort content, modules, and student progress.
          </p>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="max-w-7xl mx-auto p-6">
          <div className="bg-red-500/10 border border-red-400/30 rounded-2xl p-6 text-center">
            <p className="text-red-300">{error}</p>
            <button
              onClick={fetchCohorts}
              className="mt-4 px-6 py-3 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Cohorts Grid */}
      <div className="max-w-7xl mx-auto p-6">
        {cohorts.length === 0 ? (
          <div className="text-center py-20">
            <Trophy className="w-16 h-16 text-och-steel/30 mx-auto mb-4" />
            <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-4">
              No Cohorts Found
            </h2>
            <p className="text-och-steel">Create your first cohort to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {cohorts.map((cohort) => (
              <motion.div
                key={cohort.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6 hover:border-och-gold/30 transition-all"
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-xl font-black text-white uppercase tracking-tighter mb-2">
                      {cohort.name}
                    </h3>
                    <div className="flex items-center gap-2 text-och-gold text-sm font-bold">
                      <Trophy className="w-4 h-4" />
                      {cohort.track_name}
                    </div>
                  </div>
                  
                  <div className={`px-3 py-1 rounded-lg border text-sm font-bold ${getStatusColor(cohort.status)}`}>
                    {cohort.status}
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center p-3 bg-och-steel/5 rounded-xl">
                    <div className="text-lg font-black text-och-gold">
                      {cohort.enrolled_count}/{cohort.seat_cap}
                    </div>
                    <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Enrolled</div>
                  </div>
                  <div className="text-center p-3 bg-och-steel/5 rounded-xl">
                    <div className="text-lg font-black text-emerald-400">
                      {cohort.completion_rate}%
                    </div>
                    <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Complete</div>
                  </div>
                </div>

                {/* Timeline */}
                <div className="mb-6 p-3 bg-och-steel/5 rounded-xl">
                  <div className="flex items-center gap-2 text-och-steel text-sm mb-2">
                    <Calendar className="w-4 h-4" />
                    <span>
                      {new Date(cohort.start_date).toLocaleDateString()} - {new Date(cohort.end_date).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="w-full bg-och-steel/20 rounded-full h-2">
                    <div 
                      className="bg-och-gold h-2 rounded-full transition-all duration-500"
                      style={{ width: `${cohort.completion_rate}%` }}
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="space-y-3">
                  <button
                    onClick={() => handleManageModules(cohort)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all"
                  >
                    <BookOpen className="w-4 h-4" />
                    Manage Modules
                  </button>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <button className="flex items-center justify-center gap-2 px-4 py-2 bg-och-mint/20 text-och-mint border border-och-mint/30 font-bold rounded-xl hover:bg-och-mint/30 transition-all">
                      <Users className="w-4 h-4" />
                      Students
                    </button>
                    <button className="flex items-center justify-center gap-2 px-4 py-2 bg-och-defender/20 text-och-defender border border-och-defender/30 font-bold rounded-xl hover:bg-och-defender/30 transition-all">
                      <BarChart3 className="w-4 h-4" />
                      Analytics
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Module Management Modal */}
      {showModuleManagement && selectedCohort && (
        <ModuleManagement
          cohortId={selectedCohort.id}
          cohortName={selectedCohort.name}
          onClose={() => {
            setShowModuleManagement(false);
            setSelectedCohort(null);
          }}
        />
      )}
    </div>
  );
}