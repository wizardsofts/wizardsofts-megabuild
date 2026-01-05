import {
  Card, CardHeader, CardBody,
  Table, Badge
} from '@wizwebui/core';

/**
 * Holdings Content - Tab content only
 *
 * Rendered inside the parent TickerPage's holdings tab
 *
 * Component Library: wizwebui v0.2.0
 */

interface HoldingContentProps {
  ticker: string;
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

// Trend Bar Component - Data visualization
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

export default function HoldingContent({ ticker }: HoldingContentProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_300px] gap-4 md:gap-6 mt-4 md:mt-6">
      {/* Left Column: Holdings Summary */}
      <div>
        <Card variant="panel">
          <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
            Holdings Summary
          </CardHeader>
          <CardBody className="p-4">
            {/* Pie Chart - CSS Conic Gradient (data visualization) */}
            <div className="flex justify-center mb-5">
              <div
                className="w-36 h-36 rounded-full relative"
                style={{
                  background: `conic-gradient(
                    rgb(52, 58, 64) 0% 72.91%,
                    rgb(0, 86, 179) 72.91% 84.94%,
                    rgb(40, 167, 69) 84.94% 91.78%,
                    rgb(224, 224, 224) 91.78% 100%
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
            <div className="py-8 text-center text-gray-400 italic text-sm">
              No recent insider transactions.
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
