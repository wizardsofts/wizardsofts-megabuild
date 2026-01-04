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
    <header className="fixed top-0 left-0 right-0 z-50 w-full border-b border-gray-200 bg-white" style={{ height: '50px' }}>
      <div className="flex items-center justify-between px-5 h-full">
        {/* Left: Brand + Navigation */}
        <div className="flex items-center">
          <Link
            href="/"
            className="flex-shrink-0 mr-7"
            onClick={() => handleNavClick('Home', '/')}
            style={{
              fontWeight: 700,
              fontSize: '1.2rem',
              letterSpacing: '-0.5px',
              color: '#212529'
            }}
          >
            Guardian Investment BD
          </Link>

          {/* Navigation Links */}
          <nav className="flex items-center gap-5">
          <Link
            href="/dashboard"
            style={{ fontWeight: 500, color: '#212529', textDecoration: 'none' }}
            onClick={() => handleNavClick('Dashboard', '/dashboard')}
          >
            Dashboard
          </Link>

          {/* Markets Dropdown */}
          <div className="relative">
            <button
              onClick={() => setMarketsDropdownOpen(!marketsDropdownOpen)}
              style={{ fontWeight: 500, color: '#212529', textDecoration: 'none', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              className="flex items-center gap-1"
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

          <Link
            href="/screener"
            style={{ fontWeight: 500, color: '#212529', textDecoration: 'none' }}
            onClick={() => handleNavClick('Screener', '/screener')}
          >
            Screener
          </Link>

          <Link
            href="/chat"
            style={{ fontWeight: 500, color: '#212529', textDecoration: 'none' }}
            onClick={() => handleNavClick('Chat', '/chat')}
          >
            Chat
          </Link>

          <Link
            href="/portfolio"
            style={{ fontWeight: 500, color: '#212529', textDecoration: 'none' }}
            onClick={() => handleNavClick('Portfolio', '/portfolio')}
          >
            Portfolio
          </Link>

          <Link
            href="/news"
            style={{ fontWeight: 500, color: '#212529', textDecoration: 'none' }}
            onClick={() => handleNavClick('News', '/news')}
          >
            News
          </Link>

          {/* Learn Dropdown */}
          <div className="relative">
            <button
              onClick={() => setLearnDropdownOpen(!learnDropdownOpen)}
              style={{ fontWeight: 500, color: '#212529', textDecoration: 'none', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              className="flex items-center gap-1"
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
            style={{ fontWeight: 500, color: '#212529', textDecoration: 'none' }}
            onClick={() => handleNavClick('Community', '/community')}
          >
            Community
          </Link>
        </nav>
        </div>

        {/* Right Section: Search + Profile */}
        <div className="flex items-center gap-5">
          {/* Search Bar */}
          <form onSubmit={handleSearch}>
            <input
              type="text"
              value={tickerSearch}
              onChange={(e) => setTickerSearch(e.target.value)}
              placeholder="Search (e.g., BATBC)"
              style={{
                padding: '5px 10px',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                width: '300px',
                fontSize: '14px'
              }}
            />
          </form>

          {/* Profile */}
          <div style={{ fontSize: '0.9rem', color: '#212529' }}>
            Mashfiqur Rahman
          </div>
        </div>
      </div>
    </header>
  );
}
