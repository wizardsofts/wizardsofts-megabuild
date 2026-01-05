/**
 * Company Detail Page
 *
 * Morningstar-style company detail page with interactive charts,
 * trading signals, and comprehensive company information.
 */

import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { getCompanyDetails, getCompanySignals, analyzeCompany } from '@/lib/api/company';
import CompanyHeader from '@/components/company/CompanyHeader';
import CompanyTabs from '@/components/company/CompanyTabs';

interface PageProps {
  params: Promise<{
    ticker: string;
  }>;
}

/**
 * Generate metadata for SEO
 */
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { ticker } = await params;
  const upperTicker = ticker.toUpperCase();
  const details = await getCompanyDetails(upperTicker);

  if (!details) {
    return {
      title: `${upperTicker} Not Found - Guardian Investment BD`,
      description: `Company ${upperTicker} not found in our database`,
    };
  }

  return {
    title: `${details.company.company_name} (${upperTicker}) - Guardian Investment BD`,
    description: `View detailed analysis, trading signals, and charts for ${details.company.company_name} (${upperTicker}). Sector: ${details.company.sector}`,
    openGraph: {
      title: `${details.company.company_name} (${upperTicker})`,
      description: `${details.company.sector} | ${details.company.category}`,
    },
  };
}

/**
 * Main Company Page Component (Server Component)
 */
export default async function CompanyPage({ params }: PageProps) {
  const { ticker } = await params;
  const upperTicker = ticker.toUpperCase();

  // Fetch all data in parallel for better performance
  const [companyDetails, companySignals, analysisData] = await Promise.all([
    getCompanyDetails(upperTicker),
    getCompanySignals(upperTicker, 20),
    analyzeCompany(upperTicker),
  ]);

  // Handle case where company is not found
  if (!companyDetails) {
    notFound();
  }

  // Type assertion for analysis data
  const analysis = analysisData as {
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Company Header with key metrics */}
        <CompanyHeader
          company={companyDetails.company}
          latestPrice={companyDetails.latest_price}
          indicators={companyDetails.indicators}
          analysis={analysis}
        />

        {/* Tabbed content area */}
        <div className="mt-6">
          <CompanyTabs
            ticker={upperTicker}
            companyDetails={companyDetails}
            signals={companySignals}
            analysis={analysis}
          />
        </div>
      </div>
    </div>
  );
}
