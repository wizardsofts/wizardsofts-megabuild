import NextAuth from 'next-auth';
import { authOptions } from '@/lib/auth';

/**
 * NextAuth.js API route handler
 *
 * Handles:
 * - /api/auth/signin - Initiates Keycloak login
 * - /api/auth/signout - Ends session
 * - /api/auth/callback/keycloak - OAuth callback
 * - /api/auth/session - Get current session
 */
const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
