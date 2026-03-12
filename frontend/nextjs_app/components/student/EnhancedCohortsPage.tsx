'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Calendar, 
  Users, 
  MapPin, 
  DollarSign, 
  Clock, 
  Trophy, 
  Star,
  CheckCircle,
  ArrowRight,
  Shield,
  Zap,
  Crown
} from 'lucide-react';
import { apiGateway } from '@/services/apiGateway';
import { useRouter } from 'next/navigation';

interface CohortData {
  id: string;
  name: string;
  description: string;
  track_name: string;
  program_name: string;
  start_date: string;
  end_date: string;
  mode: string;
  duration_weeks: number;
  seat_availability: {
    total_capacity: number;
    total_enrolled: number;
    available_seats: number;
    seat_breakdown: {
      paid: { capacity: number; enrolled: number; available: number };
      scholarship: { capacity: number; enrolled: number; available: number };
      sponsored: { capacity: number; enrolled: number; available: number };
    };
    is_full: boolean;
    waitlist_count: number;
  };
  pricing: {
    base_price: number;
    final_price: number;
    discount_amount: number;
    discount_reason: string;
    seat_type: string;
  };
  user_enrolled: boolean;
  profile_image?: string;
}

interface UserStatus {
  current_cohorts: Array<{
    enrollment_id: string;
    cohort_id: string;
    cohort_name: string;
    track_name: string;
    status: string;
    seat_type: string;
  }>;
  subscription_benefits: {
    eligible: boolean;
    reason: string;
    discount: number;
    subscription_benefit?: {
      plan_type: string;
      priority_enrollment: boolean;
      subscription_id: string;
    };
  };
  total_cohorts_completed: number;
  can_enroll_multiple: boolean;
}

export function EnhancedCohortsPage() {
  const router = useRouter();
  const [cohorts, setCohorts] = useState<CohortData[]>([]);
  const [userStatus, setUserStatus] = useState<UserStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [enrolling, setEnrolling] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeatType, setSelectedSeatType] = useState<'paid' | 'scholarship' | 'sponsored'>('paid');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [cohortsData, statusData] = await Promise.all([
        apiGateway.get('/cohorts/available/'),
        apiGateway.get('/cohorts/my-status/')
      ]);
      
      setCohorts(cohortsData.cohorts || []);
      setUserStatus(statusData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load cohorts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEnroll = async (cohortId: string) => {
    try {
      setEnrolling(cohortId);
      
      // Check eligibility first
      const eligibility = await apiGateway.post('/cohorts/check-eligibility/', {
        cohort_id: cohortId,
        seat_type: selectedSeatType
      });
      
      if (!eligibility.eligible) {
        alert('You are not eligible to enroll in this cohort.');
        return;
      }
      
      // Proceed with enrollment
      const result = await apiGateway.post('/cohorts/enroll/', {
        cohort_id: cohortId,
        seat_type: selectedSeatType,
        enrollment_type: 'self'
      });
      
      if (result.success) {
        if (result.payment_info) {
          // Redirect to payment page
          router.push(`/cohorts/payment?enrollment_id=${result.enrollment_id}`);
        } else {
          // Free enrollment successful
          alert('Enrollment successful!');
          fetchData(); // Refresh data
        }
      }
    } catch (err: any) {
      alert(err.message || 'Enrollment failed');
    } finally {
      setEnrolling(null);
    }
  };

  const getSubscriptionBadge = () => {
    if (!userStatus?.subscription_benefits?.subscription_benefit) return null;
    
    const { plan_type } = userStatus.subscription_benefits.subscription_benefit;
    const badges = {
      basic: { icon: Shield, color: 'text-blue-400 bg-blue-400/10 border-blue-400/30', label: 'Basic' },
      premium: { icon: Zap, color: 'text-purple-400 bg-purple-400/10 border-purple-400/30', label: 'Premium' },
      enterprise: { icon: Crown, color: 'text-amber-400 bg-amber-400/10 border-amber-400/30', label: 'Enterprise' }
    };
    
    const badge = badges[plan_type as keyof typeof badges];
    if (!badge) return null;
    
    const Icon = badge.icon;
    
    return (
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-lg border text-sm font-bold ${badge.color}`}>
        <Icon className="w-4 h-4" />
        {badge.label} Subscriber
      </div>
    );
  };

  const getSeatAvailabilityColor = (available: number, total: number) => {
    const percentage = (available / total) * 100;
    if (percentage > 50) return 'text-emerald-400';
    if (percentage > 20) return 'text-amber-400';
    return 'text-red-400';
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
      {/* Background Effects */}
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(10,14,26,1),_transparent_55%),radial-gradient(circle_at_top_left,_rgba(245,158,11,0.12),_transparent_55%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.12),_transparent_55%)]" />
      <div className="pointer-events-none fixed inset-0 -z-10 opacity-[0.03]" style={{backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '50px 50px'}} />

      {/* Header */}
      <div className="bg-gradient-to-b from-och-midnight to-och-midnight/95 border-b border-och-steel/10 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-4">
                Available Cohorts
              </h1>
              <p className="text-och-steel text-lg">
                Join structured learning programs with dedicated mentorship and peer collaboration.
              </p>
            </div>
            
            {/* User Status */}
            {userStatus && (
              <div className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl p-6">
                <div className="flex items-center gap-4 mb-4">
                  <Trophy className="w-6 h-6 text-och-gold" />
                  <div>
                    <h3 className="font-black text-white uppercase tracking-tighter">Your Status</h3>
                    {getSubscriptionBadge()}
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-black text-och-gold">
                      {userStatus.current_cohorts.length}
                    </div>
                    <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Active</div>
                  </div>
                  <div>
                    <div className="text-2xl font-black text-emerald-400">
                      {userStatus.total_cohorts_completed}
                    </div>
                    <div className="text-xs text-och-steel uppercase tracking-widest font-bold">Completed</div>
                  </div>
                </div>
                
                {userStatus.subscription_benefits.discount > 0 && (
                  <div className="mt-4 p-3 bg-och-gold/10 border border-och-gold/30 rounded-xl">
                    <p className="text-och-gold text-sm font-bold">
                      🎉 {Math.round(userStatus.subscription_benefits.discount * 100)}% discount on all cohorts!
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="max-w-7xl mx-auto p-6">
          <div className="bg-red-500/10 border border-red-400/30 rounded-2xl p-6 text-center">
            <p className="text-red-300">{error}</p>
            <button
              onClick={fetchData}
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
              No Cohorts Available
            </h2>
            <p className="text-och-steel">Check back soon for new cohort announcements.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {cohorts.map((cohort) => (
              <motion.div
                key={cohort.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-och-midnight/60 border border-och-steel/10 rounded-2xl overflow-hidden hover:border-och-gold/30 transition-all group"
              >
                {/* Cohort Image */}
                <div className="h-48 bg-och-gold/10 border-b border-och-steel/10 flex items-center justify-center relative overflow-hidden">
                  {cohort.profile_image ? (
                    <img 
                      src={cohort.profile_image} 
                      alt={cohort.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <Shield className="w-16 h-16 text-och-gold/50" />
                  )}
                  
                  {/* Status Badges */}
                  <div className="absolute top-4 left-4 flex flex-col gap-2">
                    {cohort.user_enrolled && (
                      <div className="px-3 py-1 bg-emerald-500/90 text-white text-xs font-bold rounded-lg">
                        Enrolled
                      </div>
                    )}
                    {cohort.seat_availability.is_full && (
                      <div className="px-3 py-1 bg-red-500/90 text-white text-xs font-bold rounded-lg">
                        Full
                      </div>
                    )}
                  </div>
                  
                  {/* Pricing Badge */}
                  <div className="absolute top-4 right-4">
                    <div className="px-3 py-1 bg-och-midnight/90 border border-och-gold/30 text-och-gold text-sm font-bold rounded-lg">
                      ${cohort.pricing.final_price}
                      {cohort.pricing.discount_amount > 0 && (
                        <span className="ml-2 text-xs text-och-steel line-through">
                          ${cohort.pricing.base_price}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="p-6">
                  {/* Header */}
                  <div className="mb-4">
                    <h3 className="text-xl font-black text-white uppercase tracking-tighter mb-2">
                      {cohort.name}
                    </h3>
                    <div className="flex items-center gap-2 text-och-gold text-sm font-bold">
                      <Trophy className="w-4 h-4" />
                      {cohort.track_name}
                    </div>
                  </div>

                  {/* Description */}
                  {cohort.description && (
                    <p className="text-och-steel text-sm mb-4 line-clamp-2">
                      {cohort.description}
                    </p>
                  )}

                  {/* Details Grid */}
                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div className="flex items-center gap-2 text-och-steel">
                      <Calendar className="w-4 h-4" />
                      <span>{new Date(cohort.start_date).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2 text-och-steel">
                      <Clock className="w-4 h-4" />
                      <span>{cohort.duration_weeks} weeks</span>
                    </div>
                    <div className="flex items-center gap-2 text-och-steel">
                      <MapPin className="w-4 h-4" />
                      <span className="capitalize">{cohort.mode}</span>
                    </div>
                    <div className={`flex items-center gap-2 ${getSeatAvailabilityColor(cohort.seat_availability.available_seats, cohort.seat_availability.total_capacity)}`}>
                      <Users className="w-4 h-4" />
                      <span>{cohort.seat_availability.available_seats} seats left</span>
                    </div>
                  </div>

                  {/* Pricing Info */}
                  {cohort.pricing.discount_amount > 0 && (
                    <div className="mb-4 p-3 bg-och-gold/10 border border-och-gold/30 rounded-xl">
                      <p className="text-och-gold text-sm font-bold">
                        💰 Save ${cohort.pricing.discount_amount.toFixed(2)} - {cohort.pricing.discount_reason}
                      </p>
                    </div>
                  )}

                  {/* Seat Availability */}
                  <div className="mb-4 p-3 bg-och-steel/5 rounded-xl">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-bold text-och-steel uppercase tracking-widest">Seat Availability</span>
                      <span className="text-xs text-och-steel">
                        {cohort.seat_availability.total_enrolled}/{cohort.seat_availability.total_capacity}
                      </span>
                    </div>
                    <div className="w-full bg-och-steel/20 rounded-full h-2">
                      <div 
                        className="bg-och-gold h-2 rounded-full transition-all duration-500"
                        style={{ 
                          width: `${(cohort.seat_availability.total_enrolled / cohort.seat_availability.total_capacity) * 100}%` 
                        }}
                      />
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="space-y-3">
                    {cohort.user_enrolled ? (
                      <button
                        onClick={() => router.push(`/student/cohorts/${cohort.id}`)}
                        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-emerald-500/20 text-emerald-400 border border-emerald-400/30 font-bold rounded-xl hover:bg-emerald-500/30 transition-all"
                      >
                        <CheckCircle className="w-4 h-4" />
                        View Dashboard
                      </button>
                    ) : cohort.seat_availability.is_full ? (
                      <button
                        disabled
                        className="w-full px-6 py-3 bg-och-steel/20 text-och-steel font-bold rounded-xl cursor-not-allowed"
                      >
                        Cohort Full
                        {cohort.seat_availability.waitlist_count > 0 && (
                          <span className="ml-2 text-xs">
                            ({cohort.seat_availability.waitlist_count} on waitlist)
                          </span>
                        )}
                      </button>
                    ) : (
                      <button
                        onClick={() => handleEnroll(cohort.id)}
                        disabled={enrolling === cohort.id}
                        className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-och-gold text-black font-black uppercase tracking-widest rounded-xl hover:bg-och-gold/90 transition-all disabled:opacity-50"
                      >
                        {enrolling === cohort.id ? (
                          <>
                            <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                            Enrolling...
                          </>
                        ) : (
                          <>
                            Enroll Now
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    )}
                    
                    <button
                      onClick={() => router.push(`/cohorts/apply/${cohort.id}`)}
                      className="w-full px-6 py-3 bg-och-steel/10 text-och-steel font-bold rounded-xl hover:bg-och-steel/20 transition-all"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}