'use client';

// TODO: Fix React type mismatch with NextAuth SessionProvider
// import { SessionProvider } from 'next-auth/react';
import { ReactNode } from 'react';

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Authentication provider component.
 * Wraps the application with NextAuth.js session context.
 *
 * TODO: Fix React JSX type compatibility issue with SessionProvider
 *
 * Usage in layout.tsx:
 *   <AuthProvider>{children}</AuthProvider>
 */
export function AuthProvider({ children }: AuthProviderProps) {
  // TODO: Wrap with SessionProvider once React type compatibility is fixed
  return children;
  // return (
  //   <SessionProvider refetchInterval={4 * 60} refetchOnWindowFocus={true}>
  //     {children}
  //   </SessionProvider>
  // );
}
