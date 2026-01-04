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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
      <div className="flex items-center justify-between px-3 md:px-5 h-full">
        {/* Mobile: Burger Menu */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 -ml-2"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Brand */}
        <Link
          href="/"
          className="flex-shrink-0 md:mr-5"
          onClick={() => handleNavClick('Home', '/')}
          style={{
            fontWeight: 700,
            fontSize: '1rem',
            letterSpacing: '-0.5px',
            color: '#212529'
          }}
        >
          <span className="hidden md:inline">Guardian Investment BD</span>
          <span className="md:hidden">GIBD</span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-3 lg:gap-5 text-sm md:text-base flex-1">
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
              <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[150px] z-10">
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
              <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[150px] z-10">
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

        {/* Right Section: Search + Profile */}
        <div className="flex items-center gap-2 md:gap-3 lg:gap-5 flex-shrink-0">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="hidden md:block">
            <input
              type="text"
              value={tickerSearch}
              onChange={(e) => setTickerSearch(e.target.value)}
              placeholder="Search (e.g., BATBC)"
              className="w-32 lg:w-48 xl:w-64"
              style={{
                padding: '5px 10px',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            />
          </form>

          {/* Profile */}
          <div style={{ fontSize: '0.9rem', color: '#212529' }} className="hidden sm:block">
            Mashfiqur Rahman
          </div>
          {/* Mobile Profile Icon */}
          <div className="sm:hidden w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center" style={{ fontSize: '0.75rem', fontWeight: 600, color: '#212529' }}>
            MR
          </div>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-white border-b border-gray-200 shadow-lg z-40">
          <nav className="flex flex-col py-2">
            <Link
              href="/dashboard"
              className="px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-100"
              onClick={() => { handleNavClick('Dashboard', '/dashboard'); setMobileMenuOpen(false); }}
            >
              Dashboard
            </Link>

            <div className="px-5 py-3 border-b border-gray-100">
              <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Markets</div>
              <Link
                href="/markets/dse"
                className="block py-2 text-sm text-gray-700 hover:text-blue-600"
                onClick={() => { handleNavClick('DSE', '/markets/dse'); setMobileMenuOpen(false); }}
              >
                DSE
              </Link>
              <Link
                href="/markets/cse"
                className="block py-2 text-sm text-gray-700 hover:text-blue-600"
                onClick={() => { handleNavClick('CSE', '/markets/cse'); setMobileMenuOpen(false); }}
              >
                CSE
              </Link>
            </div>

            <Link
              href="/screener"
              className="px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-100"
              onClick={() => { handleNavClick('Screener', '/screener'); setMobileMenuOpen(false); }}
            >
              Screener
            </Link>

            <Link
              href="/chat"
              className="px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-100"
              onClick={() => { handleNavClick('Chat', '/chat'); setMobileMenuOpen(false); }}
            >
              Chat
            </Link>

            <Link
              href="/portfolio"
              className="px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-100"
              onClick={() => { handleNavClick('Portfolio', '/portfolio'); setMobileMenuOpen(false); }}
            >
              Portfolio
            </Link>

            <Link
              href="/news"
              className="px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 border-b border-gray-100"
              onClick={() => { handleNavClick('News', '/news'); setMobileMenuOpen(false); }}
            >
              News
            </Link>

            <div className="px-5 py-3 border-b border-gray-100">
              <div className="text-xs font-semibold text-gray-500 uppercase mb-2">Learn</div>
              <Link
                href="/learn/guides"
                className="block py-2 text-sm text-gray-700 hover:text-blue-600"
                onClick={() => { handleNavClick('Guides', '/learn/guides'); setMobileMenuOpen(false); }}
              >
                Guides
              </Link>
              <Link
                href="/learn/tutorials"
                className="block py-2 text-sm text-gray-700 hover:text-blue-600"
                onClick={() => { handleNavClick('Tutorials', '/learn/tutorials'); setMobileMenuOpen(false); }}
              >
                Tutorials
              </Link>
            </div>

            <Link
              href="/community"
              className="px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50"
              onClick={() => { handleNavClick('Community', '/community'); setMobileMenuOpen(false); }}
            >
              Community
            </Link>

            {/* Mobile Search */}
            <div className="px-5 py-3 border-t border-gray-200">
              <form onSubmit={(e) => { handleSearch(e); setMobileMenuOpen(false); }}>
                <input
                  type="text"
                  value={tickerSearch}
                  onChange={(e) => setTickerSearch(e.target.value)}
                  placeholder="Search ticker (e.g., BATBC)"
                  className="w-full"
                  style={{
                    padding: '8px 12px',
                    border: '1px solid #ced4da',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </form>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
