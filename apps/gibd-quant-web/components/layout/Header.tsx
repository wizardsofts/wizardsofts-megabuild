'use client';

import { useState, FormEvent } from 'react';
import Link from "next/link";
import { useRouter } from 'next/navigation';
import { trackEvent } from '@/lib/analytics';

/**
 * Header Component - Minimal fixed navigation bar
 *
 * Features:
 * - Fixed at top with backdrop blur
 * - One-line minimal design
 * - Click tracking for all navigation links
 */

export function Header() {
  const router = useRouter();
  const [tickerSearch, setTickerSearch] = useState('');

  const handleSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (tickerSearch.trim()) {
      const ticker = tickerSearch.toUpperCase().trim();
      trackEvent('search', 'ticker_search', ticker);
      router.push(`/company/${ticker}`);
      setTickerSearch('');
    }
  };

  const handleNavClick = (label: string, href: string) => {
    trackEvent('navigation', 'header_nav_click', label);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full border-b border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="container mx-auto flex h-12 items-center justify-between px-4">
        {/* Logo / Brand */}
        <Link
          href="/"
          className="flex items-center gap-2 flex-shrink-0"
          onClick={() => handleNavClick('Home', '/')}
        >
          <span className="text-base font-bold text-gray-900">Guardian Investment BD</span>
          <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-600">DSE</span>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-4 md:gap-6">
          <Link
            href="/signals"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Signals', '/signals')}
          >
            Signals
          </Link>
          <Link
            href="/charts"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Charts', '/charts')}
          >
            Charts
          </Link>
          <Link
            href="/chat"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('AI Chat', '/chat')}
          >
            Chat
          </Link>
          <Link
            href="/multi-criteria"
            className="hidden md:inline text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Multi-Criteria', '/multi-criteria')}
          >
            Multi-Criteria
          </Link>
        </nav>

        {/* Ticker Search - Compact */}
        <form
          onSubmit={handleSearch}
          className="hidden lg:flex items-center flex-shrink-0"
        >
          <input
            type="text"
            value={tickerSearch}
            onChange={(e) => setTickerSearch(e.target.value)}
            placeholder="Ticker..."
            className="w-24 px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </form>
      </div>
    </header>
  );
}
