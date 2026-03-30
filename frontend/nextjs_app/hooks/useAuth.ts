/**
 * Authentication hook
 * Manages login, logout, token refresh, and user session
 */

'use client';

import React, { useState, useEffect, useCallback, useContext } from 'react';
import { useRouter } from 'next/navigation';
import { djangoClient } from '../services/djangoClient';
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
      // Don't log connection errors (backend not running) as errors - this is expected
      const isConnectionError = 
        error?.status === 0 ||
        error?.message?.includes('Cannot connect') ||
        error?.message?.includes('Network Error') ||
        error?.message?.includes('fetch failed') ||
        error?.message?.includes('ECONNREFUSED');
      
      // Token invalid or expired - only clear if it's an auth error
      if (error?.status === 401 || error?.response?.status === 401) {
        clearAuthTokens();
        setState({ user: null, isLoading: false, isAuthenticated: false });
      } else {
        // For other errors (including connection errors), keep the token but mark as not authenticated
        setState({ user: null, isLoading: false, isAuthenticated: false });
      }
    }
  }, []);

  /**
   * Login user
   */
  const login = useCallback(async (credentials: LoginRequest) => {
    try {
      // Call Next.js API route (sets HttpOnly cookies)
      let response: Response;
      try {
        response = await fetch('/api/auth/login', {
        method: 'POST',
        credentials: 'include',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      } catch (fetchError: any) {
        // Catch network/connection errors
        const errorMsg = fetchError.message || 'Unknown error';
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

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = errorData.detail || errorData.error || 'Login failed';
        const error = new Error(message);
        (error as any).data = errorData;
        (error as any).status = response.status;
        (error as any).code = errorData.code; // e.g. 'BAD_GATEWAY' for backend 5xx
        throw error;
      }

      const responseData = await response.json();

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
      
      const { user, access_token, refresh_token } = responseData;

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
      
      // Update state with authenticated user immediately
      setState({
        user: fullUser,
        isLoading: false,
        isAuthenticated: true,
      });

      return { user: fullUser, access_token: access_token };
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
    const { access_token, refresh_token: newRefreshToken, user: userData } = await djangoClient.auth.completeMFA(params);
    // Set tokens in localStorage and in cookies (client-side) so middleware sees them on next request
    setAuthTokens(access_token, newRefreshToken ?? '');
    // Also set via API so och_roles and other cookies are set; middleware relies on access_token cookie
    try {
      await fetch('/api/auth/set-tokens', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_token, refresh_token: newRefreshToken, user: userData }),
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
    return { user: fullUser, access_token };
  }, []);

  /**
   * Send MFA challenge (SMS or email code). Call when user's method is sms/email.
   */
  const sendMFAChallenge = useCallback(async (refresh_token: string, method?: 'email' | 'sms') => {
    return djangoClient.auth.sendMFAChallenge(refresh_token, method);
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
  const refresh = useCallback(async () => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await djangoClient.auth.refreshToken({ refresh_token: refreshToken });
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
    refresh,
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
