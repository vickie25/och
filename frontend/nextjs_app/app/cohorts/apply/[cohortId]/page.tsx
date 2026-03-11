'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  GraduationCap, 
  ArrowLeft, 
  Users, 
  X,
  Shield,
  Calendar,
  MapPin,
  DollarSign
} from 'lucide-react';
import { apiGateway } from '@/services/apiGateway';

interface CohortDetails {
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

type ApplicantType = 'student' | 'sponsor';

export default function CohortApplicationPage() {
  const router = useRouter();
  const params = useParams();
  const cohortId = params.cohortId as string;
  
  const [cohort, setCohort] = useState<CohortDetails | null>(null);
  const [applicantType, setApplicantType] = useState<ApplicantType | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cohortId) {
      fetchCohortDetails();
    }
  }, [cohortId]);

  const fetchCohortDetails = async () => {
    try {
      setIsLoading(true);
      const cohorts = await apiGateway.get('/public/cohorts/', { skipAuth: true });
      const foundCohort = cohorts.find((c: any) => c.id === cohortId);
      
      if (foundCohort) {
        setCohort(foundCohort);
      } else {
        setError('Cohort not found');
      }
    } catch (error) {
      console.error('Failed to fetch cohort details:', error);
      setError('Failed to load cohort details');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cohort || !applicantType) return;
    
    setSubmitting(true);
    setError(null);
    
    try {
      const endpoint = applicantType === 'student'
        ? `/public/cohorts/${cohort.id}/apply/student/`
        : `/public/cohorts/${cohort.id}/apply/sponsor/`;
      
      const res = await apiGateway.post(endpoint, formData, { skipAuth: true });
      const data = res as any;
      setSuccess(data?.message || 'Application submitted successfully!');
      setFormData({});
    } catch (err: any) {
      const msg = err?.data?.error || err?.data?.detail || err?.message || 'Submission failed. Please try again.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
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

  if (error && !cohort) {
    return (
      <div className="min-h-screen bg-och-midnight text-slate-200 p-8">
        <div className="max-w-4xl mx-auto text-center py-20">
          <GraduationCap className="w-16 h-16 text-och-steel/30 mx-auto mb-4" />
          <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-4">
            Cohort Not Found
          </h1>
          <p className="text-och-steel text-lg mb-8">{error}</p>
          <button
            onClick={() => router.push('/cohorts')}
            className="px-8 py-4 bg-och-gold text-black font-black uppercase tracking-widest rounded-2xl hover:bg-och-gold/90 transition-all"
          >
            View Available Cohorts
          </button>
        </div>
      </div>
    );
  }

  if (!cohort) return null;

  return (
    <div className="min-h-screen bg-och-midnight text-slate-200">
      {/* Header */}
      <div className="bg-gradient-to-b from-och-midnight to-och-midnight/95 border-b border-och-steel/10">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <button
            onClick={() => router.push('/cohorts')}
            className="flex items-center gap-2 text-och-steel hover:text-och-gold transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm font-medium">Back to Cohorts</span>
          </button>
          
          <div className="flex flex-col lg:flex-row gap-8 items-start">
            {/* Cohort Image */}
            <div className="w-full lg:w-80 h-48 rounded-2xl overflow-hidden bg-och-gold/10 border border-och-gold/30 flex items-center justify-center">
              {cohort.profile_image ? (
                <img 
                  src={cohort.profile_image} 
                  alt={cohort.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <Shield className="w-16 h-16 text-och-gold/50" />
              )}
            </div>

            {/* Cohort Details */}
            <div className="flex-1">
              <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-4">
                {cohort.name}
              </h1>
              
              {cohort.track_name && (
                <p className="text-och-gold text-lg font-bold mb-4">
                  Track: {cohort.track_name}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="flex items-center gap-2 text-och-steel">
                  <Calendar className="w-5 h-5" />
                  <span>
                    {new Date(cohort.start_date).toLocaleDateString()} - {new Date(cohort.end_date).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-och-steel">
                  <MapPin className="w-5 h-5" />
                  <span className="capitalize">{cohort.mode}</span>
                </div>

                <div className="flex items-center gap-2 text-och-steel">
                  <Users className="w-5 h-5" />
                  <span>
                    {cohort.enrolled_count || 0} / {cohort.seat_cap} enrolled
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-och-gold" />
                  <span className="text-och-gold font-bold">
                    {cohort.currency} {cohort.enrollment_fee}
                  </span>
                </div>
              </div>

              {cohort.description && (
                <p className="text-och-steel leading-relaxed">
                  {cohort.description}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Application Section */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        {!applicantType ? (
          <div className="text-center">
            <h2 className="text-3xl font-black text-white uppercase tracking-tighter mb-8">
              How would you like to join?
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl mx-auto">
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setApplicantType('student')}
                className="p-8 bg-och-midnight/60 border border-och-steel/10 rounded-3xl hover:border-och-gold/30 transition-all group"
              >
                <GraduationCap className="w-12 h-12 text-och-gold mx-auto mb-4" />
                <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2 group-hover:text-och-gold transition-colors">
                  Apply as Student
                </h3>
                <p className="text-och-steel text-sm">
                  Join the cohort as a learner and build your cybersecurity skills
                </p>
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setApplicantType('sponsor')}
                className="p-8 bg-och-midnight/60 border border-och-steel/10 rounded-3xl hover:border-och-gold/30 transition-all group"
              >
                <Users className="w-12 h-12 text-och-gold mx-auto mb-4" />
                <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2 group-hover:text-och-gold transition-colors">
                  Join as Sponsor
                </h3>
                <p className="text-och-steel text-sm">
                  Support talent development and connect with emerging professionals
                </p>
              </motion.button>
            </div>
          </div>
        ) : (
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-3xl font-black text-white uppercase tracking-tighter">
                {applicantType === 'student' ? 'Student Application' : 'Sponsor Application'}
              </h2>
              <button
                onClick={() => {
                  setApplicantType(null);
                  setFormData({});
                  setError(null);
                  setSuccess(null);
                }}
                className="text-och-steel hover:text-och-gold transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {success ? (
              <div className="p-6 bg-emerald-500/10 border border-emerald-400/30 rounded-2xl text-emerald-300 text-center">
                <h3 className="text-xl font-bold mb-2">Application Submitted!</h3>
                <p>{success}</p>
                <button
                  onClick={() => router.push('/cohorts')}
                  className="mt-4 px-6 py-3 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all"
                >
                  View Other Cohorts
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                {error && (
                  <div className="p-4 bg-rose-500/10 border border-rose-400/30 rounded-xl text-rose-300">
                    {error}
                  </div>
                )}

                {applicantType === 'student' ? (
                  <>
                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Full Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter your full name"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        required
                        value={formData.email || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter your email address"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Phone Number
                      </label>
                      <input
                        type="tel"
                        value={formData.phone || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter your phone number"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Background & Experience
                      </label>
                      <textarea
                        value={formData.background || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, background: e.target.value }))}
                        rows={4}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Tell us about your background and relevant experience"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Motivation
                      </label>
                      <textarea
                        value={formData.motivation || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, motivation: e.target.value }))}
                        rows={4}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Why do you want to join this cohort?"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Organization Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.organization_name || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, organization_name: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter your organization name"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Contact Name *
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.contact_name || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, contact_name: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter contact person name"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Contact Email *
                      </label>
                      <input
                        type="email"
                        required
                        value={formData.contact_email || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, contact_email: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter contact email address"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Phone Number
                      </label>
                      <input
                        type="tel"
                        value={formData.phone || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="Enter contact phone number"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-bold text-white mb-2">
                        Sponsorship Goals
                      </label>
                      <textarea
                        value={formData.goals || ''}
                        onChange={(e) => setFormData(prev => ({ ...prev, goals: e.target.value }))}
                        rows={4}
                        className="w-full px-4 py-3 bg-och-midnight/80 border border-och-steel/20 rounded-xl text-white placeholder:text-och-steel/50 focus:border-och-gold/50 outline-none transition-all"
                        placeholder="What are your goals for sponsoring this cohort?"
                      />
                    </div>
                  </>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full bg-och-gold text-black font-black uppercase tracking-widest rounded-xl py-4 hover:bg-och-gold/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Submitting...' : 'Submit Application'}
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
}