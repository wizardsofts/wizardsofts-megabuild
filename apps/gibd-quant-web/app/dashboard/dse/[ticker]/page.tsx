'use client';

import { useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { Tabs, TabList, Tab, TabPanel } from '@wizwebui/core';
import ProfileContent from './profile/ProfileContent';
import HoldingContent from './holding/HoldingContent';
import NewsContent from './news/NewsContent';

/**
 * Ticker Details Page - Parent page for all ticker-specific tabs
 *
 * URL: /dashboard/dse/{ticker}
 * Example: /dashboard/dse/BATBC
 *
 * Features:
 * - Stock price header with company information
 * - Tab navigation (Company Profile, Guardian Analysis, Chart, Holdings, etc.)
 * - Each tab renders its own content component
 *
 * Component Library: wizwebui v0.2.0
 */

interface TickerPageProps {
  params: {
    ticker: string;
  };
}

export default function TickerPage({ params }: TickerPageProps) {
  const { ticker } = use(params);
  return <TickerPageClient ticker={ticker} />;
}

function TickerPageClient({ ticker }: { ticker: string }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);

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
      <Tabs variant="underline" value={activeTab} onChange={(key) => setActiveTab(key as string)} className="mt-3 md:mt-4">
        <div className="relative flex items-center gap-2">
          <TabList className="overflow-x-auto scrollbar-hide whitespace-nowrap flex-1">
            {/* Always visible tabs */}
            <Tab value="profile" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base">Company Profile</Tab>
            <Tab value="analysis" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base">Guardian Analysis</Tab>
            <Tab value="chart" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base">Chart</Tab>
            <Tab value="holdings" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base">Holdings</Tab>

            {/* Desktop: Show all tabs */}
            <Tab value="financials" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base hidden md:inline-flex">Financials</Tab>
            <Tab value="returns" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base hidden md:inline-flex">Trailing Returns</Tab>
            <Tab value="dividends" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base hidden md:inline-flex">Dividends</Tab>
            <Tab value="news" className="pb-2 md:pb-2.5 text-xs sm:text-sm md:text-base hidden md:inline-flex">News</Tab>
          </TabList>

          {/* Mobile: More dropdown for hidden tabs */}
          <div className="relative md:hidden flex-shrink-0">
            <button
              onClick={() => setMoreMenuOpen(!moreMenuOpen)}
              className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50 font-medium text-gray-900"
            >
              More ▾
            </button>
            {moreMenuOpen && (
              <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded shadow-lg py-1 min-w-[150px] z-10">
                <button
                  onClick={() => { setActiveTab('financials'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Financials
                </button>
                <button
                  onClick={() => { setActiveTab('returns'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Trailing Returns
                </button>
                <button
                  onClick={() => { setActiveTab('dividends'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  Dividends
                </button>
                <button
                  onClick={() => { setActiveTab('news'); setMoreMenuOpen(false); }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  News
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Tab Panels */}
        <TabPanel value="profile">
          <ProfileContent ticker={ticker} />
        </TabPanel>

        <TabPanel value="analysis">
          <div className="text-center py-10 text-gray-500">Guardian Analysis - Coming Soon</div>
        </TabPanel>

        <TabPanel value="chart">
          <div className="text-center py-10 text-gray-500">Chart - Coming Soon</div>
        </TabPanel>

        <TabPanel value="holdings">
          <HoldingContent ticker={ticker} />
        </TabPanel>

        <TabPanel value="financials">
          <div className="text-center py-10 text-gray-500">Financials - Coming Soon</div>
        </TabPanel>

        <TabPanel value="returns">
          <div className="text-center py-10 text-gray-500">Trailing Returns - Coming Soon</div>
        </TabPanel>

        <TabPanel value="dividends">
          <div className="text-center py-10 text-gray-500">Dividends - Coming Soon</div>
        </TabPanel>

        <TabPanel value="news">
          <NewsContent ticker={ticker} />
        </TabPanel>
      </Tabs>
    </div>
  );
}
