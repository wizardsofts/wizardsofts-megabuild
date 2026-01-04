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
 * - Dropdown menus for Markets and Learn
 * - Profile dropdown on the right
 */

export function Header() {
  const router = useRouter();
  const [tickerSearch, setTickerSearch] = useState('');
  const [marketsDropdownOpen, setMarketsDropdownOpen] = useState(false);
  const [learnDropdownOpen, setLearnDropdownOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

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
      <div className="container mx-auto flex h-12 items-center justify-between px-4 gap-6">
        {/* Logo / Brand */}
        <Link
          href="/"
          className="flex items-center gap-2 flex-shrink-0"
          onClick={() => handleNavClick('Home', '/')}
        >
          <span className="text-base font-bold text-gray-900">Guardian Investment BD</span>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-4 md:gap-6">
          <Link
            href="/dashboard"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Dashboard', '/dashboard')}
          >
            Dashboard
          </Link>

          {/* Markets Dropdown */}
          <div className="relative">
            <button
              onClick={() => setMarketsDropdownOpen(!marketsDropdownOpen)}
              className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1"
            >
              Markets
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {marketsDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[150px]">
                <Link
                  href="/markets/dse"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => { handleNavClick('DSE', '/markets/dse'); setMarketsDropdownOpen(false); }}
                >
                  DSE
                </Link>
                <Link
                  href="/markets/cse"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => { handleNavClick('CSE', '/markets/cse'); setMarketsDropdownOpen(false); }}
                >
                  CSE
                </Link>
              </div>
            )}
          </div>

          {/* Screener Dropdown */}
          <div className="relative">
            <button
              className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1"
            >
              Screener
            </button>
          </div>

          <Link
            href="/chat"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Chat', '/chat')}
          >
            Chat
          </Link>

          <Link
            href="/portfolio"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Portfolio', '/portfolio')}
          >
            Portfolio
          </Link>

          <Link
            href="/news"
            className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('News', '/news')}
          >
            News
          </Link>

          {/* Learn Dropdown */}
          <div className="relative hidden md:block">
            <button
              onClick={() => setLearnDropdownOpen(!learnDropdownOpen)}
              className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1"
            >
              Learn
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {learnDropdownOpen && (
              <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[150px]">
                <Link
                  href="/learn/guides"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => { handleNavClick('Guides', '/learn/guides'); setLearnDropdownOpen(false); }}
                >
                  Guides
                </Link>
                <Link
                  href="/learn/tutorials"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => { handleNavClick('Tutorials', '/learn/tutorials'); setLearnDropdownOpen(false); }}
                >
                  Tutorials
                </Link>
              </div>
            )}
          </div>

          <Link
            href="/community"
            className="hidden md:inline text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            onClick={() => handleNavClick('Community', '/community')}
          >
            Community
          </Link>
        </nav>

        {/* Right Section: Profile Dropdown */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {/* Profile Dropdown */}
          <div className="relative">
            <button
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="text-xs md:text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1"
            >
              Mashfiqur Rahman
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {profileDropdownOpen && (
              <div className="absolute top-full right-0 mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[180px]">
                <Link
                  href="/profile"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => { handleNavClick('My Profile', '/profile'); setProfileDropdownOpen(false); }}
                >
                  My Profile
                </Link>
                <Link
                  href="/settings"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  onClick={() => { handleNavClick('Settings', '/settings'); setProfileDropdownOpen(false); }}
                >
                  Settings
                </Link>
                <div className="border-t border-gray-200 my-1"></div>
                <Link
                  href="/logout"
                  className="block px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                  onClick={() => { handleNavClick('Logout', '/logout'); setProfileDropdownOpen(false); }}
                >
                  Logout
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
