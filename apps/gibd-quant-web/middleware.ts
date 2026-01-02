import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware to show Coming Soon page when accessed via domain name
 *
 * When the app is accessed via guardianinvestmentbd.com, it shows a Coming Soon page.
 * When accessed via local IP or localhost, it shows the full application.
 */
export function middleware(request: NextRequest) {
  const host = request.headers.get('host') || '';

  // Production domains that should show Coming Soon
  const comingSoonDomains = [
    'guardianinvestmentbd.com',
    'www.guardianinvestmentbd.com',
  ];

  // Check if accessing via a production domain
  const isProductionDomain = comingSoonDomains.some(domain =>
    host.includes(domain)
  );

  // If accessing via production domain, redirect to coming-soon page
  if (isProductionDomain) {
    const url = request.nextUrl;

    // Don't redirect if already on coming-soon page (avoid infinite loop)
    if (url.pathname === '/coming-soon') {
      return NextResponse.next();
    }

    // Allow static assets and API routes
    if (
      url.pathname.startsWith('/_next') ||
      url.pathname.startsWith('/api') ||
      url.pathname.includes('.')
    ) {
      return NextResponse.next();
    }

    // Redirect all other routes to coming-soon
    return NextResponse.rewrite(new URL('/coming-soon', request.url));
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
