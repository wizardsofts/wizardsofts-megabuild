'use client';

import { useState, use } from 'react';
import {
  Card, CardHeader, CardBody,
  Table, Badge, Tabs, TabList, Tab, TabPanel,
  Sparkline
} from '@wizwebui/core';

/**
 * Holdings Page - Stock shareholding information
 *
 * URL: /dashboard/dse/{ticker}/holding
 * Example: /dashboard/dse/BATBC/holding
 *
 * Features:
 * - Stock price header with company information
 * - Tab navigation (Summary, Profile, Financials, Holdings, etc.)
 * - 3-column dashboard layout
 * - Holdings summary with pie chart
 * - Detailed shareholding composition table
 * - Market statistics
 *
 * Component Library: wizwebui v0.2.0
 */

interface HoldingsPageProps {
  params: {
    ticker: string;
  };
}

// Sample data - In production, fetch from API
const basicInfo = [
  { label: 'Total Securities', value: '540 Mn' },
  { label: 'Market Cap', value: '134.4 Bn' },
  { label: 'Share Audit', value: 'OK', status: 'success' },
];

const shareholdingData = [
  {
    category: 'Sponsor / Director',
    chip: 'Locked',
    holders: 5,
    percentage: '72.91%',
    shares: '393,714,000',
    trend: [50, 50, 50, 50], // neutral trend
  },
  {
    category: 'Institutions',
    chip: 'Smart Money',
    holders: 124,
    percentage: '12.03%',
    shares: '64,962,000',
    trend: [40, 45, 50, 60], // upward trend
  },
  {
    category: 'Foreign Investors',
    chip: null,
    holders: 12,
    percentage: '6.84%',
    shares: '36,936,000',
    trend: [60, 55, 50, 45], // downward trend
  },
  {
    category: 'Public / Retail',
    chip: null,
    holders: '--',
    percentage: '7.58%',
    shares: '40,932,000',
    trend: [30, 40, 45, 50], // upward trend
  },
];

const marketStats = [
  { label: 'Last Trade', value: '248.60' },
  { label: 'Change', value: '0.00%', color: 'text-gray-600' },
  { label: 'Volume', value: '5,320' },
];

// Trend Bar Component (custom, not in wizwebui)
function TrendBar({ data = [50, 60, 55, 70] }: { data?: number[] }) {
  const getTrendClass = () => {
    const last = data[data.length - 1];
    const first = data[0];
    if (last > first + 5) return 'bg-green-500';
    if (last < first - 5) return 'bg-red-500';
    return 'bg-gray-400';
  };

  return (
    <div className="flex gap-0.5 items-end h-4 w-12">
      {data.map((height, i) => (
        <div
          key={i}
          className={`w-1/4 rounded-sm ${i === data.length - 1 ? getTrendClass() : 'bg-gray-300'}`}
          style={{ height: `${height}%` }}
        />
      ))}
    </div>
  );
}

export default function HoldingsPage({ params }: HoldingsPageProps) {
  const { ticker } = use(params);
  return <HoldingsPageClient ticker={ticker} />;
}

function HoldingsPageClient({ ticker }: { ticker: string }) {
  const [activeTab, setActiveTab] = useState('profile');
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);

  return (
    <div className="px-3 sm:px-4 md:px-5 mt-3 md:mt-5">
      {/* Stock Header - Dense like mockup */}
      <div className="flex flex-col md:grid md:grid-cols-[auto_1fr_auto] items-start md:items-center gap-3 md:gap-5 pb-3 md:pb-4 border-b border-gray-200 mb-4 md:mb-5">
        <div className="w-full md:w-auto">
          <h1 className="text-xl sm:text-2xl md:text-3xl" style={{ margin: 0, fontSize: 'clamp(1.25rem, 4vw, 1.8rem)', letterSpacing: '-0.5px', fontWeight: 400, color: '#212529' }}>
            British American Tobacco Bangladesh
          </h1>
          <div className="text-xs sm:text-sm" style={{ color: '#6c757d', fontSize: 'clamp(0.75rem, 2vw, 0.9rem)', marginTop: '2px' }}>
            Trading Code: <strong>{ticker}</strong> | Scrip: 14259 | Sector: <strong>Food & Allied</strong>
          </div>
        </div>

        <div className="hidden md:block">
          {/* Chart removed - not in mockup */}
        </div>

        <div className="w-full md:w-auto flex justify-between md:justify-end items-center md:flex-col md:items-end gap-2 md:gap-0">
          <div>
            <div className="text-2xl sm:text-3xl md:text-4xl" style={{ fontSize: 'clamp(1.5rem, 5vw, 2rem)', fontWeight: 300, color: '#212529' }}>
              248.60 <span className="text-sm sm:text-base md:text-lg" style={{ fontSize: 'clamp(0.875rem, 2vw, 1rem)', color: '#28a745', fontWeight: 600, marginLeft: '10px' }}>BDT</span>
            </div>
          </div>
          <div className="text-sm sm:text-base" style={{ fontSize: 'clamp(0.875rem, 2vw, 1rem)', color: '#28a745', fontWeight: 600, marginTop: '0' }}>Closed</div>
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
              className="px-2 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
              style={{ fontWeight: 500, color: '#212529' }}
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

        {/* Holdings Tab Panel */}
        <TabPanel value="holdings">
          {/* Dashboard Grid - Mobile: Stack, Desktop: 3-column */}
          <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_300px] gap-4 md:gap-6 mt-4 md:mt-6">
            {/* Left Column: Holdings Summary */}
            <div>
              <Card variant="panel">
                <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
                  Holdings Summary
                </CardHeader>
                <CardBody className="p-4">
                  {/* Pie Chart - CSS Conic Gradient (keep from mockup) */}
                  <div className="flex justify-center mb-5">
                    <div
                      className="w-36 h-36 rounded-full relative"
                      style={{
                        background: `conic-gradient(
                          #343a40 0% 72.91%,
                          #0056b3 72.91% 84.94%,
                          #28a745 84.94% 91.78%,
                          #e0e0e0 91.78% 100%
                        )`
                      }}
                    >
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-20 h-20 bg-white rounded-full flex flex-col items-center justify-center">
                        <div className="text-xs text-gray-600">Total</div>
                        <div className="text-sm font-bold">100%</div>
                      </div>
                    </div>
                  </div>

                  {/* Legend */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 bg-gray-800 rounded-sm" />
                        <span className="text-sm text-gray-600">Sponsor</span>
                      </div>
                      <span className="text-sm font-semibold">72.9%</span>
                    </div>
                    <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 bg-blue-600 rounded-sm" />
                        <span className="text-sm text-gray-600">Institute</span>
                      </div>
                      <span className="text-sm font-semibold">12.0%</span>
                    </div>
                    <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 bg-green-600 rounded-sm" />
                        <span className="text-sm text-gray-600">Foreign</span>
                      </div>
                      <span className="text-sm font-semibold">6.8%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 bg-gray-300 rounded-sm" />
                        <span className="text-sm text-gray-600">Public</span>
                      </div>
                      <span className="text-sm font-semibold">7.6%</span>
                    </div>
                  </div>
                </CardBody>
              </Card>

              <Card variant="panel" className="mt-4 md:mt-5">
                <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
                  Basic Info
                </CardHeader>
                <CardBody className="p-4">
                  <Table
                    dataSource={basicInfo.map((item, idx) => ({ id: idx, ...item }))}
                    density="compact"
                    borderStyle="minimal"
                    columns={[
                      {
                        key: 'label',
                        title: 'Metric',
                        render: (value, record) => <span className="text-gray-600 text-sm">{record.label}</span>
                      },
                      {
                        key: 'value',
                        title: 'Value',
                        render: (value, record) => (
                          <span className={`text-sm ${record.status === 'success' ? 'text-green-600 font-semibold' : ''}`}>
                            {record.value}
                          </span>
                        )
                      },
                    ]}
                  />
                </CardBody>
              </Card>
            </div>

            {/* Middle Column: Detailed Shareholding */}
            <div>
              <Card variant="panel">
                <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
                    <span>Detailed Shareholding Composition</span>
                    <span className="text-xs font-normal normal-case text-gray-500">As of Sep 30, 2024</span>
                  </div>
                </CardHeader>
                <CardBody className="p-4">
                  <div className="overflow-x-auto -mx-4 md:mx-0">
                    <Table
                      dataSource={shareholdingData.map((item, idx) => ({ id: idx, ...item }))}
                      rowKey={(record) => record.category}
                      density="compact"
                      borderStyle="minimal"
                    columns={[
                      {
                        key: 'category',
                        title: 'Category',
                        render: (value, record) => (
                          <div>
                            <div className="font-medium text-sm">{record.category}</div>
                            {record.chip && (
                              <Badge variant="secondary" size="xs" shape="pill" className="mt-1">
                                {record.chip}
                              </Badge>
                            )}
                          </div>
                        ),
                      },
                      {
                        key: 'holders',
                        title: 'Holders',
                        render: (value, record) => <span className="text-sm">{record.holders}</span>
                      },
                      {
                        key: 'percentage',
                        title: '% Holding',
                        render: (value, record) => <span className="font-semibold text-sm">{record.percentage}</span>
                      },
                      {
                        key: 'shares',
                        title: 'Shares (Est.)',
                        render: (value, record) => <span className="text-sm">{record.shares}</span>
                      },
                      {
                        key: 'trend',
                        title: 'Trend (6M)',
                        render: (value, record) => (
                          <div className="flex justify-center">
                            <TrendBar data={record.trend} />
                          </div>
                        ),
                      },
                    ]}
                  />
                  </div>
                </CardBody>
              </Card>

              <Card variant="panel" className="mt-4 md:mt-5">
                <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
                  Major Institutional Holders (Top 5)
                </CardHeader>
                <CardBody className="p-4">
                  <div className="py-8 text-center text-gray-400 italic text-sm">
                    Detailed holder data requires Premium Access.
                  </div>
                </CardBody>
              </Card>
            </div>

            {/* Right Column: Market Statistics */}
            <div>
              <Card variant="panel">
                <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
                  Market Statistics
                </CardHeader>
                <CardBody className="p-4">
                  <Table
                    dataSource={marketStats.map((item, idx) => ({ id: idx, ...item }))}
                    density="compact"
                    borderStyle="minimal"
                    columns={[
                      {
                        key: 'label',
                        title: 'Metric',
                        render: (value, record) => <span className="text-gray-600 text-sm">{record.label}</span>
                      },
                      {
                        key: 'value',
                        title: 'Value',
                        render: (value, record) => (
                          <span className={`text-sm ${record.color || ''}`}>{record.value}</span>
                        )
                      },
                    ]}
                  />
                </CardBody>
              </Card>

              <Card variant="panel" className="mt-4 md:mt-5">
                <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
                  Insider Actions
                </CardHeader>
                <CardBody className="p-4">
                  <div className="text-[0.85rem] text-gray-600 mb-4">Last 6 months</div>
                  <div className="flex gap-2.5 items-center mb-2.5">
                    <div className="w-7 h-7 md:w-8 md:h-8 bg-green-50 text-green-600 rounded-full flex items-center justify-center font-bold text-sm">
                      B
                    </div>
                    <div>
                      <div className="font-semibold text-sm">Buy</div>
                      <div className="text-xs text-gray-600">0 Transactions</div>
                    </div>
                  </div>
                  <div className="flex gap-2.5 items-center">
                    <div className="w-7 h-7 md:w-8 md:h-8 bg-red-50 text-red-600 rounded-full flex items-center justify-center font-bold text-sm">
                      S
                    </div>
                    <div>
                      <div className="font-semibold text-sm">Sell</div>
                      <div className="text-xs text-gray-600">0 Transactions</div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
        </TabPanel>

        {/* Other Tab Panels (placeholders) */}
        <TabPanel value="profile">
          <div className="text-center py-12 text-gray-400">Company Profile content coming soon...</div>
        </TabPanel>
        <TabPanel value="financials">
          <div className="text-center py-12 text-gray-400">Financials content coming soon...</div>
        </TabPanel>
        <TabPanel value="chart">
          <div className="text-center py-12 text-gray-400">Chart content coming soon...</div>
        </TabPanel>
        <TabPanel value="returns">
          <div className="text-center py-12 text-gray-400">Trailing Returns content coming soon...</div>
        </TabPanel>
        <TabPanel value="dividends">
          <div className="text-center py-12 text-gray-400">Dividends content coming soon...</div>
        </TabPanel>
        <TabPanel value="news">
          <div className="text-center py-12 text-gray-400">News content coming soon...</div>
        </TabPanel>
        <TabPanel value="analysis">
          <div className="text-center py-12 text-gray-400">Guardian Analysis content coming soon...</div>
        </TabPanel>
      </Tabs>
    </div>
  );
}
