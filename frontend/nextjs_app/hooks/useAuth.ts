/**
 * Authentication hook
 * Manages login, logout, token refresh, and user session
 */

'use client';

import React, { useState, useEffect, useCallback, useContext } from 'react';
import { useRouter } from 'next/navigation';
import { apiGateway } from '../services/apiGateway';
import { djangoClient } from '../services/djangoClient';
import { ApiError } from '../utils/fetcher';
import { setAuthTokens, clearAuthTokens, getAccessToken, isAuthenticated } from '../utils/auth';
import type { LoginRequest, User } from '../services/types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginRequest) => Promise<any>;
  logout: () => Promise<void>;
  refresh: () => Promise<any>;
  reloadUser: () => Promise<void>;
  completeMFA: (params: {
    refresh_token: string;
    code: string;
    method: 'totp' | 'sms' | 'email' | 'backup_codes';
  }) => Promise<{ user: User; access_token: string }>;
  sendMFAChallenge: (refresh_token: string, method?: 'email' | 'sms') => Promise<any>;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

function useProvideAuth(): AuthContextValue {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  /**
   * Load current user from API
   */
  const loadUser = useCallback(async () => {
    // Set loading state first
    setState(prev => ({ ...prev, isLoading: true }));
    
    if (!isAuthenticated()) {
      setState({ user: null, isLoading: false, isAuthenticated: false });
      return;
    }

    try {
      const user = await djangoClient.auth.getCurrentUser();
      setState({ user, isLoading: false, isAuthenticated: true });
    } catch (error: any) {
      const httpStatus = error?.status || error?.response?.status || 0;
      const isGenuine401 = httpStatus === 401;

      // Only clear tokens when Django explicitly rejects the token (401).
      // For 503 (Django down / network error / timeout), keep existing tokens
      // so the user is not logged out on a transient backend failure.
      if (isGenuine401) {
        clearAuthTokens();
        setState({ user: null, isLoading: false, isAuthenticated: false });
      } else {
        // Transient error (503, network, timeout) — do NOT clear tokens.
        // Keep isAuthenticated: false so protected routes still block rendering,
        // but the tokens remain so the next request can succeed.
        setState((prev) => ({ ...prev, user: null, isLoading: false, isAuthenticated: false }));
      }
    }
  }, []);

  /**
   * Login user
   */
  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      // Django login via apiGateway (JSON body). Middleware only sees cookies — sync via /api/auth/set-tokens.
      let responseData: any;
      try {
        responseData = await apiGateway.post<any>('/auth/login', credentials, { skipAuth: true });
      } catch (fetchError: unknown) {
        if (fetchError instanceof ApiError) {
          const d = fetchError.data as any;
          const message =
            (typeof d?.detail === 'string' && d.detail) ||
            (Array.isArray(d?.detail) && d.detail.length ? String(d.detail[0]) : null) ||
            d?.error ||
            d?.message ||
            fetchError.message ||
            'Login failed';
          const error = new Error(message);
          (error as any).data = fetchError.data;
          (error as any).status = fetchError.status;
          (error as any).code = d?.code;
          throw error;
        }
        const errorMsg = fetchError instanceof Error ? fetchError.message : 'Unknown error';
        const isConnectionError =
          errorMsg.includes('fetch failed') ||
          errorMsg.includes('Failed to fetch') ||
          errorMsg.includes('NetworkError') ||
          errorMsg.includes('ECONNREFUSED');

        const error = new Error(
          isConnectionError
            ? 'Cannot connect to backend server. Please ensure the Django API is running on port 8000.'
            : `Network error: ${errorMsg}`
        );
        (error as any).data = { detail: error.message };
        throw error;
      }

      // Check if MFA is required — return structured result (do not throw)
      if (responseData.mfa_required) {
        setState(prev => ({ ...prev, isLoading: false }));
        return {
          mfaRequired: true as const,
          refresh_token: responseData.refresh_token,
          session_id: responseData.session_id,
          mfa_method: responseData.mfa_method || 'totp',
          mfa_methods_available: Array.isArray(responseData.mfa_methods_available)
            ? responseData.mfa_methods_available
            : undefined,
        };
      }
      
      const { user, access_token, refresh_token, primary_role, profiling_required } = responseData;

      if (!access_token) {
        throw new Error('No access token received from login response');
      }

      // Store tokens immediately
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('auth_token', access_token); // backwards-compat
      if (refresh_token) {
        localStorage.setItem('refresh_token', refresh_token);
      }
      
      // Fetch full user profile with a short timeout so login UX stays responsive.
      let fullUser = user;
      try {
        const timedProfile = await Promise.race([
          djangoClient.auth.getCurrentUser(),
          new Promise<null>((resolve) => setTimeout(() => resolve(null), 1500)),
        ]);
        if (timedProfile && timedProfile.roles && timedProfile.roles.length > 0) {
          fullUser = timedProfile;
        }
      } catch {
        // Keep login responsive; fallback to user payload from login response.
      }

      try {
        await fetch('/api/auth/set-tokens', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            access_token,
            refresh_token: refresh_token ?? '',
            user: fullUser ?? user,
            primary_role:
              typeof primary_role === 'string' && primary_role.trim()
                ? primary_role
                : undefined,
          }),
        });
      } catch {
        // Non-fatal; login page recovery may still call set-tokens when redirect= is present
      }

      // Update state with authenticated user immediately
      setState({
        user: fullUser,
        isLoading: false,
        isAuthenticated: true,
      });

      return {
        user: fullUser,
        access_token: access_token,
        primary_role: primary_role as string | undefined,
        profiling_required: profiling_required as boolean | undefined,
      };
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      throw error;
    }
  }, []);

  /**
   * Complete MFA after login (when mfa_required was returned).
   * Call with refresh_token, code, and method from the MFA step.
   */
  const completeMFA = useCallback(async (params: {
    refresh_token: string;
    code: string;
    method: 'totp' | 'sms' | 'email' | 'backup_codes';
  }) => {
    try {
      const response: any = await apiGateway.post<any>('/auth/mfa/complete', params, { skipAuth: true });
      const { access_token, refresh_token: newRefreshToken, user: userData, primary_role } = response as any;
      // Set tokens in localStorage and in cookies (client-side) so middleware sees them on next request
      setAuthTokens(access_token, newRefreshToken ?? '');
      // Also set via API so och_roles and other cookies are set; middleware relies on access_token cookie
      try {
        await fetch('/api/auth/set-tokens', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            access_token,
            refresh_token: newRefreshToken,
            user: userData,
            primary_role:
              typeof primary_role === 'string' && primary_role.trim()
                ? primary_role
                : undefined,
          }),
        });
      } catch {
        // Non-fatal; tokens may still be in localStorage
      }
      let fullUser = userData;
      try {
        fullUser = await djangoClient.auth.getCurrentUser();
      } catch {
        fullUser = userData;
      }
      setState({ user: fullUser, isLoading: false, isAuthenticated: true });
      return {
        user: fullUser,
        access_token,
        primary_role: typeof primary_role === 'string' ? primary_role : undefined,
      };
    } catch (error: any) {
      throw error;
    }
  }, []);

  /**
   * Send MFA challenge (SMS or email code). Call when user's method is sms/email.
   */
  const sendMFAChallenge = useCallback(async (refresh_token: string, method?: 'email' | 'sms') => {
    try {
      const response = await apiGateway.post('/auth/mfa/send-challenge', { refresh_token, method }, { skipAuth: true });
      return response;
    } catch (error: any) {
      throw error;
    }
  }, []);

  /**
   * Logout user
   */
  const logout = useCallback(async () => {
    try {
      // Call Next.js API route (clears HttpOnly cookies)
      await fetch('/api/auth/logout', {
        method: 'POST',
      });
    } catch {
      // Continue with logout even if API call fails
    } finally {
      clearAuthTokens();
      if (typeof window !== 'undefined') window.sessionStorage.removeItem('mfa_compliant');
      setState({ user: null, isLoading: false, isAuthenticated: false });
      router.push('/login');
    }
  }, [router]);

  /**
   * Refresh access token
   */
  const refreshToken = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response: any = await apiGateway.post<any>(
        '/auth/token/refresh',
        { refresh_token: refreshToken },
        { skipAuth: true }
      );
      setAuthTokens(response.access_token, response.refresh_token);
      return response;
    } catch (error) {
      clearAuthTokens();
      setState({ user: null, isLoading: false, isAuthenticated: false });
      throw error;
    }
  }, []);

  // Load user on mount
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return {
    ...state,
    login,
    logout,
    refresh: refreshToken,
    reloadUser: loadUser,
    completeMFA,
    sendMFAChallenge,
  };
}

/**
 * AuthProvider wraps the app and ensures we fetch /auth/me only once,
 * sharing the result via React context.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const value = useProvideAuth();
  // Avoid JSX here so this file can remain .ts (not .tsx)
  return React.createElement(AuthContext.Provider, { value }, children);
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
