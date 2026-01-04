'use client';

import { useState } from 'react';
import {
  Card, CardHeader, CardBody,
  Table, Badge, Tabs, TabList, Tab, TabPanel,
  Grid, GridItem, Statistic
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
function TrendBar({ data }: { data: number[] }) {
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
  const { ticker } = params;
  const [activeTab, setActiveTab] = useState('holdings');

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Stock Header */}
      <Card className="mb-6">
        <CardBody>
          <Grid cols={3} gap={4}>
            <GridItem>
              <h1 className="text-2xl font-bold">British American Tobacco Bangladesh</h1>
              <div className="text-sm text-gray-600 mt-2">
                Trading Code: <strong>{ticker}</strong> | Scrip: 14259 | Sector: <strong>Food & Allied</strong>
              </div>
            </GridItem>

            <GridItem>
              {/* Sparkline placeholder - can add chart later */}
              <div className="h-16 bg-gray-100 rounded flex items-center justify-center text-gray-400 text-sm">
                Price Chart
              </div>
            </GridItem>

            <GridItem className="text-right">
              <Statistic
                value={248.60}
                suffix=" BDT"
                precision={2}
                className="text-3xl font-light"
              />
              <Badge variant="secondary" className="mt-2">Closed</Badge>
            </GridItem>
          </Grid>
        </CardBody>
      </Card>

      {/* Tabs Navigation */}
      <Tabs value={activeTab} onChange={(key) => setActiveTab(key as string)}>
        <TabList>
          <Tab value="summary">Summary</Tab>
          <Tab value="profile">Company Profile</Tab>
          <Tab value="financials">Financials</Tab>
          <Tab value="chart">Chart</Tab>
          <Tab value="holdings">Holdings</Tab>
          <Tab value="returns">Trailing Returns</Tab>
          <Tab value="dividends">Dividends</Tab>
          <Tab value="news">News</Tab>
          <Tab value="analysis">Guardian Analysis</Tab>
        </TabList>

        {/* Holdings Tab Panel */}
        <TabPanel value="holdings">
          {/* Dashboard Grid (3-column layout: 240px-1fr-300px) */}
          <Grid cols={[1, 2, 3]} gap={6} className="mt-6">
            {/* Left Column: Holdings Summary */}
            <GridItem>
              <Card>
                <CardHeader>Holdings Summary</CardHeader>
                <CardBody>
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

              <Card className="mt-4">
                <CardHeader>Basic Info</CardHeader>
                <CardBody>
                  <Table
                    dataSource={basicInfo}
                    columns={[
                      {
                        title: 'Metric',
                        dataIndex: 'label',
                        render: (text) => <span className="text-gray-600">{text}</span>
                      },
                      {
                        title: 'Value',
                        dataIndex: 'value',
                        align: 'right',
                        render: (text, record) => (
                          <span className={record.status === 'success' ? 'text-green-600 font-semibold' : ''}>
                            {text}
                          </span>
                        )
                      },
                    ]}
                    showHeader={false}
                    pagination={false}
                  />
                </CardBody>
              </Card>
            </GridItem>

            {/* Middle Column: Detailed Shareholding */}
            <GridItem colSpan={1}>
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <span>Detailed Shareholding Composition</span>
                    <span className="text-xs font-normal text-gray-500">As of Sep 30, 2024</span>
                  </div>
                </CardHeader>
                <CardBody>
                  <Table
                    dataSource={shareholdingData}
                    columns={[
                      {
                        title: 'Category',
                        dataIndex: 'category',
                        render: (text, record) => (
                          <div>
                            <div className="font-medium">{text}</div>
                            {record.chip && (
                              <Badge variant="secondary" className="mt-1 text-xs">
                                {record.chip}
                              </Badge>
                            )}
                          </div>
                        ),
                      },
                      {
                        title: 'Holders',
                        dataIndex: 'holders',
                      },
                      {
                        title: '% Holding',
                        dataIndex: 'percentage',
                        align: 'right',
                        render: (text) => <span className="font-semibold">{text}</span>
                      },
                      {
                        title: 'Shares (Est.)',
                        dataIndex: 'shares',
                        align: 'right',
                      },
                      {
                        title: 'Trend (6M)',
                        dataIndex: 'trend',
                        align: 'center',
                        render: (trend) => (
                          <div className="flex justify-center">
                            <TrendBar data={trend} />
                          </div>
                        ),
                      },
                    ]}
                    pagination={false}
                  />
                </CardBody>
              </Card>

              <Card className="mt-4">
                <CardHeader>Major Institutional Holders (Top 5)</CardHeader>
                <CardBody>
                  <div className="py-8 text-center text-gray-400 italic text-sm">
                    Detailed holder data requires Premium Access.
                  </div>
                </CardBody>
              </Card>
            </GridItem>

            {/* Right Column: Market Statistics */}
            <GridItem>
              <Card>
                <CardHeader>Market Statistics</CardHeader>
                <CardBody>
                  <Table
                    dataSource={marketStats}
                    columns={[
                      {
                        title: 'Metric',
                        dataIndex: 'label',
                        render: (text) => <span className="text-gray-600">{text}</span>
                      },
                      {
                        title: 'Value',
                        dataIndex: 'value',
                        align: 'right',
                        render: (text, record) => (
                          <span className={record.color || ''}>{text}</span>
                        )
                      },
                    ]}
                    showHeader={false}
                    pagination={false}
                  />
                </CardBody>
              </Card>

              <Card className="mt-4">
                <CardHeader>Insider Actions</CardHeader>
                <CardBody>
                  <div className="text-xs text-gray-600 mb-4">Last 6 months</div>
                  <div className="flex gap-3 items-center mb-3">
                    <div className="w-8 h-8 bg-green-100 text-green-600 rounded-full flex items-center justify-center font-bold">
                      B
                    </div>
                    <div>
                      <div className="font-semibold text-sm">Buy</div>
                      <div className="text-xs text-gray-600">0 Transactions</div>
                    </div>
                  </div>
                  <div className="flex gap-3 items-center">
                    <div className="w-8 h-8 bg-red-100 text-red-600 rounded-full flex items-center justify-center font-bold">
                      S
                    </div>
                    <div>
                      <div className="font-semibold text-sm">Sell</div>
                      <div className="text-xs text-gray-600">0 Transactions</div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </GridItem>
          </Grid>
        </TabPanel>

        {/* Other Tab Panels (placeholders) */}
        <TabPanel value="summary">
          <div className="text-center py-12 text-gray-400">Summary content coming soon...</div>
        </TabPanel>
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
