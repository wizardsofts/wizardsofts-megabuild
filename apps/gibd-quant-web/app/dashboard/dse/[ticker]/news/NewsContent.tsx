'use client';

import { useState } from 'react';
import { Card, CardHeader, CardBody, Badge } from '@wizwebui/core';

/**
 * News Content - Tab content only
 *
 * Rendered inside the parent TickerPage's news tab
 *
 * Component Library: wizwebui v0.2.0
 */

interface NewsContentProps {
  ticker: string;
}

// Mock data - Replace with API calls in production
const newsArticles = [
  {
    id: 1,
    date: '2025-01-04',
    category: 'Corporate Action',
    title: 'Board Meeting Scheduled for Q4 2024 Results',
    summary: 'The Board of Directors will meet on January 15, 2025, to review and approve the financial results for Q4 2024 and discuss dividend recommendations.',
    source: 'DSE News',
    year: 2025,
    badge: 'Important',
    badgeVariant: 'warning' as const,
  },
  {
    id: 2,
    date: '2025-01-02',
    category: 'Financials',
    title: 'BATBC Maintains Market Leadership in Q4',
    summary: 'British American Tobacco Bangladesh continues to hold dominant position in the tobacco sector with 72% market share, according to industry reports.',
    source: 'Company Site',
    year: 2025,
    badge: null,
    badgeVariant: null,
  },
  {
    id: 3,
    date: '2024-12-28',
    category: 'Price Sensitive',
    title: 'Price Sensitive Information Disclosure',
    summary: 'Company disclosed material information regarding production capacity expansion plan for FY2025, subject to board approval.',
    source: 'DSE News',
    year: 2024,
    badge: 'Filing',
    badgeVariant: 'info' as const,
  },
  {
    id: 4,
    date: '2024-12-20',
    category: 'Corporate Action',
    title: 'Interim Dividend Declared',
    summary: 'Board of Directors declared interim cash dividend of Tk 25 per share for the year ending December 31, 2024. Record date: January 10, 2025.',
    source: 'Company Site',
    year: 2024,
    badge: 'Dividend',
    badgeVariant: 'success' as const,
  },
  {
    id: 5,
    date: '2024-12-15',
    category: 'Financials',
    title: 'Excise Duty Impact on Tobacco Sector',
    summary: 'National Board of Revenue announced revised excise duty structure for tobacco products, expected to impact industry margins in FY2025.',
    source: 'Press Releases',
    year: 2024,
    badge: null,
    badgeVariant: null,
  },
  {
    id: 6,
    date: '2024-11-10',
    category: 'Directorship',
    title: 'New Independent Director Appointed',
    summary: 'The Board has appointed Mr. Rahman as an Independent Director, effective November 15, 2024.',
    source: 'DSE News',
    year: 2024,
    badge: null,
    badgeVariant: null,
  },
  {
    id: 7,
    date: '2023-12-30',
    category: 'Price Sensitive',
    title: 'Annual Production Targets Announced',
    summary: 'Company announced production targets for FY2024, projecting 5% growth over previous year.',
    source: 'Company Site',
    year: 2023,
    badge: null,
    badgeVariant: null,
  },
];

const corporateActions = [
  {
    date: '2025-01-10',
    type: 'Record Date',
    description: 'Interim Dividend Record Date',
    details: 'Tk 25 per share',
  },
  {
    date: '2025-01-15',
    type: 'Board Meeting',
    description: 'Q4 2024 Results Review',
    details: 'Financial results approval',
  },
  {
    date: '2024-03-25',
    type: 'AGM',
    description: 'Annual General Meeting',
    details: 'FY2024 accounts approval',
  },
  {
    date: '2024-03-15',
    type: 'Book Closure',
    description: 'Book Closure Period',
    details: 'March 15-25, 2024',
  },
];

const upcomingEvents = [
  {
    date: '2025-01-15',
    event: 'Board Meeting',
    description: 'Q4 2024 Financial Results',
  },
  {
    date: '2025-01-20',
    event: 'Dividend Payment',
    description: 'Interim Dividend Disbursement',
  },
  {
    date: '2025-03-25',
    event: 'AGM 2025',
    description: 'Annual General Meeting',
  },
];

// Format date for display
function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export default function NewsContent({ ticker }: NewsContentProps) {
  // Filter state
  const [selectedSources, setSelectedSources] = useState<string[]>(['All Sources']);
  const [selectedCategories, setSelectedCategories] = useState<string[]>(['Price Sensitive', 'Financials']);
  const [selectedYears, setSelectedYears] = useState<string[]>(['2025']);

  // Toggle filter selection
  const toggleFilter = (
    value: string,
    selectedValues: string[],
    setSelectedValues: (values: string[]) => void,
    isAllOption = false
  ) => {
    if (isAllOption) {
      // If "All" is clicked, select only "All"
      setSelectedValues([value]);
    } else {
      // Remove "All" if other options are selected
      const newValues = selectedValues.includes(value)
        ? selectedValues.filter(v => v !== value)
        : [...selectedValues.filter(v => !v.startsWith('All')), value];

      // If no values selected, default to "All"
      setSelectedValues(newValues.length === 0 ? ['All Sources'] : newValues);
    }
  };

  // Filter news articles
  const filteredArticles = newsArticles.filter(article => {
    const sourceMatch = selectedSources.includes('All Sources') || selectedSources.includes(article.source);
    const categoryMatch = selectedCategories.length === 0 || selectedCategories.includes(article.category);
    const yearMatch = selectedYears.includes(article.year.toString()) ||
      (selectedYears.includes('Older') && article.year < 2023);

    return sourceMatch && categoryMatch && yearMatch;
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr_300px] gap-4 md:gap-6 mt-4 md:mt-6">
      {/* Left Column: Filters */}
      <div className="space-y-4">
        {/* Source Filter */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600 font-semibold">
            Source
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-2">
              {['All Sources', 'DSE News', 'Company Site', 'Press Releases'].map((source) => (
                <label key={source} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedSources.includes(source)}
                    onChange={() => toggleFilter(source, selectedSources, setSelectedSources, source === 'All Sources')}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{source}</span>
                </label>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Category Filter */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600 font-semibold">
            Category
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-2">
              {['Price Sensitive', 'Financials', 'Corporate Action', 'Directorship'].map((category) => (
                <label key={category} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category)}
                    onChange={() => toggleFilter(category, selectedCategories, setSelectedCategories)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{category}</span>
                </label>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Year Filter */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600 font-semibold">
            Year
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-2">
              {['2025', '2024', '2023', 'Older'].map((year) => (
                <label key={year} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedYears.includes(year)}
                    onChange={() => toggleFilter(year, selectedYears, setSelectedYears)}
                    className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">{year}</span>
                </label>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Middle Column: News Articles */}
      <div className="space-y-4 md:space-y-5">
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            <div className="flex justify-between items-center">
              <span>Recent News & Announcements</span>
              <span className="text-xs font-normal normal-case text-gray-500">
                {filteredArticles.length} {filteredArticles.length === 1 ? 'article' : 'articles'}
              </span>
            </div>
          </CardHeader>
          <CardBody className="p-4">
            {filteredArticles.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                No news articles match the selected filters.
              </div>
            ) : (
              <div className="space-y-4">
                {filteredArticles.map((article) => (
                  <div
                    key={article.id}
                    className="border-b border-gray-100 pb-4 last:border-0 last:pb-0"
                  >
                    {/* Date and Category */}
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">
                          {formatDate(article.date)}
                        </span>
                        <span className="text-xs text-gray-400">•</span>
                        <span className="text-xs text-gray-600 font-medium">
                          {article.category}
                        </span>
                      </div>
                      {article.badge && article.badgeVariant && (
                        <Badge variant={article.badgeVariant} size="xs" shape="pill">
                          {article.badge}
                        </Badge>
                      )}
                    </div>

                    {/* Title */}
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">
                      {article.title}
                    </h3>

                    {/* Summary */}
                    <p className="text-sm text-gray-700 leading-relaxed mb-2">
                      {article.summary}
                    </p>

                    {/* Source */}
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <span>Source:</span>
                      <span className="font-medium">{article.source}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>

        {/* Corporate Actions History */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            Corporate Actions History
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-3">
              {corporateActions.map((action, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 border-b border-gray-100 pb-3 last:border-0 last:pb-0"
                >
                  {/* Date */}
                  <div className="flex-shrink-0 w-20">
                    <div className="text-xs font-semibold text-gray-900">
                      {formatDate(action.date)}
                    </div>
                  </div>

                  {/* Type Badge */}
                  <div className="flex-shrink-0">
                    <Badge
                      variant={
                        action.type === 'Record Date'
                          ? 'success'
                          : action.type === 'Board Meeting'
                          ? 'warning'
                          : action.type === 'AGM'
                          ? 'info'
                          : 'secondary'
                      }
                      size="xs"
                      shape="pill"
                      className="min-w-20 text-center"
                    >
                      {action.type}
                    </Badge>
                  </div>

                  {/* Details */}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900">
                      {action.description}
                    </div>
                    <div className="text-xs text-gray-600 mt-0.5">
                      {action.details}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Right Column: Quick Access */}
      <div className="space-y-4 md:space-y-5">
        {/* Upcoming Events */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            Upcoming Events
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-3">
              {upcomingEvents.map((event, index) => (
                <div
                  key={index}
                  className="border-b border-gray-100 pb-3 last:border-0 last:pb-0"
                >
                  <div className="text-xs font-semibold text-blue-600 mb-1">
                    {formatDate(event.date)}
                  </div>
                  <div className="text-sm font-medium text-gray-900 mb-0.5">
                    {event.event}
                  </div>
                  <div className="text-xs text-gray-600">
                    {event.description}
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Quick Access */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            Quick Access
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-2">
              <button className="w-full text-left px-3 py-2 rounded text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2">
                <span className="text-lg">📋</span>
                <span>AGM / EGM Notices</span>
              </button>
              <button className="w-full text-left px-3 py-2 rounded text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2">
                <span className="text-lg">📊</span>
                <span>Annual Reports</span>
              </button>
              <button className="w-full text-left px-3 py-2 rounded text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center gap-2">
                <span className="text-lg">💰</span>
                <span>Dividend History</span>
              </button>
            </div>
          </CardBody>
        </Card>

        {/* Disclaimer */}
        <Card variant="panel">
          <CardBody className="p-4">
            <div className="text-xs text-gray-500 leading-relaxed">
              <strong className="text-gray-700">Disclaimer:</strong> The information
              provided is for informational purposes only and should not be considered
              as investment advice. Please verify all information from official sources
              before making investment decisions.
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
