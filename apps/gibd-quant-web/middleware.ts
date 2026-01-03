import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getToken } from 'next-auth/jwt';

/**
 * Middleware to enforce authentication on protected routes
 *
 * - Public routes: /, /coming-soon, /api/auth
 * - Protected routes: All other routes require authentication
 * - For production domains (guardianinvestmentbd.com), unauthenticated users
 *   see the coming-soon page with login prompt
 */

const PUBLIC_ROUTES = ['/', '/coming-soon'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const host = request.headers.get('host') || '';

  // Allow static assets and auth routes (always public)
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api/auth') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Public routes are always accessible
  if (PUBLIC_ROUTES.some(route => pathname === route)) {
    return NextResponse.next();
  }

  // Check if production domain
  const isProductionDomain = host.includes('guardianinvestmentbd.com');

  if (isProductionDomain) {
    // Check if user is authenticated
    const token = await getToken({
      req: request,
      secret: process.env.NEXTAUTH_SECRET,
    });

    // If authenticated, allow access to protected routes
    if (token) {
      return NextResponse.next();
    }

    // Redirect unauthenticated users to coming-soon
    if (pathname !== '/coming-soon') {
      return NextResponse.rewrite(new URL('/coming-soon', request.url));
    }
  }

  // For local development / IP access, allow normal access
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
