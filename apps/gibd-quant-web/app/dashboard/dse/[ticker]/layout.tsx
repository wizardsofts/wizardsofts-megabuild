'use client';

import { useState, useEffect, useRef } from 'react';
import { usePathname, useParams } from 'next/navigation';
// TODO: Replace with @wizwebui/core Tabs, TabList, Tab once library is fixed (missing exports in dist)
import ProfileContent from './profile/ProfileContent';
import CompanyChart from '@/components/company/CompanyChart';

/**
 * Ticker Layout - All-in-one client-side tab navigation
 *
 * Manages:
 * - Active tab state (persists across switches)
 * - Chart indicator state (preserved when switching tabs)
 * - URL updates for bookmarkability
 * - No full page reloads on tab switches
 *
 * Component Library: wizwebui v0.2.0
 */

interface IndicatorConfig {
  id: string;
  type: 'SMA' | 'EMA' | 'BB' | 'RSI' | 'MACD';
  params: Record<string, number>;
  color: string;
}

interface TickerLayoutProps {
  children: React.ReactNode;
}

export default function TickerLayout({ children }: TickerLayoutProps) {
  const pathname = usePathname();
  const params = useParams();
  const ticker = params.ticker as string;

  // Extract tab from URL pathname
  // Pathname format: /dashboard/dse/BATBC or /dashboard/dse/BATBC/chart
  const getTabFromPathname = () => {
    const parts = pathname.split('/');
    const tickerIndex = parts.findIndex((p) => p === 'dse') + 1;
    return parts[tickerIndex + 1] || 'profile';
  };

  const [activeTab, setActiveTab] = useState(getTabFromPathname());
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [indicators, setIndicators] = useState<IndicatorConfig[]>([]);
  const moreMenuRef = useRef<HTMLDivElement>(null);

  // Sync activeTab when pathname changes (e.g., back/forward navigation)
  useEffect(() => {
    setActiveTab(getTabFromPathname());
  }, [pathname]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (moreMenuRef.current && !moreMenuRef.current.contains(event.target as Node)) {
        setMoreMenuOpen(false);
      }
    };

    if (moreMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [moreMenuOpen]);

  // Client-side tab switching (no page reloads)
  const handleTabChange = (key: string | number) => {
    const tabKey = key as string;
    setActiveTab(tabKey);
    // Update URL for bookmarkability using browser history (client-side)
    const url = tabKey === 'profile' 
      ? `/dashboard/dse/${ticker}` 
      : `/dashboard/dse/${ticker}/${tabKey}`;
    window.history.pushState({ tab: tabKey }, '', url);
  };

  return (
    <div className="px-3 sm:px-4 md:px-5 mt-3 md:mt-5">
      {/* Stock Header */}
      <div className="flex flex-col md:grid md:grid-cols-[auto_1fr_auto] items-start md:items-center gap-3 md:gap-5 pb-3 md:pb-4 border-b border-gray-200 mb-4 md:mb-5">
        <div className="w-full md:w-auto">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-normal text-gray-900 tracking-tight">
            British American Tobacco Bangladesh
          </h1>
          <div className="text-xs sm:text-sm text-gray-600 mt-0.5">
            Trading Code: <strong>{ticker}</strong> | Scrip: 14259 | Sector: <strong>Food & Allied</strong>
          </div>
        </div>

        <div className="hidden md:block"></div>

        <div className="w-full md:w-auto flex justify-between md:justify-end items-center md:flex-col md:items-end gap-2 md:gap-0">
          <div>
            <div className="text-2xl sm:text-3xl md:text-4xl font-light text-gray-900">
              248.60 <span className="text-sm sm:text-base md:text-lg text-green-600 font-semibold ml-2.5">BDT</span>
            </div>
          </div>
          <div className="text-sm sm:text-base text-green-600 font-semibold">Closed</div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="mt-3 md:mt-4">
        <div className="relative flex items-center gap-2">
          <div className="overflow-x-auto scrollbar-hide whitespace-nowrap flex-1 flex gap-0">
            {/* Always visible tabs */}
            <button
              onClick={() => handleTabChange('profile')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors ${
                activeTab === 'profile'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Company Profile
            </button>
            <button
              onClick={() => handleTabChange('analysis')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors ${
                activeTab === 'analysis'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Guardian Analysis
            </button>
            <button
              onClick={() => handleTabChange('chart')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors ${
                activeTab === 'chart'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Chart
            </button>
            <button
              onClick={() => handleTabChange('holding')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors ${
                activeTab === 'holding'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Holdings
            </button>

            {/* Desktop: Show all tabs */}
            <button
              onClick={() => handleTabChange('financials')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors hidden md:inline-flex ${
                activeTab === 'financials'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Financials
            </button>
            <button
              onClick={() => handleTabChange('returns')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors hidden md:inline-flex ${
                activeTab === 'returns'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Trailing Returns
            </button>
            <button
              onClick={() => handleTabChange('dividends')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors hidden md:inline-flex ${
                activeTab === 'dividends'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Dividends
            </button>
            <button
              onClick={() => handleTabChange('news')}
              className={`pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base px-3 border-b-2 transition-colors hidden md:inline-flex ${
                activeTab === 'news'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              News
            </button>
          </div>

          {/* Mobile: More dropdown for hidden tabs */}
          <div ref={moreMenuRef} className="relative md:hidden flex-shrink-0">
            <button
              onClick={() => setMoreMenuOpen(!moreMenuOpen)}
              className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 font-medium text-gray-900"
            >
              More ▾
            </button>
            {moreMenuOpen && (
              <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[150px] z-10">
                <button
                  onClick={() => { handleTabChange('financials'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Financials
                </button>
                <button
                  onClick={() => { handleTabChange('returns'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Trailing Returns
                </button>
                <button
                  onClick={() => { handleTabChange('dividends'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Dividends
                </button>
                <button
                  onClick={() => { handleTabChange('news'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  News
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tab Content - Rendered client-side based on activeTab state */}
      <div className="mt-4">
        {activeTab === 'profile' && <ProfileContent ticker={ticker} />}
        {activeTab === 'analysis' && (
          <div className="text-center py-10 text-gray-500">Guardian Analysis - Coming Soon</div>
        )}
        {activeTab === 'chart' && (
          <CompanyChart 
            ticker={ticker} 
            indicators={indicators}
            onIndicatorsChange={setIndicators}
          />
        )}
        {activeTab === 'holding' && (
          <div className="text-center py-10 text-gray-500">Holdings - Coming Soon</div>
        )}
        {activeTab === 'financials' && (
          <div className="text-center py-10 text-gray-500">Financials - Coming Soon</div>
        )}
        {activeTab === 'returns' && (
          <div className="text-center py-10 text-gray-500">Trailing Returns - Coming Soon</div>
        )}
        {activeTab === 'dividends' && (
          <div className="text-center py-10 text-gray-500">Dividends - Coming Soon</div>
        )}
        {activeTab === 'news' && (
          <div className="text-center py-10 text-gray-500">News - Coming Soon</div>
        )}
      </div>
    </div>
  );
}
