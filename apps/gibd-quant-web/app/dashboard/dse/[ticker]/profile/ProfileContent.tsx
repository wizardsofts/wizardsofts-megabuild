/**
 * Company Profile Content - Tab content only
 *
 * Rendered inside the parent TickerPage's profile tab
 *
 * TODO: Replace with wizwebui Card, CardHeader, CardBody components
 * once the library exports are fixed in the dist build.
 * Currently using Tailwind CSS for layout as a temporary solution.
 *
 * @see https://github.com/wizardsofts/wizwebui - Fix dist build exports
 */

interface ProfileContentProps {
  ticker: string;
}

export default function ProfileContent({ ticker }: ProfileContentProps) {
  // Company data - In production, this would come from an API
  const companyData = {
    name: 'British American Tobacco Bangladesh',
    ticker: ticker,
    sector: 'Food & Allied',
    scrip: '14259',
    website: 'www.bat-bangladesh.com',
    employees: '1,200+',
    founded: '1928',
    description:
      'British American Tobacco Bangladesh Limited is a leading cigarette manufacturer and distributor in Bangladesh. The company operates under the BAT group and maintains a significant market presence in the tobacco industry.',
    headquarters: 'Dhaka, Bangladesh',
  };

  return (
    <div className="space-y-5">
      {/* Company Overview Card */}
      <div className="rounded-lg border border-gray-200 p-6 bg-white">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Company Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-600 mb-1">Trading Code</p>
            <p className="text-lg font-medium text-gray-900">{companyData.ticker}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Scrip Code</p>
            <p className="text-lg font-medium text-gray-900">{companyData.scrip}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Sector</p>
            <p className="text-lg font-medium text-gray-900">{companyData.sector}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Headquarters</p>
            <p className="text-lg font-medium text-gray-900">{companyData.headquarters}</p>
          </div>
        </div>
      </div>

      {/* Company Description Card */}
      <div className="rounded-lg border border-gray-200 p-6 bg-white">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">About the Company</h2>
        <p className="text-gray-700 leading-relaxed mb-4">{companyData.description}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-200">
          <div>
            <p className="text-sm text-gray-600 mb-1">Founded</p>
            <p className="text-base font-medium text-gray-900">{companyData.founded}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Employees</p>
            <p className="text-base font-medium text-gray-900">{companyData.employees}</p>
          </div>
        </div>
      </div>

      {/* Business Segments Card */}
      <div className="rounded-lg border border-gray-200 p-6 bg-white">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Business Segments</h2>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0"></div>
            <div>
              <p className="font-medium text-gray-900">Cigarette Manufacturing</p>
              <p className="text-sm text-gray-600">Production and distribution of cigarettes</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-2 h-2 rounded-full bg-blue-600 mt-2 flex-shrink-0"></div>
            <div>
              <p className="font-medium text-gray-900">Retail Distribution</p>
              <p className="text-sm text-gray-600">Nationwide distribution network</p>
            </div>
          </div>
        </div>
      </div>

      {/* Key Information Card */}
      <div className="rounded-lg border border-gray-200 p-6 bg-white">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Information</h2>
        <div className="space-y-4">
          <div className="flex justify-between items-start py-2 border-b border-gray-100">
            <span className="text-gray-600">Market Cap</span>
            <span className="font-medium text-gray-900">Coming Soon</span>
          </div>
          <div className="flex justify-between items-start py-2 border-b border-gray-100">
            <span className="text-gray-600">P/E Ratio</span>
            <span className="font-medium text-gray-900">Coming Soon</span>
          </div>
          <div className="flex justify-between items-start py-2 border-b border-gray-100">
            <span className="text-gray-600">Dividend Yield</span>
            <span className="font-medium text-gray-900">Coming Soon</span>
          </div>
          <div className="flex justify-between items-start py-2">
            <span className="text-gray-600">Book Value</span>
            <span className="font-medium text-gray-900">Coming Soon</span>
          </div>
        </div>
      </div>

      {/* Info Box */}
      <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
        <p className="text-sm text-blue-900">
          💡 <strong>Tip:</strong> Additional company data (detailed financials, historical charts, news) will be available as we integrate more data sources.
        </p>
      </div>
    </div>
  );
}
