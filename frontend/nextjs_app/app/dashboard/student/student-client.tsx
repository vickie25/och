/**
 * Student Dashboard Client
 * Orchestrates the Mission Control interface.
 * The sidebar and navigation are handled by the parent StudentLayout.
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { fastapiClient } from '@/services/fastapiClient';
import { foundationsClient } from '@/services/foundationsClient';
import { StudentDashboardHub } from './components/StudentDashboardHub';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Card } from '@/components/ui/Card';
import { Loader2 } from 'lucide-react';

export default function StudentClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isAuthenticated, isLoading: authLoading, reloadUser } = useAuth();
  const [checkingProfiling, setCheckingProfiling] = useState(true);
  const [checkingFoundations, setCheckingFoundations] = useState(false);
  const hasCheckedRef = useRef(false);

  useEffect(() => {
    // Only check if user is authenticated
    // Add a small delay to prevent premature redirects during auth loading
    if (authLoading || !isAuthenticated || !user) {
      console.log('StudentClient: Waiting for auth to load...', { authLoading, isAuthenticated, user: !!user });
      return;
    }

    // Prevent multiple checks
    if (hasCheckedRef.current) {
      return;
    }

    // Mark as checked immediately to prevent re-runs
    hasCheckedRef.current = true;

    // Check if user is a student/mentee
    const userRoles = user?.roles || [];
    const isStudent = userRoles.some((r: any) => {
      const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase();
      return roleName === 'student' || roleName === 'mentee';
    });

    if (!isStudent) {
      console.log('StudentClient: User is not a student/mentee, allowing access without checks');
      setCheckingProfiling(false);
      return;
    }

    console.log('StudentClient: User is student/mentee, proceeding with checks');

    // Check if user needs to update their profile name
    const checkProfileName = () => {
      if (!user?.first_name || !user?.last_name || 
          user.first_name.trim() === '' || user.last_name.trim() === '') {
        console.log('StudentClient: Profile name incomplete - showing name update prompt');
        return true;
      }
      return false;
    };

    // Check profiling status - fetch fresh status from Django API
    const checkProfiling = async () => {
      try {
        // CRITICAL: Fetch fresh user data directly from Django API
        // This ensures admin resets are immediately respected
        const { djangoClient } = await import('@/services/djangoClient');
        
        let currentProfilingComplete: boolean | null = null; // null = unknown (error)
        let universitySet = true;
        
        try {
          console.log('StudentClient: Fetching fresh user data from Django...');
          const freshUser = await djangoClient.auth.getCurrentUser();
          currentProfilingComplete = freshUser?.profiling_complete ?? false;
          console.log('StudentClient: Fresh profiling_complete =', currentProfilingComplete);

          // University mapping is required for community features.
          const uniId = (freshUser as any)?.university_id;
          const uniName = (freshUser as any)?.university_name;
          universitySet = Boolean(uniId) || (typeof uniName === 'string' && uniName.trim().length > 0);
        } catch (err: any) {
          // API error (503, network, timeout) — do NOT redirect to profiler.
          const httpStatus = err?.status || err?.response?.status || 0;
          console.warn('StudentClient: Failed to fetch fresh user, status:', httpStatus, '— allowing dashboard access');
          // For all errors: show dashboard, do not redirect to profiler
          setCheckingProfiling(false);
          setCheckingFoundations(false);
          return;
        }
        
        // ONLY redirect to profiler when Django EXPLICITLY says profiling_complete=false
        if (currentProfilingComplete === false) {
          console.log('✅ Django profiling_complete=false - redirecting to profiler');
          router.push('/onboarding/ai-profiler');
          return;
        }

        // Prompt to set university once per session if missing.
        if (!universitySet && typeof window !== 'undefined') {
          const alreadyPrompted = sessionStorage.getItem('och_prompt_university') === '1';
          if (!alreadyPrompted) {
            sessionStorage.setItem('och_prompt_university', '1');
            console.log('StudentClient: University missing - redirecting to university mapping');
            setCheckingProfiling(false);
            setCheckingFoundations(false);
            router.push('/dashboard/student/settings/profile?highlight=university');
            return;
          }
        }
        
        // Django says profiling is complete - TRUST IT
        console.log('✅ Django profiling_complete=true - profiling verified complete');
        
        setCheckingProfiling(false);
        setCheckingFoundations(true);
        
        // Now check Foundations
        await checkFoundations();
      } catch (error: any) {
        console.error('❌ Unexpected error in checkProfiling:', error);
        // On any unexpected error, allow access to dashboard — never redirect to profiler
        setCheckingProfiling(false);
        setCheckingFoundations(false);
      }
    };

    const checkFoundations = async () => {
      try {
        // Check URL param first - if redirected from foundations completion, trust it
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('foundations_complete') === 'true') {
          console.log('✅ Foundations just completed (URL param) - allowing access');
          setCheckingFoundations(false);
          return;
        }

        // CRITICAL: Fetch fresh user data from Django for foundations status
        // The cached user object may be stale
        const { djangoClient } = await import('@/services/djangoClient');
        let currentFoundationsComplete = user.foundations_complete;
        
        try {
          const freshUser = await djangoClient.auth.getCurrentUser();
          currentFoundationsComplete = freshUser?.foundations_complete ?? false;
          console.log('StudentClient: Fresh foundations_complete =', currentFoundationsComplete);
        } catch (err) {
          console.log('StudentClient: Failed to fetch fresh user for foundations check');
        }

        if (currentFoundationsComplete) {
          console.log('✅ Foundations already completed (Django confirmed)');
          setCheckingFoundations(false);
          return;
        }

        // Check Foundations status from API
        try {
          const foundationsStatus = await foundationsClient.getStatus();
          
          if (!foundationsStatus.foundations_available) {
            console.log('⚠️ Foundations not available:', foundationsStatus);
            // Don't redirect to profiler - we already confirmed profiling is complete above
            // Just allow access to dashboard
            setCheckingFoundations(false);
            return;
          }

          // If Foundations is not complete, redirect to the dashboard Foundations
          // section so the student can resume exactly where they left off.
          if (!foundationsStatus.is_complete) {
            // Allow a special deep-link that shows the Foundations
            // card + video preview on the dashboard without bouncing
            // back to the standalone Foundations page.
            if (typeof window !== 'undefined') {
              const hash = window.location.hash || '';
              if (hash === '#student-tour-foundations') {
                console.log('✅ Foundations incomplete but hash deep-link present - staying on dashboard');
                setCheckingFoundations(false);
                return;
              }
            }

            console.log('✅ Foundations not completed - redirecting to dashboard Foundations section');
            // Allow dashboard to render while the router navigation happens
            setCheckingFoundations(false);
            setCheckingProfiling(false);
            router.push('/dashboard/student#student-tour-foundations');
            return;
          }

          console.log('✅ Foundations completed');
        } catch (foundationsError) {
          console.error('⚠️ Failed to check foundations status:', foundationsError);
          // On error, allow access - don't block the dashboard
        }

        setCheckingFoundations(false);
      } catch (error: any) {
        console.error('❌ Failed to check Foundations status:', error);
        // On error, allow access but log it
        setCheckingFoundations(false);
      }
    };

    // Check if profile name update is needed
    if (checkProfileName()) {
      console.log('StudentClient: Profile name incomplete - redirecting to profile settings');
      setCheckingProfiling(false);
      setCheckingFoundations(false);
      // Add query parameter to highlight the name fields
      router.push('/dashboard/student/settings?tab=profile&highlight=name');
      return;
    }

    checkProfiling();
  }, [isAuthenticated, authLoading, user]);

  // Show loading while checking profiling or foundations
  // This prevents dashboard from rendering and making API calls before redirect
  if ((checkingProfiling || checkingFoundations) && isAuthenticated) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <Card className="p-8">
          <div className="text-center space-y-4">
            <Loader2 className="w-12 h-12 text-och-defender animate-spin mx-auto" />
            <div className="text-white text-lg">
              {checkingProfiling ? 'Checking profiling status...' : 'Checking Foundations status...'}
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // Always show the new dashboard - redirects happen in background
  return (
    <ErrorBoundary>
      <StudentDashboardHub />
    </ErrorBoundary>
  );
}
