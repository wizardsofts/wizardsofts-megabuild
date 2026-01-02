'use client';

import { useSession, signIn, signOut } from 'next-auth/react';
import { useCallback } from 'react';

/**
 * Custom hook for authentication operations.
 *
 * Provides:
 * - Current session state
 * - User information with tenant context
 * - Sign in/out functions
 * - Role-based authorization helpers
 */
export function useAuth() {
  const { data: session, status, update } = useSession();

  const isAuthenticated = status === 'authenticated';
  const isLoading = status === 'loading';

  const user = session?.user;
  const accessToken = session?.accessToken;
  const tenantId = user?.tenantId;
  const roles = user?.roles || [];

  /**
   * Check if user has a specific role
   */
  const hasRole = useCallback(
    (role: string) => {
      return roles.includes(role);
    },
    [roles]
  );

  /**
   * Check if user is a super admin
   */
  const isSuperAdmin = useCallback(() => {
    return hasRole('super-admin');
  }, [hasRole]);

  /**
   * Check if user is a tenant admin
   */
  const isTenantAdmin = useCallback(() => {
    return hasRole('tenant-admin');
  }, [hasRole]);

  /**
   * Sign in with Keycloak
   */
  const login = useCallback(async (callbackUrl?: string) => {
    await signIn('keycloak', {
      callbackUrl: callbackUrl || '/',
    });
  }, []);

  /**
   * Sign out and end Keycloak session
   */
  const logout = useCallback(async (callbackUrl?: string) => {
    await signOut({
      callbackUrl: callbackUrl || '/',
    });
  }, []);

  /**
   * Get authorization header for API calls
   */
  const getAuthHeader = useCallback(() => {
    if (!accessToken) {
      return {};
    }
    return {
      Authorization: `Bearer ${accessToken}`,
    };
  }, [accessToken]);

  return {
    // Session state
    session,
    status,
    isAuthenticated,
    isLoading,

    // User info
    user,
    accessToken,
    tenantId,
    roles,

    // Role checks
    hasRole,
    isSuperAdmin,
    isTenantAdmin,

    // Auth actions
    login,
    logout,
    refreshSession: update,

    // API helpers
    getAuthHeader,
  };
}

/**
 * Hook for protected content
 * Returns null while loading, redirects if not authenticated
 */
export function useRequireAuth(redirectUrl = '/auth/signin') {
  const { isAuthenticated, isLoading, login } = useAuth();

  if (isLoading) {
    return { isLoading: true, isAuthorized: false };
  }

  if (!isAuthenticated) {
    login(typeof window !== 'undefined' ? window.location.href : undefined);
    return { isLoading: false, isAuthorized: false };
  }

  return { isLoading: false, isAuthorized: true };
}

/**
 * Hook for role-protected content
 */
export function useRequireRole(requiredRole: string, redirectUrl = '/') {
  const { isAuthenticated, isLoading, hasRole, login } = useAuth();

  if (isLoading) {
    return { isLoading: true, isAuthorized: false };
  }

  if (!isAuthenticated) {
    login(typeof window !== 'undefined' ? window.location.href : undefined);
    return { isLoading: false, isAuthorized: false };
  }

  if (!hasRole(requiredRole)) {
    return { isLoading: false, isAuthorized: false };
  }

  return { isLoading: false, isAuthorized: true };
}
