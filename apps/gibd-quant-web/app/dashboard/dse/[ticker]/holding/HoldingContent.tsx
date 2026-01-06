/**
 * Holdings Content - Tab content only
 *
 * Rendered inside the parent TickerPage's holdings tab
 *
 * TODO: Replace with wizwebui Card, CardHeader, CardBody, Table, Badge components
 * once the library exports are fixed in the dist build.
 * Currently using Tailwind CSS for layout as a temporary solution.
 *
 * @see https://github.com/wizardsofts/wizwebui - Fix dist build exports
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

// Badge component using Tailwind
function Badge({ variant, children }: { variant: 'success' | 'warning' | 'secondary'; children: React.ReactNode }) {
  const variantClasses = {
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    secondary: 'bg-gray-100 text-gray-800',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${variantClasses[variant]}`}>
      {children}
    </span>
  );
}

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
        {/* Pie Chart Card */}
        <div className="rounded-lg border border-gray-200 bg-white">
          <div className="px-4 py-3 border-b border-gray-100">
            <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Holdings Summary
            </span>
          </div>
          <div className="p-4">
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
          </div>
        </div>

        {/* Basic Info Card */}
        <div className="rounded-lg border border-gray-200 bg-white mt-4 md:mt-5">
          <div className="px-4 py-3 border-b border-gray-100">
            <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Basic Info
            </span>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {basicInfo.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center border-b border-gray-100 pb-2 last:border-0 last:pb-0">
                  <span className="text-sm text-gray-600">{item.label}</span>
                  <span className={`text-sm ${item.status === 'success' ? 'text-green-600 font-semibold' : 'font-medium'}`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Middle Column: Detailed Shareholding */}
      <div>
        {/* Detailed Shareholding Table */}
        <div className="rounded-lg border border-gray-200 bg-white">
          <div className="px-4 py-3 border-b border-gray-100">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-1">
              <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                Detailed Shareholding Composition
              </span>
              <span className="text-xs font-normal text-gray-500">As of Sep 30, 2024</span>
            </div>
          </div>
          <div className="p-4">
            <div className="overflow-x-auto -mx-4 md:mx-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 px-2 font-medium text-gray-600">Category</th>
                    <th className="text-left py-2 px-2 font-medium text-gray-600">Holders</th>
                    <th className="text-left py-2 px-2 font-medium text-gray-600">% Holding</th>
                    <th className="text-left py-2 px-2 font-medium text-gray-600">Shares (Est.)</th>
                    <th className="text-center py-2 px-2 font-medium text-gray-600">Trend (6M)</th>
                  </tr>
                </thead>
                <tbody>
                  {shareholdingData.map((item, idx) => (
                    <tr key={idx} className="border-b border-gray-100 last:border-0">
                      <td className="py-3 px-2">
                        <div className="font-medium text-gray-900">{item.category}</div>
                        {item.chip && (
                          <Badge variant="secondary">
                            {item.chip}
                          </Badge>
                        )}
                      </td>
                      <td className="py-3 px-2 text-gray-700">{item.holders}</td>
                      <td className="py-3 px-2 font-semibold text-gray-900">{item.percentage}</td>
                      <td className="py-3 px-2 text-gray-700">{item.shares}</td>
                      <td className="py-3 px-2">
                        <div className="flex justify-center">
                          <TrendBar data={item.trend} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Major Institutional Holders */}
        <div className="rounded-lg border border-gray-200 bg-white mt-4 md:mt-5">
          <div className="px-4 py-3 border-b border-gray-100">
            <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Major Institutional Holders (Top 5)
            </span>
          </div>
          <div className="p-4">
            <div className="py-8 text-center text-gray-400 italic text-sm">
              Detailed holder data requires Premium Access.
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Market Statistics */}
      <div>
        {/* Market Statistics Card */}
        <div className="rounded-lg border border-gray-200 bg-white">
          <div className="px-4 py-3 border-b border-gray-100">
            <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Market Statistics
            </span>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {marketStats.map((item, idx) => (
                <div key={idx} className="flex justify-between items-center border-b border-gray-100 pb-2 last:border-0 last:pb-0">
                  <span className="text-sm text-gray-600">{item.label}</span>
                  <span className={`text-sm font-medium ${item.color || 'text-gray-900'}`}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Insider Actions Card */}
        <div className="rounded-lg border border-gray-200 bg-white mt-4 md:mt-5">
          <div className="px-4 py-3 border-b border-gray-100">
            <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
              Insider Actions
            </span>
          </div>
          <div className="p-4">
            <div className="py-8 text-center text-gray-400 italic text-sm">
              No recent insider transactions.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
