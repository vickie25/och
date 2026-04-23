'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useParams, useSearchParams } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { getRedirectRoute } from '@/utils/redirect';
import { roleNamesFromUser, shouldRunStudentProfilerFlow } from '@/utils/loginStudentFlow';
import { getAccessToken, getRefreshToken } from '@/utils/auth';
import { Eye, EyeOff, ArrowRight, Lock, Mail, Sparkles } from 'lucide-react';
import { OchLogoMark } from '@/components/brand/OchLogo';
import type { LoginRequest } from '@/services/types';

const PERSONAS = {
  student: {
    name: 'Student',
    icon: '🎓',
    color: 'defender-blue',
    description: 'Begin your cyber defense journey',
    gradient: 'from-blue-500/20 via-blue-600/10 to-slate-900/30'
  },
  mentor: {
    name: 'Mentor',
    icon: '👨‍🏫',
    color: 'sahara-gold',
    description: 'Guide the next generation',
    gradient: 'from-yellow-500/20 via-yellow-600/10 to-slate-900/30'
  },
  admin: {
    name: 'Admin',
    icon: '⚡',
    color: 'sahara-gold',
    description: 'Full platform access',
    gradient: 'from-yellow-500/20 via-orange-600/10 to-slate-900/30'
  },
  director: {
    name: 'Program Director',
    icon: '👔',
    color: 'sahara-gold',
    description: 'Manage programs and operations',
    gradient: 'from-yellow-500/20 via-yellow-600/10 to-slate-900/30'
  },
  sponsor: {
    name: 'Sponsor/Employer',
    icon: '💼',
    color: 'sahara-gold',
    description: 'Support talent development',
    gradient: 'from-yellow-500/20 via-yellow-600/10 to-slate-900/30'
  },
  institution: {
    name: 'Institution',
    icon: '🏫',
    color: 'sahara-gold',
    description: 'Institution onboarding and management',
    gradient: 'from-yellow-500/20 via-yellow-600/10 to-slate-900/30'
  },
  analyst: {
    name: 'Analyst',
    icon: '📊',
    color: 'defender-blue',
    description: 'Access analytics and insights',
    gradient: 'from-blue-500/20 via-blue-600/10 to-slate-900/30'
  },
  finance: {
    name: 'Finance',
    icon: '💰',
    color: 'defender-blue',
    description: 'Manage billing and revenue operations',
    gradient: 'from-blue-500/20 via-blue-600/10 to-slate-900/30'
  },
  support: {
    name: 'Support',
    icon: '🛟',
    color: 'defender-blue',
    description: 'Internal support: tickets and problem tracking',
    gradient: 'from-cyan-500/20 via-blue-600/10 to-slate-900/30'
  },
};

const VALID_ROLES = Object.keys(PERSONAS);

const MFA_RESEND_COOLDOWN_SECONDS = 60;
const MFA_CODE_EXPIRY_SECONDS = 300; // 5 minutes

function formatCountdown(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function LoginForm() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const roleParam = params?.role as string;
  const urlRole = roleParam && VALID_ROLES.includes(roleParam) ? roleParam : 'student';

  const [currentRole, setCurrentRole] = useState(urlRole);

  useEffect(() => {
    if (urlRole !== currentRole) {
      setCurrentRole(urlRole);
    }
  }, [urlRole, currentRole]);

  const { login, isLoading, isAuthenticated, user, completeMFA, sendMFAChallenge } = useAuth();

  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
    device_fingerprint: 'web-' + Date.now(),
    device_name: 'Web Browser',
  });

  const [error, setError] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const hasRedirectedRef = useRef(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [mfaPending, setMfaPending] = useState<{
    refresh_token: string;
    mfa_method: string;
    mfa_methods_available?: string[];
  } | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaMethod, setMfaMethod] = useState<'totp' | 'sms' | 'email' | 'backup_codes'>('totp');
  const [mfaSending, setMfaSending] = useState(false);
  const [mfaSubmitting, setMfaSubmitting] = useState(false);
  const [resendCooldownSeconds, setResendCooldownSeconds] = useState(0);
  const [expirySecondsRemaining, setExpirySecondsRemaining] = useState(0);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedEmail = localStorage.getItem('remembered_email');
      const savedRememberMe = localStorage.getItem('remember_me') === 'true';
      if (savedEmail && savedRememberMe) {
        setFormData(prev => ({ ...prev, email: savedEmail }));
        setRememberMe(true);
      }
    }
  }, []);

  useEffect(() => {
    if (currentRole && !VALID_ROLES.includes(currentRole)) {
      router.push('/login');
    }
  }, [currentRole, router]);

  // Fallback: we have token in localStorage but middleware sent us back to login (no cookie).
  // Sync token to cookies via set-tokens, then redirect so the next request is authenticated.
  const localStorageRecoverRef = useRef(false);
  useEffect(() => {
    if (typeof window === 'undefined' || hasRedirectedRef.current || localStorageRecoverRef.current) return;
    const redirectTo = searchParams.get('redirect');
    if (!redirectTo || (!redirectTo.startsWith('/dashboard') && !redirectTo.startsWith('/onboarding/') && !redirectTo.startsWith('/students/'))) return;
    const accessToken = getAccessToken();
    const refreshToken = getRefreshToken();
    if (!accessToken) return;

    localStorageRecoverRef.current = true;
    (async () => {
      try {
        const { djangoClient } = await import('@/services/djangoClient');
        const userData = await djangoClient.auth.getCurrentUser();
        const res = await fetch('/api/auth/set-tokens', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            access_token: accessToken,
            refresh_token: refreshToken ?? '',
            user: userData,
          }),
        });
        if (res.ok) {
          window.location.replace(redirectTo);
        } else {
          localStorageRecoverRef.current = false;
        }
      } catch {
        localStorageRecoverRef.current = false;
      }
    })();
  }, [searchParams]);

  useEffect(() => {
    if (hasRedirectedRef.current) return;
    if (isLoggingIn || isRedirecting) return;
    if (isLoading) return;

    if (isAuthenticated && user) {
      const redirectTo = searchParams.get('redirect');
      if (redirectTo && (redirectTo.startsWith('/dashboard') || redirectTo.startsWith('/onboarding/'))) {
        hasRedirectedRef.current = true;
        router.push(redirectTo);
      }
    }
  }, [isAuthenticated, user, isLoading, isLoggingIn, isRedirecting, router, searchParams]);

  // Countdown for MFA resend cooldown and code expiry (SMS/email only)
  const isMfaSmsOrEmail = mfaPending && (mfaPending.mfa_method === 'sms' || mfaPending.mfa_method === 'email');
  useEffect(() => {
    if (!isMfaSmsOrEmail) return;
    const interval = setInterval(() => {
      setResendCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
      setExpirySecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [isMfaSmsOrEmail]);

  // Auto-send MFA code when landing on SMS/email step (backend does not send on login response)
  const mfaSentRef = useRef(false);
  useEffect(() => {
    if (!mfaPending?.refresh_token || (mfaPending.mfa_method !== 'sms' && mfaPending.mfa_method !== 'email')) {
      mfaSentRef.current = false;
      return;
    }
    if (mfaSentRef.current) return;
    mfaSentRef.current = true;
    const method = mfaPending.mfa_method === 'sms' ? 'sms' : 'email';
    sendMFAChallenge(mfaPending.refresh_token, method).catch((e: any) => {
      mfaSentRef.current = false;
      setError(e?.data?.detail || e?.message || 'Failed to send verification code');
    });
  }, [mfaPending?.refresh_token, mfaPending?.mfa_method, sendMFAChallenge]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoggingIn(true);
    setIsRedirecting(false);

    try {

      if (rememberMe && typeof window !== 'undefined') {
        localStorage.setItem('remembered_email', formData.email);
        localStorage.setItem('remember_me', 'true');
      } else if (typeof window !== 'undefined') {
        localStorage.removeItem('remembered_email');
        localStorage.removeItem('remember_me');
      }

      const result = await login(formData);

      // MFA required — show MFA step without throwing (backend sends preferred method: TOTP → email → SMS)
      if (result && 'mfaRequired' in result && result.mfaRequired && result.refresh_token) {
        const backendMethod = (result.mfa_method || 'totp').toLowerCase();
        const available: string[] = Array.isArray((result as any).mfa_methods_available)
          ? (result as any).mfa_methods_available
          : [backendMethod];
        setMfaPending({
          refresh_token: result.refresh_token,
          mfa_method: backendMethod,
          mfa_methods_available: available,
        });
        if (backendMethod === 'sms' || backendMethod === 'email') {
          setMfaMethod(backendMethod === 'sms' ? 'sms' : 'email');
          setResendCooldownSeconds(MFA_RESEND_COOLDOWN_SECONDS);
          setExpirySecondsRemaining(MFA_CODE_EXPIRY_SECONDS);
        } else {
          setMfaMethod((backendMethod === 'backup_codes' ? 'backup_codes' : 'totp') as 'totp' | 'sms' | 'email' | 'backup_codes');
        }
        setMfaCode('');
        setError(null);
        setIsLoggingIn(false);
        return;
      }

      if (!result || !('user' in result) || !result.user) {
        throw new Error('Login failed: No user data received');
      }

      const token = result.access_token || localStorage.getItem('access_token');

      if (!token) {
        throw new Error('Authentication token not found');
      }

      localStorage.setItem('access_token', token);

      // CRITICAL: Wait for cookies to be set by the browser and verify they exist
      // In production, cookies take time to be written
      let cookiesSet = false;
      let attempts = 0;
      const maxAttempts = 3;
      
      while (!cookiesSet && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
        
        // Check if access_token cookie exists
        const cookies = document.cookie.split(';');
        const hasAccessToken = cookies.some(c => c.trim().startsWith('access_token='));
        
        if (hasAccessToken) {
          cookiesSet = true;
        }
      }

      const redirectTo = searchParams.get('redirect');

      const loginPrimaryRole =
        typeof (result as { primary_role?: string }).primary_role === 'string'
          ? String((result as { primary_role?: string }).primary_role).trim()
          : '';

      let updatedUser = result?.user || user;

      const { djangoClient } = await import('@/services/djangoClient');
      let retries = 0;
      while ((!updatedUser?.roles || updatedUser.roles.length === 0) && retries < 3) {
        await new Promise((resolve) => setTimeout(resolve, 200));
        try {
          const u = await djangoClient.auth.getCurrentUser();
          if (u?.roles && u.roles.length > 0) {
            updatedUser = u;
            break;
          }
        } catch {
          // ignore transient /auth/me failures
        }
        retries++;
      }

      if (!updatedUser || !updatedUser.roles || updatedUser.roles.length === 0) {
        try {
          const fullUser = await djangoClient.auth.getCurrentUser();
          if (fullUser) updatedUser = fullUser;
        } catch {
          // Ignore fetch errors; continue with existing user state
        }
      }

      if ((!updatedUser?.roles || updatedUser.roles.length === 0) && loginPrimaryRole) {
        updatedUser = { ...updatedUser, roles: [{ role: loginPrimaryRole }] };
      }

      const roleNames = roleNamesFromUser(updatedUser);

      // Student/mentee onboarding — skip for staff and anyone whose primary role is not learner
      if (shouldRunStudentProfilerFlow(roleNames, loginPrimaryRole)) {
        // Students are treated as email-verified (onboarding link is the verification).
        const emailVerified = true;
        const mfaEnabled = updatedUser?.mfa_enabled || false;
        const profilingComplete = updatedUser?.profiling_complete ?? false;

        // Step 2: MFA setup (optional but recommended)
        // Note: We'll skip MFA requirement for now to not block onboarding
        // Users can set it up later in settings
        
        if (!profilingComplete) {
          setIsRedirecting(true);
          hasRedirectedRef.current = true;
          window.location.href = redirectTo || '/onboarding/ai-profiler';
          return;
        }
        
        // Django says complete, optionally verify with FastAPI (non-blocking)
        // Don't block redirect if FastAPI check fails - Django is source of truth
        try {
          const { fastapiClient } = await import('@/services/fastapiClient');
          const fastapiStatus = await Promise.race([
            fastapiClient.profiling.checkStatus(),
            new Promise<{ completed: boolean }>((resolve) => setTimeout(() => resolve({ completed: true }), 1500)),
          ]);
          if (!fastapiStatus.completed) {
            setIsRedirecting(true);
            hasRedirectedRef.current = true;
            window.location.href = '/onboarding/ai-profiler';
            return;
          }
        } catch {
          // FastAPI unavailable - trust Django's profiling_complete; continue to dashboard
        }
      } else if (
        (result as { profiling_required?: boolean }).profiling_required &&
        shouldRunStudentProfilerFlow(roleNames, loginPrimaryRole)
      ) {
        setIsRedirecting(true);
        hasRedirectedRef.current = true;
        router.push('/profiling');
        return;
      }

      // CRITICAL: Check for mentor role FIRST before any route determination
      // Mentors should NEVER be redirected to student dashboard
      const userRoles = updatedUser?.roles || [];
      const hasMentorRole = userRoles.some((r: any) => {
        const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
        return roleName === 'mentor';
      });

      // Initialize route variable
      let route: string;
      
      // CRITICAL: If user is a mentor, ALWAYS use mentor dashboard - NO EXCEPTIONS
      if (hasMentorRole) {
        route = '/dashboard/mentor';
      } else {
        // Only determine route for non-mentors
        route = '/dashboard/student'; // Default fallback
        
        let dashboardFromCookie: string | null = null;
        if (typeof document !== 'undefined') {
          const cookies = document.cookie.split(';');
          const dashboardCookie = cookies.find(c => c.trim().startsWith('och_dashboard='));
          if (dashboardCookie) {
            dashboardFromCookie = dashboardCookie.split('=')[1]?.trim() || null;
          }
        }

        if (redirectTo && (redirectTo.startsWith('/dashboard') || redirectTo.startsWith('/students/') || redirectTo.startsWith('/onboarding/'))) {
          route = redirectTo;
          console.log('[Login] Using redirectTo route:', route);
        } else {
          if (!updatedUser || !updatedUser.roles || updatedUser.roles.length === 0) {
            if (dashboardFromCookie) {
              route = dashboardFromCookie;
              console.log('[Login] Using dashboard cookie route:', route);
            } else {
              route = '/dashboard/student';
              console.log('[Login] Using default student route:', route);
            }
          } else {
            // Use getRedirectRoute as the primary routing mechanism
            // This ensures users are routed to the correct dashboard based on their role priority
            route = getRedirectRoute(updatedUser);
            console.log('[Login] Route from getRedirectRoute:', route);
            console.log('[Login] User roles:', updatedUser?.roles);
          }
        }
      }

      console.log('[Login] Final route before validation:', route);
      
      // CRITICAL: Final mentor check - ensure mentors NEVER get student dashboard
      // This is a safety net that runs AFTER all route determination logic
      if (updatedUser?.roles) {
        const hasMentorRoleFinal = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
          return roleName === 'mentor';
        });
        
        if (hasMentorRoleFinal && route !== '/dashboard/mentor') {
          route = '/dashboard/mentor';
        }
      }

      // CRITICAL: Check for mentor role AGAIN - mentors should NEVER be associated with student routes
      if (updatedUser?.roles) {
        const hasMentorRoleCheck = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
          return roleName === 'mentor';
        });
        if (hasMentorRoleCheck && route === '/dashboard/student') {
          route = '/dashboard/mentor';
        }
      }

      // Check for other roles that should override default student route
      if (route === '/dashboard/student' && updatedUser?.roles) {
        // Check for sponsor role
        const hasSponsorRole = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
          return roleName === 'sponsor_admin' || roleName === 'sponsor';
        });
        if (hasSponsorRole) {
          route = '/dashboard/sponsor';
        }
        // Check for finance role — must go to finance dashboard, never student
        const hasFinanceRole = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim();
          return roleName === 'finance' || roleName === 'finance_admin';
        });
        if (hasFinanceRole) {
          route = '/dashboard/finance';
        }
        // Check for support role — must go to support dashboard, never student
        const hasSupportRole = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim();
          return roleName === 'support';
        });
        if (hasSupportRole) {
          route = '/support/dashboard';
        }
      }

      if (!route || (!route.startsWith('/dashboard') && !route.startsWith('/students/'))) {
        if (updatedUser?.roles) {
          const hasMentorRoleCheck = updatedUser.roles.some((r: any) => {
            const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
            return roleName === 'mentor';
          });
          if (hasMentorRoleCheck) {
            route = '/dashboard/mentor';
          } else {
            // Only fallback to student if user is NOT a mentor
            route = '/dashboard/student';
          }
        } else {
          // No roles - default to student (but this should rarely happen)
          route = '/dashboard/student';
        }
      }

      // Additional validation for dashboard routes
      if (route.startsWith('/dashboard/')) {
        const { isValidDashboardRoute, getFallbackRoute } = await import('@/utils/redirect');
        if (!isValidDashboardRoute(route)) {
          if (updatedUser?.roles?.some((r: any) => {
            const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
            return roleName === 'mentor';
          })) {
            route = '/dashboard/mentor';
          } else {
            route = getFallbackRoute(updatedUser);
          }
        }
      }

      // CRITICAL: ABSOLUTE FINAL CHECK - Force mentor route if mentor detected
      // This runs RIGHT BEFORE redirect to ensure nothing can override it
      if (updatedUser?.roles && Array.isArray(updatedUser.roles)) {
        const finalMentorCheck = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim();
          return roleName === 'mentor';
        });
        if (finalMentorCheck && route !== '/dashboard/mentor') {
          route = '/dashboard/mentor';
        }
        // CRITICAL: Force finance route if finance detected — finance must NEVER land on student dashboard
        const finalFinanceCheck = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim();
          return roleName === 'finance' || roleName === 'finance_admin';
        });
        if (finalFinanceCheck && route === '/dashboard/student') {
          route = '/dashboard/finance';
        }
        // CRITICAL: Force support route if support detected — support must NEVER land on student dashboard
        const finalSupportCheck = updatedUser.roles.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim();
          return roleName === 'support';
        });
        if (finalSupportCheck && route === '/dashboard/student') {
          route = '/support/dashboard';
        }
      }

      // Before redirect: if destination requires 2 MFA, check now so we never show dashboard URL with "Verifying..."
      const ROUTES_REQUIRING_TWO_MFA = ['/dashboard/director', '/dashboard/mentor', '/dashboard/admin', '/finance', '/dashboard/analyst', '/support'];
      const needsMfaCheck = ROUTES_REQUIRING_TWO_MFA.some((r) => route === r || route.startsWith(r + '/'));
      if (needsMfaCheck) {
        try {
          const { djangoClient } = await import('@/services/djangoClient');
          const res = await Promise.race([
            djangoClient.auth.getMFAMethods(),
            new Promise<{ methods: any[] }>((resolve) => setTimeout(() => resolve({ methods: [] }), 1500)),
          ]);
          const count = (res.methods || []).length;
          if (count < 2) {
            route = '/dashboard/mfa-required';
            if (typeof window !== 'undefined') window.sessionStorage.removeItem('mfa_compliant');
          } else {
            if (typeof window !== 'undefined') window.sessionStorage.setItem('mfa_compliant', '1');
          }
        } catch (_e) {
          route = '/dashboard/mfa-required';
          if (typeof window !== 'undefined') window.sessionStorage.removeItem('mfa_compliant');
        }
      }
      setIsRedirecting(true);
      setIsLoggingIn(false);
      hasRedirectedRef.current = true;

      if (typeof window !== 'undefined') {
        try {
          window.location.replace(route);
          setTimeout(() => {
            if (window.location.pathname.includes('/login/')) {
              window.location.href = route;
            }
          }, 100);
        } catch {
          window.location.href = route;
        }
      }

      setTimeout(() => {
        if (typeof window !== 'undefined' && window.location.pathname.includes('/login/')) {
          router.replace(route);
        }
      }, 1000);

    } catch (err: any) {
      setIsLoggingIn(false);
      setIsRedirecting(false);

      if (user && user.roles && user.roles.length > 0) {
        let fallbackRoute = getRedirectRoute(user);
        if (user.roles?.some((r: any) => {
          const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
          return roleName === 'mentor';
        }) && fallbackRoute === '/dashboard/student') {
          fallbackRoute = '/dashboard/mentor';
        }
        setTimeout(() => {
          window.location.replace(fallbackRoute);
        }, 500);
        return; // Exit early to prevent error display
      }
      
      // Also check if login was successful but error occurred during redirect logic
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const { djangoClient } = await import('@/services/djangoClient');
          const currentUser = await djangoClient.auth.getCurrentUser();
          if (currentUser?.roles?.length) {
            let redirectRoute = getRedirectRoute(currentUser);
            if (currentUser.roles.some((r: any) => {
              const roleName = typeof r === 'string' ? r : (r?.role || r?.name || '').toLowerCase().trim();
              return roleName === 'mentor';
            }) && redirectRoute === '/dashboard/student') {
              redirectRoute = '/dashboard/mentor';
            }
            setTimeout(() => window.location.replace(redirectRoute), 500);
            return;
          }
        } catch {
          // Ignore
        }
      }

      let message = 'Login failed. Please check your credentials.';

      if (err?.mfa_required && err?.refresh_token) {
        const backendMethod = (err.mfa_method || 'totp').toLowerCase();
        const available: string[] = Array.isArray(err.mfa_methods_available) ? err.mfa_methods_available : [backendMethod];
        setMfaPending({
          refresh_token: err.refresh_token,
          mfa_method: backendMethod,
          mfa_methods_available: available,
        });
        if (backendMethod === 'sms' || backendMethod === 'email') {
          setMfaMethod(backendMethod === 'sms' ? 'sms' : 'email');
          setResendCooldownSeconds(MFA_RESEND_COOLDOWN_SECONDS);
          setExpirySecondsRemaining(MFA_CODE_EXPIRY_SECONDS);
        } else {
          setMfaMethod((backendMethod === 'backup_codes' ? 'backup_codes' : 'totp') as 'totp' | 'sms' | 'email' | 'backup_codes');
        }
        setMfaCode('');
        setError(null);
        setIsLoggingIn(false);
        return;
      } else if (err?.data?.detail) {
        message = err.data.detail;
        // Check for connection errors in detail
        if (message.includes('Cannot connect') || message.includes('backend server')) {
          message = 'Cannot connect to backend server. Please ensure the Django API is running on port 8000.';
        } else if (message === 'Invalid credentials') {
          // Provide more helpful message for invalid credentials
          message = 'Invalid email or password. Please check your credentials and try again.';
        }
      } else if (err?.data?.error) {
        message = err.data.error;
      } else if (err?.detail) {
        message = err.detail;
      } else if (err?.message) {
        message = err.message;
        if (err.message.includes('fetch') || err.message.includes('network') || err.message.includes('ECONNREFUSED') || err.message.includes('Cannot connect')) {
          message = 'Cannot connect to backend server. Please ensure the Django API is running on port 8000.';
        }
      }

      setError(message);
    }
  };

  const switchRole = (newRole: string) => {
    if (newRole === currentRole) {
      return;
    }

    setCurrentRole(newRole);
    const redirectTo = searchParams.get('redirect');
    const baseUrl = newRole === 'student' ? '/login' : `/login/${newRole}`;
    const newUrl = redirectTo ? `${baseUrl}?redirect=${encodeURIComponent(redirectTo)}` : baseUrl;
    router.replace(newUrl);
  };

  return (
    <div className="min-h-screen bg-[#06090F] text-[#E2E8F0] font-sans">
      <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(10,14,26,1),_transparent_55%),radial-gradient(circle_at_top_left,_rgba(245,158,11,0.12),_transparent_55%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.12),_transparent_55%)]" />
      <div className="pointer-events-none fixed inset-0 -z-10 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '50px 50px' }} />

      {/* Top nav matching homepage */}
      <header className="border-b border-[rgba(255,255,255,0.06)] bg-[rgba(6,9,15,0.85)] backdrop-blur-[20px]">
        <nav className="max-w-[1140px] mx-auto px-6">
          <div className="flex h-[70px] items-center justify-between">
            <button
              type="button"
              onClick={() => router.push('/')}
              className="flex items-center gap-3 min-w-0"
            >
              <OchLogoMark variant="white" className="h-9 max-w-[200px]" priority />
            </button>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => router.push('/register')}
                className="relative inline-flex items-center gap-2 rounded-full px-[30px] py-[14px] text-[13px] font-bold text-[#0A0E1A] bg-gradient-to-r from-[#F59E0B] to-[#D97706] shadow-[0_0_24px_rgba(245,158,11,0.55)] hover:shadow-[0_0_30px_rgba(245,158,11,0.7)] hover:-translate-y-0.5 transition-all duration-200"
              >
                <span>Start Free</span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </nav>
      </header>

      <div className="flex items-center justify-center px-4 py-12 sm:py-16">
        <div className="w-full max-w-[440px] relative z-10 rounded-[18px] border border-[rgba(255,255,255,0.05)] bg-[rgba(255,255,255,0.03)] backdrop-blur-xl shadow-[0_18px_60px_rgba(0,0,0,0.85)] p-8">
          <div className="flex flex-col gap-3 mb-6">
            <OchLogoMark variant="white" className="h-8 max-w-[200px]" priority />
            <div>
              <h1 className="font-heading text-xl font-bold tracking-tight text-[#E2E8F0]">Sign in</h1>
              <p className="text-[13px] text-[#94A3B8]">Ongoza CyberHub — secure access</p>
            </div>
          </div>

          <h2 className="font-heading text-2xl font-bold text-[#E2E8F0] mb-1">Welcome back</h2>
          <p className="text-[#94A3B8] text-sm mb-6">Sign in to continue your cybersecurity journey</p>

          {error && (
            <div className="mb-5 p-4 bg-red-500/10 border border-red-500/30 rounded-xl" role="alert">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {isRedirecting && !error && (
            <div className="mb-5 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl" role="status">
              <div className="flex items-center gap-2 text-emerald-400 text-sm">
                <div className="animate-spin h-4 w-4 border-2 border-emerald-400 border-t-transparent rounded-full"></div>
                <span>Login successful! Redirecting to your dashboard...</span>
              </div>
            </div>
          )}

          {mfaPending ? (
            <div className="space-y-5">
              <div>
                <h2 className="text-xl font-bold text-white mb-1">Verify your identity</h2>
                <p className="text-slate-400 text-sm">
                  {mfaMethod === 'totp'
                    ? 'Enter the code from your authenticator app.'
                    : mfaMethod === 'backup_codes'
                    ? 'Enter one of your backup codes.'
                    : mfaMethod === 'sms'
                    ? 'Enter the code we sent to your phone.'
                    : 'Enter the code we sent to your email.'}
                </p>
              </div>
              {(mfaMethod === 'sms' || mfaMethod === 'email') && (
                <div className="space-y-2">
                  <p className="text-slate-400 text-xs">
                    {expirySecondsRemaining > 0
                      ? `Code expires in ${formatCountdown(expirySecondsRemaining)}`
                      : 'Code expired. Request a new code below.'}
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full py-2 rounded-lg border-slate-600 text-slate-300"
                    disabled={mfaSending || resendCooldownSeconds > 0}
                    onClick={async () => {
                      setError(null);
                      setMfaSending(true);
                      try {
                        await sendMFAChallenge(mfaPending.refresh_token, mfaMethod === 'sms' ? 'sms' : 'email');
                        setError(null);
                        setResendCooldownSeconds(MFA_RESEND_COOLDOWN_SECONDS);
                        setExpirySecondsRemaining(MFA_CODE_EXPIRY_SECONDS);
                      } catch (e: any) {
                        setError(e?.data?.detail || e?.message || 'Failed to send code');
                      } finally {
                        setMfaSending(false);
                      }
                    }}
                  >
                    {mfaSending
                      ? 'Sending...'
                      : resendCooldownSeconds > 0
                        ? `Resend code (${formatCountdown(resendCooldownSeconds)})`
                        : mfaMethod === 'sms'
                          ? 'Resend code via SMS'
                          : 'Resend code via email'}
                  </Button>
                  {(() => {
                    const available = mfaPending.mfa_methods_available ?? [mfaPending.mfa_method];
                    const others = available.filter((m) => m !== mfaMethod && (m === 'totp' || m === 'email' || m === 'sms'));
                    if (others.length === 0) return null;
                    const labels: Record<string, string> = { totp: 'Use authenticator app', email: 'Use email instead', sms: 'Use SMS instead' };
                    return (
                      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1">
                        {others.map((method) => (
                          <button
                            key={method}
                            type="button"
                            className="text-sm text-och-steel hover:text-och-mint transition-colors disabled:opacity-50"
                            disabled={mfaSending || resendCooldownSeconds > 0}
                            onClick={async () => {
                              setMfaCode('');
                              setError(null);
                              setMfaMethod(method as 'totp' | 'sms' | 'email');
                              if (method === 'email' || method === 'sms') {
                                setMfaSending(true);
                                try {
                                  await sendMFAChallenge(mfaPending.refresh_token, method);
                                  setResendCooldownSeconds(MFA_RESEND_COOLDOWN_SECONDS);
                                  setExpirySecondsRemaining(MFA_CODE_EXPIRY_SECONDS);
                                } catch (e: any) {
                                  setError(e?.data?.detail || e?.message || 'Failed to send code');
                                } finally {
                                  setMfaSending(false);
                                }
                              }
                            }}
                          >
                            {labels[method] ?? method}
                          </button>
                        ))}
                      </div>
                    );
                  })()}
                </div>
              )}
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (!mfaCode.trim() || !mfaPending) return;
                  setError(null);
                  setMfaSubmitting(true);
                  try {
                    const result = await completeMFA({
                      refresh_token: mfaPending.refresh_token,
                      code: mfaCode.trim(),
                      method: mfaMethod,
                    });
                    setMfaPending(null);
                    setMfaCode('');
                    setResendCooldownSeconds(0);
                    setExpirySecondsRemaining(0);
                    setIsRedirecting(true);
                    const { getRedirectRoute, isValidDashboardRoute } = await import('@/utils/redirect');
                    const u = result?.user;
                    const names = roleNamesFromUser(u);
                    const mfaPrimary =
                      typeof (result as { primary_role?: string }).primary_role === 'string'
                        ? String((result as { primary_role?: string }).primary_role).trim()
                        : '';
                    const needsProfiling =
                      (u as { profiling_complete?: boolean })?.profiling_complete === false &&
                      shouldRunStudentProfilerFlow(names, mfaPrimary || null);
                    const redirectTo = (searchParams.get('redirect') ?? '').replace(/\/$/, '') || '';
                    const useRedirectParam = redirectTo && (redirectTo.startsWith('/dashboard') || redirectTo.startsWith('/onboarding/') || redirectTo.startsWith('/students/')) && (isValidDashboardRoute(redirectTo) || ['/dashboard/director', '/dashboard/admin', '/dashboard/mentor', '/dashboard/sponsor', '/dashboard/institution', '/dashboard/analyst', '/dashboard/employer', '/dashboard/finance', '/finance/dashboard', '/support/dashboard'].some(r => redirectTo === r || redirectTo.startsWith(r + '/') || redirectTo.startsWith(r + '?')));
                    let redirectRoute = needsProfiling
                      ? '/profiling'
                      : (useRedirectParam ? redirectTo : (u ? getRedirectRoute(u) : '/dashboard/student'));

                    // CRITICAL: Final check for finance role before redirect
                    if (u?.roles) {
                      const hasFinanceRole = u.roles.some((r: any) => {
                        const roleName = typeof r === 'string' ? r : (r?.role || r?.name || r?.role_display_name || '').toLowerCase().trim();
                        return roleName === 'finance' || roleName === 'finance_admin';
                      });
                      if (hasFinanceRole && redirectRoute === '/dashboard/student') {
                        redirectRoute = '/dashboard/finance';
                      }
                    }

                    let cookiesSet = false;
                    let attempts = 0;
                    const maxAttempts = 10;
                    while (!cookiesSet && attempts < maxAttempts) {
                      await new Promise(resolve => setTimeout(resolve, 200));
                      attempts++;
                      const cookies = document.cookie.split(';');
                      if (cookies.some(c => c.trim().startsWith('access_token='))) cookiesSet = true;
                    }

                    if (typeof window !== 'undefined') {
                      window.location.replace(redirectRoute);
                    } else {
                      router.push(redirectRoute);
                    }
                  } catch (e: any) {
                    setError(e?.data?.detail || e?.message || 'Invalid code');
                  } finally {
                    setMfaSubmitting(false);
                  }
                }}
                className="space-y-4"
              >
                <div className="space-y-2">
                  <label htmlFor="mfa-code" className="text-sm font-medium text-slate-300">
                    Verification code
                  </label>
                  <input
                    id="mfa-code"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-slate-950/70 border border-white/10 text-[#E2E8F0] placeholder:text-slate-500 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60 transition-all"
                    placeholder={mfaMethod === 'backup_codes' ? 'Backup code' : '000000'}
                  />
                </div>
                {((mfaPending.mfa_methods_available?.includes('totp')) ?? (mfaPending.mfa_method === 'totp')) && (mfaMethod === 'totp' || mfaMethod === 'backup_codes') && (
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setMfaMethod('totp')}
                        className={`px-3 py-1.5 text-sm rounded-lg ${mfaMethod === 'totp' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50' : 'border border-slate-600 text-slate-400 hover:text-slate-300'}`}
                      >
                        Authenticator app
                      </button>
                      <button
                        type="button"
                        onClick={() => setMfaMethod('backup_codes')}
                        className={`px-3 py-1.5 text-sm rounded-lg ${mfaMethod === 'backup_codes' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50' : 'border border-slate-600 text-slate-400 hover:text-slate-300'}`}
                      >
                        Backup code
                      </button>
                    </div>
                    {(() => {
                      const available = mfaPending.mfa_methods_available ?? [mfaPending.mfa_method];
                      const others = available.filter((m) => m === 'email' || m === 'sms');
                      if (others.length === 0) return null;
                      const labels: Record<string, string> = { email: 'Use email instead', sms: 'Use SMS instead' };
                      return (
                        <div className="flex flex-wrap justify-center gap-x-4">
                          {others.map((method) => (
                            <button
                              key={method}
                              type="button"
                              className="text-sm text-och-steel hover:text-och-mint transition-colors"
                              onClick={async () => {
                                setMfaCode('');
                                setError(null);
                                setMfaMethod(method as 'email' | 'sms');
                                setMfaSending(true);
                                try {
                                  await sendMFAChallenge(mfaPending.refresh_token, method);
                                  setResendCooldownSeconds(MFA_RESEND_COOLDOWN_SECONDS);
                                  setExpirySecondsRemaining(MFA_CODE_EXPIRY_SECONDS);
                                } catch (e: any) {
                                  setError(e?.data?.detail || e?.message || 'Failed to send code');
                                } finally {
                                  setMfaSending(false);
                                }
                              }}
                            >
                              {labels[method]}
                            </button>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                )}
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    disabled={!mfaCode.trim() || mfaSubmitting}
                    className="flex-1 py-3 rounded-xl bg-gradient-to-r from-[#F59E0B] to-[#D97706] text-[#0A0E1A] font-semibold shadow-[0_0_24px_rgba(245,158,11,0.55)] hover:shadow-[0_0_30px_rgba(245,158,11,0.7)] transition-all duration-200"
                  >
                    {mfaSubmitting ? 'Verifying...' : 'Verify'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="py-3 rounded-xl border-[rgba(255,255,255,0.15)] text-[#E2E8F0] hover:border-[rgba(245,158,11,0.6)] hover:text-[#F59E0B] transition-colors duration-200"
                    onClick={() => { setMfaPending(null); setMfaCode(''); setError(null); setResendCooldownSeconds(0); setExpirySecondsRemaining(0); }}
                  >
                    Back
                  </Button>
                </div>
              </form>
            </div>
          ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-[#94A3B8] flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#F59E0B]" />
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 rounded-xl bg-slate-950/70 border border-white/10 text-[#E2E8F0] placeholder:text-slate-500 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60 transition-all"
                placeholder="your.email@example.com"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-[#94A3B8] flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#F59E0B]" />
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-4 py-3 pr-12 rounded-xl bg-slate-950/70 border border-white/10 text-[#E2E8F0] placeholder:text-slate-500 focus:outline-none focus:border-amber-400/70 focus:ring-1 focus:ring-amber-400/60 transition-all"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#94A3B8] hover:text-[#F59E0B] transition-colors p-1"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-white/20 bg-slate-950/70 text-[#F59E0B] focus:ring-[#F59E0B] focus:ring-offset-0 focus:ring-2 cursor-pointer"
                />
                <span className="text-sm text-[#94A3B8] group-hover:text-[#E2E8F0] transition-colors">
                  Remember me
                </span>
              </label>

              <button
                type="button"
                onClick={() => router.push('/forgot-password')}
                className="text-sm text-[#F59E0B] hover:text-amber-300 transition-colors font-medium"
              >
                Forgot Password?
              </button>
            </div>

            <Button
              type="submit"
              disabled={isLoading || isLoggingIn || isRedirecting}
              className="w-full py-3 text-base font-semibold rounded-xl bg-gradient-to-r from-[#F59E0B] to-[#D97706] text-[#0A0E1A] shadow-[0_0_24px_rgba(245,158,11,0.55)] hover:shadow-[0_0_30px_rgba(245,158,11,0.7)] hover:-translate-y-0.5 transition-all duration-200"
            >
              {isRedirecting ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Redirecting...
                </span>
              ) : isLoggingIn ? (
                <span className="flex items-center gap-2">
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Signing in...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </Button>
          </form>
          )}

          {!mfaPending && (
          <>
          {/* Google OAuth Button */}
          <div className="mt-4">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/5"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-[rgba(255,255,255,0.03)] text-[#64748B]">or</span>
              </div>
            </div>
            <div className="mt-4 space-y-2">
              <Button
                type="button"
                variant="outline"
                className="w-full py-3 text-base rounded-xl border-[rgba(255,255,255,0.15)] text-[#E2E8F0] hover:border-[rgba(245,158,11,0.6)] hover:text-[#F59E0B] transition-colors duration-200 flex items-center justify-center gap-3"
                  onClick={async () => {
                  try {
                      const query = `role=${encodeURIComponent(currentRole)}&mode=login`;
                      const relativePath = `/api/v1/auth/google/initiate?${query}`;
                      const configuredApiBase = process.env.NEXT_PUBLIC_DJANGO_API_URL;

                      const buildInitiateUrl = (base: string) => {
                        const normalized = base.replace(/\/$/, '');
                        if (normalized.endsWith('/api/v1')) {
                          return `${normalized}/auth/google/initiate?${query}`;
                        }
                        if (normalized.endsWith('/api')) {
                          return `${normalized}/v1/auth/google/initiate?${query}`;
                        }
                        return `${normalized}/api/v1/auth/google/initiate?${query}`;
                      };

                      const isLocalFront =
                        typeof window !== 'undefined' &&
                        ['localhost', '127.0.0.1'].includes(window.location.hostname);

                      const localDirectBase = isLocalFront
                        ? `${window.location.protocol}//${window.location.hostname}:8000`
                        : null;

                      // Never call production Django from localhost (CORS + wrong stack).
                      const isBadConfiguredApiBase =
                        !!configuredApiBase &&
                        /localhost|127\.0\.0\.1/i.test(configuredApiBase) &&
                        !isLocalFront;

                      const absoluteUrl =
                        configuredApiBase && !isLocalFront && !isBadConfiguredApiBase
                          ? buildInitiateUrl(configuredApiBase)
                          : null;
                      const localDirectUrl = localDirectBase ? buildInitiateUrl(localDirectBase) : null;

                      const endpoints = [relativePath, localDirectUrl, absoluteUrl].filter(Boolean) as string[];
                      let lastError = 'Failed to initiate Google sign-in';

                      for (const endpoint of endpoints) {
                        try {
                          const response = await fetch(endpoint, { credentials: 'include' });
                          const data = await response.json().catch(() => ({}));
                          if (response.status === 429) {
                            // Don't retry other endpoints; this is a server throttle.
                            throw new Error(
                              (typeof data?.detail === 'string' && data.detail) ||
                                'Too many requests. Please wait a minute and try again.'
                            );
                          }
                          if (response.ok && data?.auth_url) {
                            window.location.replace(data.auth_url);
                            return;
                          }

                          lastError =
                            (typeof data?.detail === 'string' && data.detail) ||
                            (typeof data?.error === 'string' && data.error) ||
                            `HTTP ${response.status}` ||
                            lastError;
                        } catch {
                          lastError = 'Failed to initiate Google sign-in';
                        }
                      }

                      throw new Error(lastError || 'No authorization URL received from server');
                    } catch (err: any) {
                      setError(err?.message || 'Failed to initiate Google sign-in');
                    }
                  }}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Continue with Google
              </Button>
              <p className="text-xs text-[#94A3B8] text-center">
                After signing in with Google, you will receive a <span className="font-semibold">Get Started</span> email.
                Open that email and click the button inside to begin your onboarding. You will not start directly in the profiler.
              </p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-white/5">
            <p className="text-center text-sm text-[#94A3B8] mb-3">
              Don't have an account?
            </p>
            <Button
              variant="outline"
              className="w-full py-3 text-base rounded-xl border-[rgba(255,255,255,0.15)] text-[#E2E8F0] hover:border-[rgba(245,158,11,0.6)] hover:text-[#F59E0B] transition-colors duration-200"
              onClick={() => router.push('/register')}
            >
              Create Account
            </Button>
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function RoleLoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400">Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
