/**
 * Company Profile Component
 *
 * Displays comprehensive company information including:
 * - Basic company details (ticker, name, sector, category)
 * - Listing information
 * - Placeholders for future features (financials, ownership, etc.)
 *
 * Responsive 2-column layout
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { CompanyInfo } from '@/lib/types';

interface CompanyProfileProps {
  company: CompanyInfo;
}

export default function CompanyProfile({ company }: CompanyProfileProps) {
  return (
    <div className="space-y-6">
      {/* Company Information Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            🏢 Company Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500 mb-1">Trading Code</div>
                <div className="font-semibold text-gray-900 flex items-center gap-2">
                  <Badge variant="outline" className="text-base">
                    {company.ticker}
                  </Badge>
                </div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">Company Name</div>
                <div className="font-semibold text-gray-900">{company.company_name}</div>
              </div>

              <div>
                <div className="text-sm text-gray-500 mb-1">Sector</div>
                <div className="font-semibold text-gray-900">{company.sector}</div>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <div className="text-sm text-gray-500 mb-1">Market Category</div>
                <div className="font-semibold text-gray-900">
                  <Badge variant="default">{company.category}</Badge>
                </div>
              </div>

              {company.listing_year && (
                <div>
                  <div className="text-sm text-gray-500 mb-1">Listing Year</div>
                  <div className="font-semibold text-gray-900">{company.listing_year}</div>
                </div>
              )}

              <div>
                <div className="text-sm text-gray-500 mb-1">Exchange</div>
                <div className="font-semibold text-gray-900">
                  Dhaka Stock Exchange (DSE)
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Future Features - Placeholder Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Financial Metrics Placeholder */}
        <Card className="bg-gray-50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2 text-gray-500">
              💰 Financial Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">
              Financial metrics will be available in a future update:
            </p>
            <ul className="mt-2 space-y-1 text-sm text-gray-400 list-disc list-inside">
              <li>Market Capitalization</li>
              <li>P/E Ratio</li>
              <li>EPS (Earnings Per Share)</li>
              <li>Dividend Yield</li>
              <li>Book Value</li>
            </ul>
          </CardContent>
        </Card>

        {/* Ownership Placeholder */}
        <Card className="bg-gray-50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2 text-gray-500">
              👥 Ownership Structure
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500">
              Ownership information will be available in a future update:
            </p>
            <ul className="mt-2 space-y-1 text-sm text-gray-400 list-disc list-inside">
              <li>Sponsor/Director Holdings</li>
              <li>Institutional Holdings</li>
              <li>Public Holdings</li>
              <li>Foreign Holdings</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* Company Description Placeholder */}
      <Card className="bg-gray-50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2 text-gray-500">
            📝 Company Description
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-500">
            Detailed company description, business model, and operations will be available
            in a future update.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
