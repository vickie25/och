/**
 * Redesigned Student Dashboard Hub
 * Compact, community-centered, track-themed interface
 * Syncs with real backend data for curriculum and missions
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Zap, 
  Target, 
  TrendingUp, 
  MessageSquare, 
  Users, 
  Star,
  CheckCircle2,
  ChevronRight,
  Flame,
  LineChart,
  ArrowUpRight,
  PlayCircle,
  BookOpen,
  Award,
  Sparkles,
  Trophy,
  Bell,
  Calendar,
  Rocket,
  Activity,
  Brain,
  MessageCircle,
  UserCircle,
  ExternalLink,
  GraduationCap,
  Lock,
  FileText,
  Clock,
  Crown,
  Zap as ZapIcon,
} from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/hooks/useAuth';
import { lazy, Suspense } from 'react';
import { fastapiClient } from '@/services/fastapiClient';

// Lazy load CoachingNudge for better performance
const CoachingNudge = lazy(() => import('@/components/coaching/CoachingNudge').then(module => ({ default: module.CoachingNudge })));
import { apiGateway } from '@/services/apiGateway';
import { programsClient } from '@/services/programsClient';
import { communityClient } from '@/services/communityClient';
import { foundationsClient } from '@/services/foundationsClient';
import { curriculumClient } from '@/services/curriculumClient';
import clsx from 'clsx';
import { useRouter } from 'next/navigation';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import type { FoundationsStatus, FoundationsModule } from '@/services/foundationsClient';
import type { CurriculumTrack, UserTrackProgress, Lesson } from '@/services/types/curriculum';

/** Resolve relative/media URLs to absolute (fixes "localhost refused to connect" when content_url is /media/...) */
function resolveContentUrl(url: string | undefined): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const base = typeof process !== 'undefined' ? process.env.NEXT_PUBLIC_DJANGO_API_URL || '' : '';
  return `${base}${url.startsWith('/') ? '' : '/'}${url}`;
}

/** YouTube/Vimeo embed URL for iframe; null for direct video files (use <video> with resolveContentUrl). */
function getEmbedUrl(url: string): string | null {
  if (!url) return null;
  const ytMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  if (ytMatch) {
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    return `https://www.youtube.com/embed/${ytMatch[1]}?enablejsapi=1&origin=${encodeURIComponent(origin)}`;
  }
  const vimeoMatch = url.match(/vimeo\.com\/(\d+)/);
  if (vimeoMatch) return `https://player.vimeo.com/video/${vimeoMatch[1]}`;
  return null;
}

// Track-specific color themes
const trackThemes: Record<string, {
  primary: string;
  secondary: string;
  accent: string;
  gradient: string;
  icon: React.ReactNode;
  name: string;
  description: string;
}> = {
  defender: {
    primary: 'indigo',
    secondary: 'blue',
    accent: 'indigo',
    gradient: 'from-indigo-500/20 via-blue-500/10 to-indigo-500/20',
    icon: <Shield className="w-6 h-6" />,
    name: 'Cyber Defender',
    description: 'Protect systems and networks from cyber threats',
  },
  offensive: {
    primary: 'red',
    secondary: 'orange',
    accent: 'red',
    gradient: 'from-red-500/20 via-orange-500/10 to-red-500/20',
    icon: <Zap className="w-6 h-6" />,
    name: 'Offensive Security',
    description: 'Ethical hacking and penetration testing',
  },
  grc: {
    primary: 'emerald',
    secondary: 'teal',
    accent: 'emerald',
    gradient: 'from-emerald-500/20 via-teal-500/10 to-emerald-500/20',
    icon: <FileText className="w-6 h-6" />,
    name: 'GRC & Risk',
    description: 'Governance, Risk, and Compliance',
  },
  innovation: {
    primary: 'cyan',
    secondary: 'sky',
    accent: 'cyan',
    gradient: 'from-cyan-500/20 via-sky-500/10 to-cyan-500/20',
    icon: <Rocket className="w-6 h-6" />,
    name: 'Security Innovation',
    description: 'Cloud security, DevSecOps, and future systems',
  },
  leadership: {
    primary: 'och-gold',
    secondary: 'amber',
    accent: 'och-gold',
    gradient: 'from-och-gold/20 via-amber-500/10 to-och-gold/20',
    icon: <Award className="w-6 h-6" />,
    name: 'VIP Leadership',
    description: 'Value, Impact, and Purpose-driven leadership',
  },
};

export function StudentDashboardHub() {
  const router = useRouter();
  const { user } = useAuth();
  const prefersReducedMotion = useReducedMotion();
  
  const [activeTab, setActiveTab] = useState<'overview' | 'progress' | 'community'>('overview');
  const [showNotifications, setShowNotifications] = useState(false);
  const [profiledTrack, setProfiledTrack] = useState<string | null>(null);
  const [profilingResults, setProfilingResults] = useState<any>(null);
  const [loadingTrack, setLoadingTrack] = useState(true);
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [foundationsStatus, setFoundationsStatus] = useState<FoundationsStatus | null>(null);
  const [curriculumProgress, setCurriculumProgress] = useState<UserTrackProgress | null>(null);
  const [loadingFoundations, setLoadingFoundations] = useState(true);
  const [foundationLessonsByModule, setFoundationLessonsByModule] = useState<Record<string, Lesson[]>>({});
  const [loadingFoundationLessons, setLoadingFoundationLessons] = useState(false);
  const [currentFoundationLessonIndex, setCurrentFoundationLessonIndex] = useState(0);
  const [foundationLessonsCompletedCount, setFoundationLessonsCompletedCount] = useState(0);
  const [currentLessonWatchedEnough, setCurrentLessonWatchedEnough] = useState(false);
  const [currentLessonWatchFraction, setCurrentLessonWatchFraction] = useState(0);
  const [recordingProgress, setRecordingProgress] = useState(false);
  const currentLessonIsYouTubeRef = useRef(false);
  const hasRestoredFoundationProgressRef = useRef(false);
  const maxWatchedTimeRef = useRef(0);
  const lastLessonIdRef = useRef<string | null>(null);
  const [loadingCurriculum, setLoadingCurriculum] = useState(true);
  
  // Real data from backend
  const [readinessScore, setReadinessScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [points, setPoints] = useState(0);
  const [badges, setBadges] = useState(0);
  const [rank, setRank] = useState('Bronze');
  const [level, setLevel] = useState('1');
  const [subscriptionTier, setSubscriptionTier] = useState<'free' | 'starter' | 'professional' | 'premium'>('free');
  const [subscriptionPlanName, setSubscriptionPlanName] = useState<string>('free');
  const [subscriptionDaysLeft, setSubscriptionDaysLeft] = useState<number | null>(null);
  
  // Missions data
  const [activeMissions, setActiveMissions] = useState<any[]>([]);
  const [loadingMissions, setLoadingMissions] = useState(true);
  
  // Cohort data
  const [cohortId, setCohortId] = useState<string | null>(null);
  const [cohortName, setCohortName] = useState<string | null>(null);
  const [cohortDiscussions, setCohortDiscussions] = useState<any[]>([]);
  const [cohortMentors, setCohortMentors] = useState<any[]>([]);
  const [loadingCohortData, setLoadingCohortData] = useState(true);
  
  // Next actions
  const [nextActions, setNextActions] = useState<any[]>([]);

  // Get track theme
  const trackTheme = profiledTrack 
    ? trackThemes[profiledTrack.toLowerCase()] || trackThemes.defender
    : trackThemes.defender;

  // Get track color classes
  const getTrackColorClasses = (type: 'bg' | 'border' | 'text' | 'gradient') => {
    const trackKey = profiledTrack?.toLowerCase() || 'defender';
    const theme = trackThemes[trackKey] || trackThemes.defender;
    
    const colorMap: Record<string, Record<string, string>> = {
      bg: {
        defender: 'bg-indigo-500/20',
        offensive: 'bg-red-500/20',
        grc: 'bg-emerald-500/20',
        innovation: 'bg-cyan-500/20',
        leadership: 'bg-och-gold/20',
      },
      border: {
        defender: 'border-indigo-500/30',
        offensive: 'border-red-500/30',
        grc: 'border-emerald-500/30',
        innovation: 'border-cyan-500/30',
        leadership: 'border-och-gold/30',
      },
      text: {
        defender: 'text-indigo-400',
        offensive: 'text-red-400',
        grc: 'text-emerald-400',
        innovation: 'text-cyan-400',
        leadership: 'text-och-gold',
      },
      gradient: {
        defender: 'from-indigo-500/20 via-blue-500/10 to-indigo-500/20',
        offensive: 'from-red-500/20 via-orange-500/10 to-red-500/20',
        grc: 'from-emerald-500/20 via-teal-500/10 to-emerald-500/20',
        innovation: 'from-cyan-500/20 via-sky-500/10 to-cyan-500/20',
        leadership: 'from-och-gold/20 via-amber-500/10 to-och-gold/20',
      },
    };
    
    return colorMap[type]?.[trackKey] || colorMap[type]?.defender || '';
  };

  // Fetch subscription status (authoritative source for plan/tier)
  useEffect(() => {
    if (!user?.id) return;
    apiGateway.get<{ tier: string; plan_name: string; current_period_end?: string }>('/subscription/status').then((status) => {
      const tier = status.tier === 'professional' || status.tier === 'premium' ? 'professional' : (status.tier || 'free');
      setSubscriptionTier(tier);
      setSubscriptionPlanName(status.plan_name || 'free');
      if (status.current_period_end) {
        const end = new Date(status.current_period_end);
        const now = new Date();
        const days = Math.max(0, Math.ceil((end.getTime() - now.getTime()) / (24 * 60 * 60 * 1000)));
        setSubscriptionDaysLeft(days);
      }
    }).catch(() => { /* keep defaults */ });
  }, [user?.id]);

  // Fetch all dashboard data in parallel for better performance
  useEffect(() => {
    const fetchAllData = async () => {
      if (!user?.id) return;

      setLoadingMissions(true);

      try {
        // Make all API calls in parallel for better performance
        // Wrap each call to suppress expected errors (404s, empty responses)
        const [dashboardResponse, actionsResponse, missionsResponse] = await Promise.allSettled([
          apiGateway.get<any>('/student/dashboard/overview').catch((err: any) => {
            // Suppress 404s and connection errors - these are expected for new users
            if (err?.status === 404 || err?.status === 0) {
              return null;
            }
            // Re-throw unexpected errors
            throw err;
          }),
          apiGateway.get<any[]>('/student/dashboard/next-actions').catch((err: any) => {
            // Suppress 404s and connection errors
            if (err?.status === 404 || err?.status === 0) {
              return [];
            }
            throw err;
          }),
          apiGateway.get<any>('/student/missions', {
            params: { status: 'in_progress', page_size: 3 }
          }).catch((err: any) => {
            // Suppress 404s and connection errors
            if (err?.status === 404 || err?.status === 0) {
              return { results: [] };
            }
            throw err;
          })
        ]);

        // Handle dashboard overview data
        if (dashboardResponse.status === 'fulfilled' && dashboardResponse.value) {
          const dashboardData = dashboardResponse.value;
          if (dashboardData?.readiness) {
            setReadinessScore(dashboardData.readiness.score || 0);
          }
          // Backend returns gamification data under 'quick_stats'
          const gamificationData = dashboardData?.gamification || dashboardData?.quick_stats;
          if (gamificationData) {
            setStreak(gamificationData.streak || 0);
            setPoints(gamificationData.points || 0);
            setBadges(gamificationData.badges || 0);
            setRank(gamificationData.rank || 'Bronze');
            setLevel(gamificationData.level || '1');
          }
          if (dashboardData?.subscription) {
            const tier = dashboardData.subscription.tier || 'free';
            setSubscriptionTier(tier === 'premium' ? 'professional' : tier);
            setSubscriptionPlanName(dashboardData.subscription.plan_name || 'free');
            setSubscriptionDaysLeft(dashboardData.subscription.days_left ?? null);
          }
        }

        // Handle next actions
        if (actionsResponse.status === 'fulfilled') {
          const actions = actionsResponse.value;
          setNextActions(Array.isArray(actions) ? actions : []);
        } else {
          // Only log if it's not a 404 or connection error (expected for new users)
          const error = actionsResponse.reason;
          if (error?.status !== 404 && error?.status !== 0) {
            console.error('Failed to fetch next actions:', error);
          }
          setNextActions([]);
        }

        // Handle active missions
        if (missionsResponse.status === 'fulfilled') {
          const missionsData = missionsResponse.value;
          setActiveMissions(Array.isArray(missionsData?.results) ? missionsData.results : []);
        } else {
          // Only log if it's not a 404 or connection error (expected for new users)
          const error = missionsResponse.reason;
          if (error?.status !== 404 && error?.status !== 0) {
            console.error('Failed to fetch missions:', error);
          }
          setActiveMissions([]);
        }

      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoadingMissions(false);
        setLoadingDashboard(false);
      }
    };

    fetchAllData();
  }, [user?.id]);

  // Fetch profiled track
  useEffect(() => {
    const fetchProfiledTrack = async () => {
      if (!user?.id) {
        setLoadingTrack(false);
        return;
      }

      try {
        try {
          const profilingStatus = await fastapiClient.profiling.checkStatus();
          if (profilingStatus.completed && profilingStatus.session_id) {
            const results = await fastapiClient.profiling.getResults(profilingStatus.session_id);
            setProfilingResults(results);
            
            if (results.primary_track) {
              const trackKey = results.primary_track.key || results.primary_track.track_key;
              if (trackKey) {
                setProfiledTrack(trackKey);
                setLoadingTrack(false);
                return;
              }
            }
            
            if (results.recommendations && results.recommendations.length > 0) {
              const primaryRec = results.recommendations[0];
              if (primaryRec.track_key) {
                setProfiledTrack(primaryRec.track_key);
                setLoadingTrack(false);
                return;
              }
            }
          }
        } catch (fastapiError) {
          console.log('FastAPI profiling not available, trying Django...', fastapiError);
        }

        try {
          const profileResponse = await apiGateway.get<any>('/student/profile');
          
          if (profileResponse?.profiled_track?.track_key) {
            setProfiledTrack(profileResponse.profiled_track.track_key);
            setLoadingTrack(false);
            return;
          }
          
          if (profileResponse?.enrollment?.track_key) {
            setProfiledTrack(profileResponse.enrollment.track_key);
            setLoadingTrack(false);
            return;
          }
        } catch (djangoError) {
          console.log('Django profile not available:', djangoError);
        }
      } catch (error) {
        console.error('Failed to fetch profiled track:', error);
      } finally {
        setLoadingTrack(false);
      }
    };

    fetchProfiledTrack();
  }, [user?.id]);

  // Fetch Foundations status
  useEffect(() => {
    const fetchFoundations = async () => {
      if (!user?.id) {
        setLoadingFoundations(false);
        return;
      }

      try {
        const status = await foundationsClient.getStatus();
        setFoundationsStatus(status);
      } catch (error: any) {
        // Only log if it's a meaningful error (not 404 or empty error)
        if (error?.status && error.status !== 404 && error.status !== 0) {
          console.error('Failed to fetch Foundations status:', error);
        }
        // Silently handle 404s and connection errors - they're expected in some cases
      } finally {
        setLoadingFoundations(false);
      }
    };

    fetchFoundations();
  }, [user?.id]);

  // Fetch curriculum progress
  useEffect(() => {
    const fetchCurriculumProgress = async () => {
      if (!user?.id || !profiledTrack) {
        setLoadingCurriculum(false);
        return;
      }

      try {
        // First, try to get track info from curriculum tracks API
        // This will fail gracefully if no tracks exist in database
        try {
          // Try to fetch track by slug first (e.g., /api/v1/curriculum/tracks/defender/)
          const trackSlug = profiledTrack.toLowerCase();
          const progressResponse = await curriculumClient.getTrackProgress(trackSlug);

          // Check if response indicates user is not enrolled
          if (progressResponse && (progressResponse as any).enrolled === false) {
            // User not enrolled - this is expected, they need to complete profiling first
            console.log('User not enrolled in track yet - awaiting profiling completion');
            setCurriculumProgress(null);
          } else if ((progressResponse as any).progress) {
            // User is enrolled, set progress from nested object
            setCurriculumProgress((progressResponse as any).progress);
          } else {
            // Direct progress object
            setCurriculumProgress(progressResponse);
          }
        } catch (apiError: any) {
          // Track doesn't exist or user not enrolled - this is okay
          // Just log for debugging but don't treat as error
          if (apiError?.status === 404) {
            console.log(`Track "${profiledTrack}" not found in curriculum - may need to be created`);
          } else {
            console.log('Track progress not available:', apiError?.message || 'Unknown error');
          }
          setCurriculumProgress(null);
        }
      } catch (error) {
        console.error('Failed to fetch curriculum progress:', error);
        setCurriculumProgress(null);
      } finally {
        setLoadingCurriculum(false);
      }
    };

    if (profiledTrack) {
      fetchCurriculumProgress();
    }
  }, [user?.id, profiledTrack]);

  // Fetch cohort data
  useEffect(() => {
    const fetchCohortData = async () => {
      if (!user?.id) {
        setLoadingCohortData(false);
        return;
      }

      setLoadingCohortData(true);
      try {
        const profileResponse = await apiGateway.get<any>('/student/profile');
        const enrollment = profileResponse?.enrollment;
        
        if (enrollment?.cohort_id) {
          const cohortIdStr = String(enrollment.cohort_id);
          setCohortId(cohortIdStr);
          setCohortName(enrollment.cohort_name || null);

          try {
            const feedResponse = await communityClient.getFeed({ 
              page: 1, 
              page_size: 3 
            });
            setCohortDiscussions(feedResponse.results || []);
          } catch (feedError) {
            console.error('Failed to fetch cohort discussions:', feedError);
            setCohortDiscussions([]);
          }

          try {
            const mentors = await programsClient.getCohortMentors(cohortIdStr);
            setCohortMentors(mentors.filter((m: any) => m.active !== false) || []);
          } catch (mentorError) {
            console.error('Failed to fetch cohort mentors:', mentorError);
            setCohortMentors([]);
          }
        }
      } catch (error) {
        console.error('Failed to fetch cohort data:', error);
      } finally {
        setLoadingCohortData(false);
      }
    };

    fetchCohortData();
  }, [user?.id]);

  // Fetch lessons for all curriculum foundation modules so we can show a flat lesson list
  useEffect(() => {
    const curriculumModules = foundationsStatus?.modules?.filter((m: FoundationsModule) => m.source === 'curriculum') ?? [];
    const missing = curriculumModules.filter((m: FoundationsModule) => !foundationLessonsByModule[m.id]);
    if (missing.length === 0) return;
    let cancelled = false;
    setLoadingFoundationLessons(true);
    Promise.all(missing.map((m: FoundationsModule) => curriculumClient.getLessonsByModule(m.id).catch(() => [])))
      .then((results) => {
        if (cancelled) return;
        setFoundationLessonsByModule((prev) => {
          const next = { ...prev };
          missing.forEach((m: FoundationsModule, i: number) => { next[m.id] = results[i] ?? []; });
          return next;
        });
      })
      .finally(() => { if (!cancelled) setLoadingFoundationLessons(false); });
    return () => { cancelled = true; };
  }, [foundationsStatus?.modules, foundationLessonsByModule]);

  // Restore which lesson to show (resume at first incomplete) — do NOT restore completed count from API so % and X/Y modules stay correct until user actually clicks Next
  useEffect(() => {
    if (hasRestoredFoundationProgressRef.current || loadingFoundationLessons) return;
    const modules = foundationsStatus?.modules?.filter((m: FoundationsModule) => m.source === 'curriculum') ?? [];
    const allLessons: Lesson[] = modules.flatMap((m: FoundationsModule) => foundationLessonsByModule[m.id] ?? []);
    if (allLessons.length === 0) return;
    hasRestoredFoundationProgressRef.current = true;
    const firstIncomplete = allLessons.findIndex((l) => !(l as Lesson & { is_completed?: boolean }).is_completed);
    if (firstIncomplete >= 0) setCurrentFoundationLessonIndex(firstIncomplete);
  }, [foundationsStatus?.modules, foundationLessonsByModule, loadingFoundationLessons]);

  // Reset "watched enough" and in-lesson progress when user moves to a different lesson (Next)
  useEffect(() => {
    setCurrentLessonWatchedEnough(false);
    setCurrentLessonWatchFraction(0);
  }, [currentFoundationLessonIndex]);

  // Listen for YouTube iframe "video ended" so Next unlocks only after watching
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== 'https://www.youtube.com') return;
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'onStateChange' && data.info === 0 && currentLessonIsYouTubeRef.current) {
          setCurrentLessonWatchedEnough(true);
          setCurrentLessonWatchFraction(1);
        }
      } catch {
        // ignore non-JSON
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // Minimum watch time for Vimeo/article iframes (no progress API) — unlock Next after ~90% of lesson duration
  useEffect(() => {
    const modules = foundationsStatus?.modules?.filter((m: FoundationsModule) => m.source === 'curriculum') ?? [];
    const allLessons: Lesson[] = modules.flatMap((m: FoundationsModule) => foundationLessonsByModule[m.id] ?? []);
    const idx = Math.min(currentFoundationLessonIndex, allLessons.length - 1);
    const lesson = allLessons[idx];
    if (!lesson || !lesson.content_url) return;
    const isYt = lesson.content_url.includes('youtube.com') || lesson.content_url.includes('youtu.be');
    const embedUrl = getEmbedUrl(lesson.content_url);
    const isVimeo = embedUrl && !isYt;
    const isArticle = lesson.lesson_type !== 'video';
    const minutes = (lesson.duration_minutes ?? 1) * 0.9;
    const ms = (isArticle ? 1 : minutes) * 60 * 1000;
    if (isVimeo || isArticle) {
      const t = setTimeout(() => setCurrentLessonWatchedEnough(true), ms);
      return () => clearTimeout(t);
    }
  }, [foundationsStatus?.modules, foundationLessonsByModule, currentFoundationLessonIndex]);

  const trackDisplayName = trackTheme.name;

  // Treat foundations as incomplete when status says so OR completion < 100 (avoids backend returning is_complete: true for new users)
  const foundationsIncomplete = foundationsStatus && (
    foundationsStatus.status === 'not_started' ||
    foundationsStatus.status === 'in_progress' ||
    !foundationsStatus.is_complete ||
    (foundationsStatus.completion_percentage ?? 0) < 100
  );
  const foundationsComplete = foundationsStatus && foundationsStatus.is_complete && foundationsStatus.status === 'completed';
  // When we have no foundations status after load (e.g. new user), show simplified dashboard too
  const showSimplifiedDashboard = foundationsIncomplete || (!loadingFoundations && !foundationsStatus);

  return (
    <div className="min-h-screen bg-gradient-to-br from-och-midnight via-och-midnight/95 to-slate-950">
      {/* Main Content - Compact */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-4">
        
        {/* Hero Section - Compact (reduced vertical space) */}
        {profiledTrack && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`relative overflow-hidden rounded-lg bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')} px-3 py-2.5`}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 flex-1 min-w-0">
                <div className={`p-1.5 rounded-md ${getTrackColorClasses('bg')} ${getTrackColorClasses('border')} border`}>
                  {trackTheme.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge className={`${getTrackColorClasses('bg')} ${getTrackColorClasses('text')} text-[10px] border-0 px-1.5 py-0`}>Your Track</Badge>
                    <h1 className="text-base font-black text-white truncate">{trackTheme.name}</h1>
                    <span className="text-[10px] text-och-steel truncate hidden sm:inline">— {trackTheme.description}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-och-steel">{curriculumProgress && curriculumProgress.completion_percentage != null ? Math.round(curriculumProgress.completion_percentage) : 0}%</span>
                <Button variant="outline" size="sm" className={`${getTrackColorClasses('border')} ${getTrackColorClasses('text')} hover:${getTrackColorClasses('bg')} border text-xs h-7 px-2`} onClick={() => router.push('/dashboard/student/curriculum')}>View</Button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Foundations section: flat lessons list + video preview (no module UI) */}
        {foundationsIncomplete && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <Card className={`p-4 bg-slate-900/50 border-slate-700 border ${getTrackColorClasses('border')}`}>
              {foundationsStatus.modules && foundationsStatus.modules.length > 0 ? (
                <>
                  {loadingFoundationLessons ? (
                    <>
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <h2 className="text-base font-semibold text-white">Beginner Level – Foundations</h2>
                        <span className="text-xs text-och-steel shrink-0">Loading…</span>
                      </div>
                      <p className="text-xs text-och-steel">Loading lessons…</p>
                    </>
                  ) : (() => {
                    const curriculumModules = foundationsStatus.modules.filter((m: FoundationsModule) => m.source === 'curriculum');
                    const allLessons: Lesson[] = curriculumModules.flatMap((m: FoundationsModule) => foundationLessonsByModule[m.id] ?? []);
                    if (allLessons.length === 0) return <p className="text-xs text-och-steel">No lessons yet.</p>;
                    const lessonIdToIndex: Record<string, number> = {};
                    allLessons.forEach((l, i) => { lessonIdToIndex[l.id] = i; });
                    const modulesCompletedCount = curriculumModules.filter((m: FoundationsModule) => {
                      const ids = (foundationLessonsByModule[m.id] ?? []).map((l: Lesson) => l.id);
                      return ids.length > 0 && ids.every((id: string) => lessonIdToIndex[id] < foundationLessonsCompletedCount);
                    }).length;
                    const totalModules = curriculumModules.length;
                    const currentIndex = Math.min(currentFoundationLessonIndex, allLessons.length - 1);
                    const currentLesson = allLessons[currentIndex];
                    const totalLessons = allLessons.length;
                    const progressPercent = totalLessons ? ((foundationLessonsCompletedCount + currentLessonWatchFraction) / totalLessons) * 100 : 0;
                    const completedSegmentPercent = totalLessons ? (foundationLessonsCompletedCount / totalLessons) * 100 : 0;
                    const inProgressSegmentPercent = totalLessons ? (currentLessonWatchFraction / totalLessons) * 100 : 0;
                    const isLastLesson = currentIndex === allLessons.length - 1;
                    const allPreviousCompleted = foundationLessonsCompletedCount >= allLessons.length - 1;
                    const canComplete = isLastLesson && allPreviousCompleted && currentLessonWatchedEnough;
                    const isYouTube = !!(currentLesson.content_url && (currentLesson.content_url.includes('youtube.com') || currentLesson.content_url.includes('youtu.be')));
                    currentLessonIsYouTubeRef.current = currentLesson.lesson_type === 'video' && isYouTube;

                    const handleNext = async () => {
                      if (recordingProgress) return;
                      setRecordingProgress(true);
                      try {
                        await curriculumClient.updateLessonProgress(currentLesson.id, { status: 'completed', progress_percentage: 100 });
                        setFoundationLessonsCompletedCount((prev) => prev + 1);
                        if (!isLastLesson) setCurrentFoundationLessonIndex((prev) => Math.min(prev + 1, allLessons.length - 1));
                        else {
                          const status = await foundationsClient.getStatus();
                          setFoundationsStatus(status);
                        }
                      } catch (e) {
                        if (!isLastLesson) setCurrentFoundationLessonIndex((prev) => Math.min(prev + 1, allLessons.length - 1));
                      } finally {
                        setRecordingProgress(false);
                      }
                    };

                    return (
                      <>
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <h2 className="text-base font-semibold text-white">Beginner Level – Foundations</h2>
                          <span className="text-xs text-och-steel shrink-0">
                            {Math.round(progressPercent)}% · {modulesCompletedCount}/{totalModules} modules
                          </span>
                        </div>
                        <div className="space-y-2 flex flex-col min-h-0">
                        {/* Progress bar with lesson markers */}
                        <div className="space-y-1 flex-shrink-0">
                          <div className="flex items-center justify-between text-[10px] sm:text-xs text-och-steel">
                            <span>Lesson {currentIndex + 1} of {allLessons.length}</span>
                            <span>{Math.round(progressPercent)}%</span>
                          </div>
                          <div className="relative h-2.5 rounded-full bg-white/10 overflow-visible">
                            {/* Completed lessons: gold */}
                            <motion.div
                              className="absolute inset-y-0 left-0 rounded-l-full bg-och-gold"
                              initial={false}
                              animate={{ width: `${completedSegmentPercent}%` }}
                              transition={{ duration: 0.25 }}
                            />
                            {/* Current lesson in progress: moves with video, different color */}
                            <motion.div
                              className="absolute inset-y-0 rounded-r-full bg-blue-500/80"
                              style={{ left: `${completedSegmentPercent}%` }}
                              initial={false}
                              animate={{ width: `${inProgressSegmentPercent}%` }}
                              transition={{ duration: 0.25 }}
                            />
                            {/* Dots at the START of each lesson (1 = start of lesson 1, 2 = start of lesson 2) with number inside */}
                            {allLessons.map((lesson, i) => {
                              const positionPercent = allLessons.length > 1 ? (i / allLessons.length) * 100 : 0;
                              const isCompleted = (i + 1) <= foundationLessonsCompletedCount;
                              const isFirst = i === 0;
                              return (
                                <button
                                  key={lesson.id}
                                  type="button"
                                  onClick={() => setCurrentFoundationLessonIndex(i)}
                                  className={clsx(
                                    'absolute top-1/2 -translate-y-1/2 w-6 h-6 rounded-full z-10 border-2 transition-colors cursor-pointer hover:scale-110 focus:outline-none focus:ring-2 focus:ring-och-gold focus:ring-offset-2 focus:ring-offset-slate-900 flex items-center justify-center text-[10px] font-bold',
                                    isCompleted ? 'bg-och-gold border-och-gold text-slate-900' : 'bg-slate-800 border-white/60 text-och-steel'
                                  )}
                                  style={{ left: isFirst ? '0' : `calc(${positionPercent}% - 12px)` }}
                                  title={`Lesson ${i + 1}: ${lesson.title}${isCompleted ? ' (completed)' : ''} — click to go`}
                                >
                                  {i + 1}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                        {/* Lesson row + video */}
                        <div className="space-y-0 flex-1 min-h-0 flex flex-col">
                          <div className="w-full text-left p-2 rounded-t-lg flex items-center gap-2 bg-white/5 border border-och-steel/20 border-b-0 flex-shrink-0">
                            <span className="text-xs text-och-steel w-6 shrink-0">{currentIndex + 1}</span>
                            <span className="text-sm text-white truncate flex-1">{currentLesson.title}</span>
                          </div>
                          <div className="rounded-b-lg overflow-hidden border border-och-steel/20 border-t-0 bg-black flex-1 min-h-[480px] flex flex-col">
                            {currentLesson.content_url ? (
                              currentLesson.lesson_type === 'video' ? (
                                getEmbedUrl(currentLesson.content_url) ? (
                                  <iframe
                                    src={getEmbedUrl(currentLesson.content_url)!}
                                    title={currentLesson.title}
                                    className="w-full aspect-video min-h-[480px]"
                                    allowFullScreen
                                  />
                                ) : (
                                  <video
                                    src={resolveContentUrl(currentLesson.content_url)}
                                    controls
                                    className="w-full aspect-video min-h-[480px]"
                                    title={currentLesson.title}
                                    onLoadedMetadata={(e) => {
                                      if (lastLessonIdRef.current !== currentLesson.id) {
                                        lastLessonIdRef.current = currentLesson.id;
                                        maxWatchedTimeRef.current = 0;
                                      }
                                    }}
                                    onTimeUpdate={(e) => {
                                      const v = e.currentTarget;
                                      const max = maxWatchedTimeRef.current;
                                      if (v.currentTime > max + 1.5) {
                                        v.currentTime = max;
                                      } else {
                                        maxWatchedTimeRef.current = v.currentTime;
                                      }
                                      if (v.duration > 0) {
                                        const frac = v.currentTime / v.duration;
                                        setCurrentLessonWatchFraction(frac);
                                        if (frac >= 0.9) setCurrentLessonWatchedEnough(true);
                                      }
                                    }}
                                    onEnded={() => { setCurrentLessonWatchedEnough(true); setCurrentLessonWatchFraction(1); }}
                                  />
                                )
                              ) : (
                                <iframe
                                  src={resolveContentUrl(currentLesson.content_url)}
                                  title={currentLesson.title}
                                  className="w-full aspect-video min-h-[480px]"
                                  allowFullScreen
                                />
                              )
                            ) : (
                              <div className="flex items-center justify-center aspect-video min-h-[480px] text-och-steel text-sm">No content URL</div>
                            )}
                          </div>
                        </div>
                        {/* Next / Complete — visible without scrolling */}
                        <div className="flex justify-end items-center gap-3 pt-1 flex-shrink-0">
                          {!currentLessonWatchedEnough && (
                            <span className="text-xs text-och-steel">Watch the video to continue</span>
                          )}
                          {isLastLesson && !allPreviousCompleted && (
                            <span className="text-xs text-och-steel">Complete all previous lessons first</span>
                          )}
                          <Button
                            onClick={handleNext}
                            disabled={recordingProgress || (isLastLesson ? !canComplete : !currentLessonWatchedEnough)}
                            className={`${getTrackColorClasses('bg')} ${getTrackColorClasses('text')} border ${getTrackColorClasses('border')} text-sm disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none`}
                          >
                            {recordingProgress ? 'Saving…' : isLastLesson ? 'Complete' : 'Next'}
                          </Button>
                        </div>
                        </div>
                      </>
                    );
                  })()}
                </>
              ) : (
                <div className="py-8 text-center text-och-steel text-sm">No Foundation Module added yet.</div>
              )}
            </Card>
          </motion.div>
        )}

        {/* Quick Stats - only when foundations complete (simplified dashboard for new students) */}
        {!showSimplifiedDashboard && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Card className={`p-3 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                <Badge className={`${getTrackColorClasses('bg')} ${getTrackColorClasses('text')} text-xs border-0`}>
                  {readinessScore}/100
                </Badge>
              </div>
              <div className="text-lg font-black text-white">{readinessScore}</div>
              <div className="text-xs text-och-steel uppercase tracking-wide">Readiness</div>
            </Card>

            <Card className="p-3 bg-gradient-to-br from-och-gold/10 to-transparent border border-och-gold/20">
              <div className="flex items-center justify-between mb-2">
                <Flame className="w-4 h-4 text-och-gold" />
              </div>
              <div className="text-lg font-black text-white">{streak}</div>
              <div className="text-xs text-och-steel uppercase tracking-wide">Day Streak</div>
            </Card>

            <Card className="p-3 bg-gradient-to-br from-och-defender/10 to-transparent border border-och-defender/20">
              <div className="flex items-center justify-between mb-2">
                <Star className="w-4 h-4 text-och-defender" />
              </div>
              <div className="text-lg font-black text-white">{points.toLocaleString()}</div>
              <div className="text-xs text-och-steel uppercase tracking-wide">Points</div>
            </Card>

            <Card className="p-3 bg-gradient-to-br from-och-orange/10 to-transparent border border-och-orange/20">
              <div className="flex items-center justify-between mb-2">
                <Award className="w-4 h-4 text-och-orange" />
              </div>
              <div className="text-lg font-black text-white">{badges}</div>
              <div className="text-xs text-och-steel uppercase tracking-wide">Badges</div>
            </Card>
          </div>
        )}

        {/* Foundations (compact when complete) & Subscription - Compact Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Foundations Status: only show compact card when complete (full section shown above when not complete) */}
          {foundationsComplete && (
            <Card className={`p-4 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <GraduationCap className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                  <div>
                    <h3 className="text-sm font-black text-white">Beginner Level - Foundations</h3>
                    <p className="text-xs text-och-steel">Complete</p>
                  </div>
                </div>
                <CheckCircle2 className="w-5 h-5 text-och-mint" />
              </div>
            </Card>
          )}

          {/* Subscription — dynamic from API */}
          <Card className={`p-4 bg-gradient-to-br ${subscriptionTier === 'free' ? 'from-och-gold/10 to-transparent border-och-gold/20' : getTrackColorClasses('gradient')} border ${subscriptionTier === 'free' ? 'border-och-gold/20' : getTrackColorClasses('border')}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Crown className={`w-4 h-4 ${subscriptionTier === 'free' ? 'text-och-gold' : getTrackColorClasses('text')}`} />
                <div>
                  <h3 className="text-sm font-black text-white">
                    {subscriptionTier === 'free'
                      ? 'Free Plan'
                      : subscriptionPlanName === 'professional_7' || subscriptionTier === 'professional'
                        ? 'Yearly Plan'
                        : subscriptionTier === 'starter'
                          ? 'Monthly Plan'
                          : subscriptionPlanName.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </h3>
                  <p className="text-xs text-och-steel">
                    {subscriptionTier === 'free'
                      ? 'Upgrade to unlock more features'
                      : subscriptionDaysLeft !== null
                        ? `${subscriptionDaysLeft} days remaining`
                        : 'Active subscription'}
                  </p>
                </div>
              </div>
              {subscriptionTier === 'free' && (
                <Button
                  variant="outline"
                  size="sm"
                  className="border-och-gold text-och-gold hover:bg-och-gold hover:text-black text-xs"
                  onClick={() => router.push('/dashboard/student/subscription')}
                >
                  Upgrade
                </Button>
              )}
            </div>
          </Card>
        </div>

        {/* When foundations incomplete: only Foundations section is shown above (no extra card). When no status: one CTA. Otherwise: full tabs. */}
        {showSimplifiedDashboard && !foundationsIncomplete ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <Card className={`p-6 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
              <div className="flex flex-col items-center text-center gap-4">
                <Lock className={`w-10 h-10 ${getTrackColorClasses('text')}`} />
                <div>
                  <h3 className="text-base font-black text-white mb-1">Start Foundations to unlock your dashboard</h3>
                  <p className="text-sm text-och-steel">
                    Complete Foundations to access your Learning Path, Missions, Discussions, Mentors, and AI Coach.
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className={`${getTrackColorClasses('border')} ${getTrackColorClasses('text')}`}
                  onClick={() => router.push('/dashboard/student/foundations')}
                >
                  Start
                  <ChevronRight className="w-3.5 h-3.5 ml-1" />
                </Button>
              </div>
            </Card>
          </motion.div>
        ) : showSimplifiedDashboard && foundationsIncomplete ? null : (
          <>
        {/* Tab Navigation - Compact */}
        <div className="flex gap-1 border-b border-och-steel/20">
          {[
            { id: 'overview', label: 'Overview', icon: Activity },
            { id: 'progress', label: 'Progress', icon: LineChart },
            { id: 'community', label: 'Community', icon: Users },
          ].map((tab) => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={clsx(
                  "flex items-center gap-1.5 px-3 py-2 text-xs font-bold uppercase tracking-wide border-b-2 transition-all",
                  activeTab === tab.id
                    ? `${getTrackColorClasses('border')} text-white`
                    : "border-transparent text-och-steel hover:text-white"
                )}
              >
                <TabIcon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-3"
            >
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                {/* Left Column - Learning */}
                <div className="lg:col-span-2 space-y-3">
                  {/* Next Action */}
                  {nextActions.length > 0 && (
                    <Card className={`p-4 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-lg ${getTrackColorClasses('bg')} ${getTrackColorClasses('border')} border`}>
                          <Rocket className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-black text-white mb-1">What to do next</h3>
                          <p className="text-xs text-white mb-2 line-clamp-2">
                            {nextActions[0].title || "Continue your learning journey"}
                          </p>
                          <Button
                            variant="defender"
                            size="sm"
                            className={`${getTrackColorClasses('bg')} ${getTrackColorClasses('text')} hover:opacity-90 text-xs`}
                            onClick={() => router.push(nextActions[0].action_url || '/dashboard/student/curriculum')}
                          >
                            Start Now
                            <ChevronRight className="w-3 h-3 ml-1" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  )}

                  {/* Active Missions */}
                  {activeMissions.length > 0 && (
                    <Card className={`p-4 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
                      <div className="flex items-center gap-2 mb-3">
                        <Target className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                        <h3 className="text-sm font-black text-white">Active Missions</h3>
                      </div>
                      <div className="space-y-2">
                        {activeMissions.slice(0, 2).map((mission: any) => (
                          <button
                            key={mission.id}
                            onClick={() => router.push(`/dashboard/student/missions/${mission.id}`)}
                            className="w-full text-left p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                          >
                            <p className="text-xs font-bold text-white truncate mb-1">
                              {mission.title || mission.mission?.title}
                            </p>
                            <p className="text-xs text-och-steel line-clamp-1">
                              {mission.status || 'In Progress'}
                            </p>
                          </button>
                        ))}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        className={`w-full mt-2 ${getTrackColorClasses('border')} ${getTrackColorClasses('text')} text-xs`}
                        onClick={() => router.push('/dashboard/student/missions')}
                      >
                        View All Missions
                      </Button>
                    </Card>
                  )}

                  {/* Curriculum Progress */}
                  {curriculumProgress && (
                    <Card className={`p-4 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <BookOpen className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                          <h3 className="text-sm font-black text-white">Learning Path</h3>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={`text-xs ${getTrackColorClasses('text')}`}
                          onClick={() => {
                            const trackCode = `${profiledTrack?.toUpperCase()}_2`;
                            router.push(`/dashboard/student/curriculum/${trackCode}/tier2`);
                          }}
                        >
                          View
                          <ChevronRight className="w-3 h-3 ml-1" />
                        </Button>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-och-steel">Progress</span>
                          <span className={`font-bold ${getTrackColorClasses('text')}`}>
                            {curriculumProgress?.completion_percentage !== null && curriculumProgress?.completion_percentage !== undefined
                              ? Math.round(curriculumProgress.completion_percentage)
                              : 0}%
                          </span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            className={`h-full ${getTrackColorClasses('bg')} rounded-full`}
                            initial={{ width: 0 }}
                            animate={{ width: `${curriculumProgress?.completion_percentage || 0}%` }}
                            transition={{ duration: 1 }}
                          />
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                          <div>
                            <div className={`text-sm font-black ${getTrackColorClasses('text')}`}>
                              {curriculumProgress?.modules_completed || 0}
                            </div>
                            <div className="text-xs text-och-steel">Modules</div>
                          </div>
                          <div>
                            <div className={`text-sm font-black ${getTrackColorClasses('text')}`}>
                              {curriculumProgress?.lessons_completed || 0}
                            </div>
                            <div className="text-xs text-och-steel">Lessons</div>
                          </div>
                          <div>
                            <div className={`text-sm font-black ${getTrackColorClasses('text')}`}>
                              {curriculumProgress?.missions_completed || 0}
                            </div>
                            <div className="text-xs text-och-steel">Missions</div>
                          </div>
                        </div>
                      </div>
                    </Card>
                  )}
                </div>

                {/* Right Column - Community */}
                <div className="space-y-3">
                  {/* Cohort Discussions */}
                  <Card className="p-3 bg-och-midnight/60 border border-och-steel/20">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-xs font-black text-och-steel uppercase tracking-wider">
                        Discussions
                      </h3>
                      {cohortId && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-5 px-1.5 text-xs text-och-gold"
                          onClick={() => router.push('/dashboard/student/community')}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                    
                    {loadingCohortData ? (
                      <div className="space-y-2">
                        {[1, 2].map((i) => (
                          <div key={i} className="h-12 bg-white/5 rounded animate-pulse" />
                        ))}
                      </div>
                    ) : cohortDiscussions.length > 0 ? (
                      <div className="space-y-2">
                        {cohortDiscussions.slice(0, 2).map((discussion: any) => (
                          <button
                            key={discussion.id}
                            onClick={() => router.push(`/dashboard/student/community?post=${discussion.id}`)}
                            className="w-full text-left p-2 rounded bg-white/5 hover:bg-white/10 transition-all"
                          >
                            <p className="text-xs font-bold text-white truncate mb-1">
                              {discussion.title || 'Discussion'}
                            </p>
                            <p className="text-xs text-och-steel line-clamp-1">
                              {discussion.content || discussion.excerpt || ''}
                            </p>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <MessageCircle className="w-6 h-6 text-och-steel/50 mx-auto mb-2" />
                        <p className="text-xs text-och-steel mb-2">No discussions yet</p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-och-steel/30 text-och-steel text-xs"
                          onClick={() => router.push('/dashboard/student/community')}
                        >
                          Start Discussion
                        </Button>
                      </div>
                    )}
                  </Card>

                  {/* Cohort Mentors */}
                  <Card className="p-3 bg-och-midnight/60 border border-och-steel/20">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-xs font-black text-och-steel uppercase tracking-wider">
                        Mentors
                      </h3>
                      {cohortId && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-5 px-1.5 text-xs text-och-gold"
                          onClick={() => router.push('/dashboard/student/mentorship')}
                        >
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      )}
                    </div>
                    
                    {loadingCohortData ? (
                      <div className="space-y-2">
                        {[1, 2].map((i) => (
                          <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
                        ))}
                      </div>
                    ) : cohortMentors.length > 0 ? (
                      <div className="space-y-1.5">
                        {cohortMentors.slice(0, 3).map((mentor: any) => {
                          const mentorName = mentor.mentor_name || 
                            (mentor.mentor?.first_name && mentor.mentor?.last_name 
                              ? `${mentor.mentor.first_name} ${mentor.mentor.last_name}`
                              : mentor.mentor?.email || 'Mentor');
                          
                          return (
                            <button
                              key={mentor.id || mentor.mentor?.id}
                              onClick={() => router.push(`/dashboard/student/mentorship?mentor=${mentor.mentor?.id || mentor.mentor_id}`)}
                              className="w-full flex items-center gap-2 p-2 rounded bg-white/5 hover:bg-white/10 transition-all"
                            >
                              <div className="w-6 h-6 rounded-full bg-och-gold/20 flex items-center justify-center flex-shrink-0">
                                <UserCircle className="w-4 h-4 text-och-gold" />
                              </div>
                              <p className="text-xs font-bold text-white truncate flex-1">
                                {mentorName}
                              </p>
                            </button>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <UserCircle className="w-6 h-6 text-och-steel/50 mx-auto mb-2" />
                        <p className="text-xs text-och-steel mb-2">No mentors available</p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-och-steel/30 text-och-steel text-xs"
                          onClick={() => router.push('/dashboard/student/mentorship')}
                        >
                          View Mentorship
                        </Button>
                      </div>
                    )}
                  </Card>

                  {/* AI Coach - dynamic from next actions or coaching */}
                  <Card className={`p-3 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                      <h3 className="text-xs font-black text-white">AI Coach</h3>
                    </div>
                    <p className="text-xs text-och-steel mb-2 line-clamp-2">
                      {nextActions.length > 0 && nextActions[0]?.title
                        ? nextActions[0].title
                        : 'Get personalized guidance and support'}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className={`w-full ${getTrackColorClasses('border')} ${getTrackColorClasses('text')} text-xs`}
                      onClick={() => router.push(nextActions.length > 0 && nextActions[0]?.action_url ? nextActions[0].action_url : '/dashboard/student/coaching')}
                    >
                      <MessageSquare className="w-3 h-3 mr-1" />
                      {nextActions.length > 0 && nextActions[0]?.action_url ? 'Continue' : 'Chat Now'}
                    </Button>
                  </Card>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'progress' && (
            <motion.div
              key="progress"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-3"
            >
              {/* TalentScope Analytics */}
              <Card className="p-4 bg-och-midnight/60 border border-och-steel/20">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <LineChart className="w-4 h-4 text-och-mint" />
                    <h3 className="text-sm font-black text-white">TalentScope Analytics</h3>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push('/dashboard/student/portfolio')}
                    className="text-xs"
                  >
                    <ArrowUpRight className="w-3 h-3" />
                  </Button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wide">
                      Readiness Breakdown
                    </h4>
                    <div className="space-y-2">
                      {[
                        { label: 'Technical Depth', value: 74, color: 'bg-och-gold' },
                        { label: 'Behavioral Readiness', value: 88, color: 'bg-och-mint' },
                        { label: 'Identity Alignment', value: 92, color: getTrackColorClasses('bg') },
                      ].map((metric) => (
                        <div key={metric.label} className="space-y-1">
                          <div className="flex justify-between text-xs font-bold">
                            <span className="text-och-steel">{metric.label}</span>
                            <span className="text-white">{metric.value}%</span>
                          </div>
                          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                            <motion.div
                              className={`h-full ${metric.color} rounded-full`}
                              initial={{ width: 0 }}
                              animate={{ width: `${metric.value}%` }}
                              transition={{ duration: 1, delay: 0.2 }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wide">
                      Future-You Blueprint
                    </h4>
                    <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-8 h-8 rounded-lg ${getTrackColorClasses('bg')} flex items-center justify-center`}>
                          <Star className={`w-4 h-4 ${getTrackColorClasses('text')}`} />
                        </div>
                        <div>
                          <p className="text-xs text-och-steel font-bold uppercase tracking-wider">
                            Persona
                          </p>
                          <p className="text-sm font-black text-white">
                            {profilingResults?.persona || (user as any)?.persona || "Not Set"}
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-och-steel leading-relaxed">
                        Your personalized career path based on your strengths and aspirations.
                      </p>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Track Progress */}
              {curriculumProgress && (
                <Card className={`p-4 bg-gradient-to-br ${getTrackColorClasses('gradient')} border ${getTrackColorClasses('border')}`}>
                  <h3 className="text-sm font-black text-white mb-3">{trackTheme.name} Track Progress</h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-bold text-white">Overall Completion</span>
                        <span className={`text-xs font-bold ${getTrackColorClasses('text')}`}>
                          {curriculumProgress?.completion_percentage !== null && curriculumProgress?.completion_percentage !== undefined
                            ? Math.round(curriculumProgress.completion_percentage)
                            : 0}%
                        </span>
                      </div>
                      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          className={`h-full ${getTrackColorClasses('bg')} rounded-full`}
                          initial={{ width: 0 }}
                          animate={{ width: `${curriculumProgress?.completion_percentage || 0}%` }}
                          transition={{ duration: 1 }}
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      <div className="text-center p-2 rounded bg-white/5">
                        <div className={`text-lg font-black ${getTrackColorClasses('text')} mb-0.5`}>
                          {curriculumProgress?.modules_completed || 0}
                        </div>
                        <div className="text-xs text-och-steel">Modules</div>
                      </div>
                      <div className="text-center p-2 rounded bg-white/5">
                        <div className={`text-lg font-black ${getTrackColorClasses('text')} mb-0.5`}>
                          {curriculumProgress?.lessons_completed || 0}
                        </div>
                        <div className="text-xs text-och-steel">Lessons</div>
                      </div>
                      <div className="text-center p-2 rounded bg-white/5">
                        <div className={`text-lg font-black ${getTrackColorClasses('text')} mb-0.5`}>
                          {curriculumProgress?.missions_completed || 0}
                        </div>
                        <div className="text-xs text-och-steel">Missions</div>
                      </div>
                      <div className="text-center p-2 rounded bg-white/5">
                        <div className={`text-lg font-black ${getTrackColorClasses('text')} mb-0.5`}>
                          {Math.round((curriculumProgress?.total_time_spent_minutes || 0) / 60)}h
                        </div>
                        <div className="text-xs text-och-steel">Time</div>
                      </div>
                    </div>
                  </div>
                </Card>
              )}
            </motion.div>
          )}

          {activeTab === 'community' && (
            <motion.div
              key="community"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="space-y-3"
            >
              {/* Community Feed */}
              <Card className="p-4 bg-och-midnight/60 border border-och-steel/20">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4 text-och-gold" />
                    <h3 className="text-sm font-black text-white">Community Feed</h3>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push('/dashboard/student/community')}
                    className="text-xs"
                  >
                    View All
                    <ArrowUpRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
                
                <div className="space-y-2">
                  {cohortDiscussions.length > 0 ? (
                    cohortDiscussions.map((post: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 rounded-lg bg-white/5 border border-white/10 hover:border-white/20 transition-all"
                      >
                        <div className="flex items-start gap-2">
                          <div className="w-8 h-8 rounded-lg bg-och-midnight border border-och-steel/10 flex items-center justify-center shrink-0">
                            <Users className="w-4 h-4 text-och-gold" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-white mb-1">
                              {post.user || 'Community Member'}
                            </p>
                            <p className="text-xs text-och-steel leading-relaxed line-clamp-2">
                              {post.action || post.content || 'Shared an update'}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-6 text-center">
                      <Users className="w-8 h-8 text-och-steel mx-auto mb-2 opacity-50" />
                      <p className="text-xs text-och-steel">
                        No community updates yet. Check back soon!
                      </p>
                    </div>
                  )}
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
          </>
        )}
      </div>

      {/* AI Coaching Nudge — foundations info while in Foundations; welcome to track when just finished (key so it refetches when context changes) */}
      <Suspense fallback={null}>
        <CoachingNudge
          key={foundationsIncomplete ? 'foundations' : foundationsComplete ? 'foundations_complete' : 'dashboard'}
          userId={user?.id?.toString()}
          autoLoad={true}
          context={foundationsIncomplete ? 'foundations' : foundationsComplete ? 'foundations_complete' : 'dashboard'}
        />
      </Suspense>
    </div>
  );
}
