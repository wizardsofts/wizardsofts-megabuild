/**
 * Company Tabs Component
 *
 * Tabbed navigation for different views: Summary, Chart, Key Metrics, Profile.
 * Mobile-first design with horizontal scroll on mobile.
 */

'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import CompanySummary from './CompanySummary';
import CompanyChart from './CompanyChart';
import CompanyKeyMetrics from './CompanyKeyMetrics';
import CompanyProfile from './CompanyProfile';
import type { CompanyTab, CompanyDetails, CompanySignalsResponse } from '@/lib/types';

interface CompanyTabsProps {
  ticker: string;
  companyDetails: CompanyDetails;
  signals: CompanySignalsResponse;
  analysis: {
    signal_type?: 'BUY' | 'SELL' | 'HOLD';
    confidence?: number;
    total_score?: number;
    decision_tree?: {
      trend_score?: number;
      momentum_score?: number;
      volatility_score?: number;
      volume_score?: number;
    };
  } | null;
}

export default function CompanyTabs({
  ticker,
  companyDetails,
  signals,
  analysis,
}: CompanyTabsProps) {
  const [activeTab, setActiveTab] = useState<CompanyTab>('summary');

  const tabs: Array<{ id: CompanyTab; label: string; icon: string }> = [
    { id: 'summary', label: 'Summary', icon: '📊' },
    { id: 'chart', label: 'Chart', icon: '📈' },
    { id: 'key-metrics', label: 'Key Metrics', icon: '🎯' },
    { id: 'profile', label: 'Profile', icon: '🏢' },
  ];

  return (
    <Card>
      {/* Tab Navigation */}
      <CardHeader className="border-b">
        <div className="flex gap-2 overflow-x-auto pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg font-medium
                transition-colors whitespace-nowrap min-h-[44px]
                ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }
              `}
            >
              <span>{tab.icon}</span>
              <span className="text-sm">{tab.label}</span>
            </button>
          ))}
        </div>
      </CardHeader>

      {/* Tab Content */}
      <CardContent className="mt-6">
        {activeTab === 'summary' && (
          <CompanySummary
            indicators={companyDetails.indicators}
            signals={signals}
            analysis={analysis}
          />
        )}

        {activeTab === 'chart' && <CompanyChart ticker={ticker} />}

        {activeTab === 'key-metrics' && (
          <CompanyKeyMetrics indicators={companyDetails.indicators} />
        )}

        {activeTab === 'profile' && <CompanyProfile company={companyDetails.company} />}
      </CardContent>
    </Card>
  );
}
