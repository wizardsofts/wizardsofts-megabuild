/**
 * Company Header Component
 *
 * Displays company name, ticker, current price, and key metrics.
 * Shows current signal badge with confidence if analysis is available.
 * Mobile-first design with responsive layout.
 */

'use client';

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { CompanyInfo, PriceData, TechnicalIndicators } from '@/lib/types';

interface CompanyHeaderProps {
  company: CompanyInfo;
  latestPrice: PriceData | null;
  indicators: TechnicalIndicators | null;
  analysis: {
    signal_type?: 'BUY' | 'SELL' | 'HOLD';
    confidence?: number;
    total_score?: number;
  } | null;
}

export default function CompanyHeader({
  company,
  latestPrice,
  indicators,
  analysis,
}: CompanyHeaderProps) {
  // Calculate daily change if we have price data
  const dailyChange = latestPrice
    ? ((latestPrice.close - latestPrice.open) / latestPrice.open) * 100
    : 0;

  const changeColor = dailyChange >= 0 ? 'text-green-600' : 'text-red-600';
  const changeBg = dailyChange >= 0 ? 'bg-green-50' : 'bg-red-50';

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          {/* Company Info */}
          <div className="space-y-2">
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
              {company.company_name}
            </h1>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="text-sm font-bold">
                {company.ticker}
              </Badge>
              <Badge variant="default" className="text-sm">
                {company.sector}
              </Badge>
              <Badge variant="default" className="text-sm">
                {company.category}
              </Badge>
              {analysis?.signal_type && (
                <Badge
                  variant={
                    analysis.signal_type === 'BUY'
                      ? 'buy'
                      : analysis.signal_type === 'SELL'
                      ? 'sell'
                      : 'hold'
                  }
                  className="text-sm"
                >
                  {analysis.signal_type}
                  {analysis.confidence && (
                    <span className="ml-1 opacity-80">
                      ({(analysis.confidence * 100).toFixed(0)}%)
                    </span>
                  )}
                </Badge>
              )}
            </div>
          </div>

          {/* Current Price */}
          {latestPrice && (
            <div className="flex flex-col items-start md:items-end">
              <div className="text-3xl font-bold text-gray-900">
                ৳{latestPrice.close.toFixed(2)}
              </div>
              <div className={`text-sm font-medium ${changeColor}`}>
                {dailyChange >= 0 ? '+' : ''}
                {dailyChange.toFixed(2)}%
              </div>
            </div>
          )}
        </div>
      </CardHeader>

      {/* Key Metrics Grid */}
      {latestPrice && (
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
            <div>
              <div className="text-xs text-gray-500">Day Range</div>
              <div className="text-sm font-medium text-gray-900">
                ৳{latestPrice.low.toFixed(2)} - ৳{latestPrice.high.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Volume</div>
              <div className="text-sm font-medium text-gray-900">
                {latestPrice.volume.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Open</div>
              <div className="text-sm font-medium text-gray-900">
                ৳{latestPrice.open.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Previous Close</div>
              <div className="text-sm font-medium text-gray-900">
                ৳{latestPrice.close.toFixed(2)}
              </div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
