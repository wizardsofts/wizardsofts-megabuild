'use client';

import { SessionProvider } from 'next-auth/react';
import { ReactNode } from 'react';

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication provider component.
 * Wraps the application with NextAuth.js session context.
 *
 * Usage in layout.tsx:
 *   <AuthProvider>{children}</AuthProvider>
 */
export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <SessionProvider refetchInterval={4 * 60} refetchOnWindowFocus={true}>
      {children}
    </SessionProvider>
  );
}
