'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { hasRouteAccess } from '@/utils/rbac'
import { getRedirectRoute } from '@/utils/redirect'
import { getUserRoles } from '@/utils/rbac'

interface RouteGuardProps {
  children: React.ReactNode
  requiredRoles?: string[]
}

export function RouteGuard({ children, requiredRoles: _requiredRoles }: RouteGuardProps) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const router = useRouter()
  const [isHydrated, setIsHydrated] = useState(false)

  // Prevent hydration mismatch by ensuring consistent server/client rendering
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  const getLoginRouteForPath = (path: string) => {
    if (path.startsWith('/dashboard/director')) return '/login/director'
    if (path.startsWith('/dashboard/admin')) return '/login/admin'
    if (path.startsWith('/dashboard/mentor')) return '/login/mentor'
    if (path.startsWith('/dashboard/sponsor')) return '/login/sponsor'
    if (path.startsWith('/dashboard/analyst') || path.startsWith('/dashboard/analytics')) return '/login/analyst'
    if (path.startsWith('/dashboard/employer') || path.startsWith('/dashboard/marketplace')) return '/login/employer'
    if (path.startsWith('/dashboard/finance') || path.startsWith('/finance/')) return '/login/finance'
    return '/login'
  }

  useEffect(() => {
    // Wait for auth state to be determined
    if (isLoading) return

    const currentPath = typeof window !== 'undefined' ? window.location.pathname : ''

    // For student dashboard routes, be much more lenient
    const isStudentRoute = currentPath.startsWith('/dashboard/student')

    if (isStudentRoute) {
      // For student routes, if there's any token at all, allow access
      // The middleware will handle proper RBAC server-side
      const hasToken = typeof window !== 'undefined' && (
        localStorage.getItem('access_token') ||
        document.cookie.includes('access_token=')
      )

      if (hasToken) {
        return // Allow access, middleware already validated token
      } else {
        const loginRoute = getLoginRouteForPath(currentPath)
        const redirectUrl = `${loginRoute}?redirect=${encodeURIComponent(currentPath)}`
        router.push(redirectUrl)
        return
      }
    }

    // For non-student routes, use normal logic
    if (!isAuthenticated || !user) {
      const hasToken = typeof window !== 'undefined' && (
        localStorage.getItem('access_token') ||
        document.cookie.includes('access_token=')
      )

      if (!hasToken) {
        const loginRoute = getLoginRouteForPath(currentPath)
        if (typeof window !== 'undefined') {
          const redirectUrl = `${loginRoute}?redirect=${encodeURIComponent(currentPath)}`
          router.push(redirectUrl)
        }
        return
      }
      // Token exists but user not loaded - wait briefly
      return
    }

    // If requiredRoles is provided, enforce it (in addition to route permissions)
    if (_requiredRoles && _requiredRoles.length > 0) {
      const roles = getUserRoles(user)
      const isMentor = roles.includes('mentor')
      const ok = _requiredRoles.some(r => roles.includes(r as any))
      if (!ok) {
        // CRITICAL: For mentors, NEVER redirect to student - always go to mentor dashboard
        if (isMentor) {
          router.push('/dashboard/mentor')
        } else {
          router.push(getRedirectRoute(user))
        }
        return
      }
    }

    // CRITICAL: Check for mentor role BEFORE hasRouteAccess check
    // This prevents mentors from being redirected to student dashboard
    const userRoles = getUserRoles(user)
    const isMentor = userRoles.includes('mentor')
    const isMentorRoute = currentPath.startsWith('/dashboard/mentor')
    
    if (isMentor && isMentorRoute) {
      // Mentor accessing mentor route - always allow
    } else if (!hasRouteAccess(user, currentPath)) {
      if (isMentor) {
        router.push('/dashboard/mentor')
        return
      }
      
      const redirectRoute = getRedirectRoute(user)
      router.push(redirectRoute)
      return
    }
  }, [user, isLoading, isAuthenticated, router])

  // Prevent hydration mismatch - always show loading on server and until hydrated
  if (!isHydrated || isLoading) {
    return (
      <div className="min-h-screen bg-och-midnight flex items-center justify-center">
        <div className="text-och-steel animate-pulse">Loading OCH Dashboard...</div>
      </div>
    )
  }

  // If not authenticated but token exists, show loading (auth state might be updating)
  if (!isAuthenticated || !user) {
    const hasToken = typeof window !== 'undefined' && (
      localStorage.getItem('access_token') ||
      document.cookie.includes('access_token=')
    )

    if (hasToken) {
      // Token exists but user not loaded - show loading
      return (
        <div className="min-h-screen bg-och-midnight flex items-center justify-center">
          <div className="text-och-steel animate-pulse">Authenticating...</div>
        </div>
      )
    }

    return null
  }

  const currentPath = typeof window !== 'undefined' ? window.location.pathname : ''

  // CRITICAL: Check for mentor role BEFORE hasRouteAccess check
  // This prevents mentors from being denied access to mentor routes
  const userRoles = getUserRoles(user)
  const isMentor = userRoles.includes('mentor')
  const isMentorRoute = currentPath.startsWith('/dashboard/mentor')
  
  if (isMentor && isMentorRoute) {
    return <>{children}</>
  }

  if (_requiredRoles && _requiredRoles.length > 0) {
    const roles = getUserRoles(user)
    const ok = _requiredRoles.some(r => roles.includes(r as any))
    if (!ok) return null
  }

  if (!hasRouteAccess(user, currentPath)) {
    return null
  }

  return <>{children}</>
}

