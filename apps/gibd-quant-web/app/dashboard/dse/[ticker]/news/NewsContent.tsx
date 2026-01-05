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
    source: 'DSE Announcement',
    badge: 'Important',
    badgeVariant: 'warning' as const,
  },
  {
    id: 2,
    date: '2025-01-02',
    category: 'Market News',
    title: 'BATBC Maintains Market Leadership in Q4',
    summary: 'British American Tobacco Bangladesh continues to hold dominant position in the tobacco sector with 72% market share, according to industry reports.',
    source: 'Market Analysis',
    badge: null,
    badgeVariant: null,
  },
  {
    id: 3,
    date: '2024-12-28',
    category: 'Regulatory Filing',
    title: 'Price Sensitive Information Disclosure',
    summary: 'Company disclosed material information regarding production capacity expansion plan for FY2025, subject to board approval.',
    source: 'DSE Filing',
    badge: 'Filing',
    badgeVariant: 'info' as const,
  },
  {
    id: 4,
    date: '2024-12-20',
    category: 'Corporate Action',
    title: 'Interim Dividend Declared',
    summary: 'Board of Directors declared interim cash dividend of Tk 25 per share for the year ending December 31, 2024. Record date: January 10, 2025.',
    source: 'Company Announcement',
    badge: 'Dividend',
    badgeVariant: 'success' as const,
  },
  {
    id: 5,
    date: '2024-12-15',
    category: 'Market News',
    title: 'Excise Duty Impact on Tobacco Sector',
    summary: 'National Board of Revenue announced revised excise duty structure for tobacco products, expected to impact industry margins in FY2025.',
    source: 'Industry Update',
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
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-4 md:gap-6 mt-4 md:mt-6">
      {/* Left Column: News Articles */}
      <div className="space-y-4 md:space-y-5">
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            Recent News & Announcements
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-4">
              {newsArticles.map((article) => (
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
                        action.type === 'Dividend' || action.type === 'Record Date'
                          ? 'success'
                          : action.type === 'Board Meeting'
                          ? 'warning'
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

      {/* Right Column: Upcoming Events & Quick Info */}
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

        {/* News Sources */}
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            News Sources
          </CardHeader>
          <CardBody className="p-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 bg-blue-600 rounded-full" />
                <span className="text-gray-700">DSE Announcements</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 bg-green-600 rounded-full" />
                <span className="text-gray-700">Company Filings</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 bg-gray-600 rounded-full" />
                <span className="text-gray-700">Market Analysis</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 bg-yellow-600 rounded-full" />
                <span className="text-gray-700">Regulatory Updates</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="text-xs text-gray-500 text-center">
                News updated every 15 minutes
              </div>
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
