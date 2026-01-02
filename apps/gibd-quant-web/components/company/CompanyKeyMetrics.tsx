/**
 * Company Key Metrics Component
 *
 * Displays technical indicators organized by category:
 * - Momentum Indicators (RSI, ADX)
 * - Moving Averages (SMA 20/50/200)
 * - Volatility Indicators (ATR, MACD)
 *
 * Responsive grid layout: 1 column (mobile) / 2 columns (tablet) / 3 columns (desktop)
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TechnicalIndicators } from '@/lib/types';

interface CompanyKeyMetricsProps {
  indicators: TechnicalIndicators | null;
}

export default function CompanyKeyMetrics({ indicators }: CompanyKeyMetricsProps) {
  if (!indicators) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No technical indicator data available</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Momentum Indicators Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            🚀 Momentum Indicators
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {indicators.RSI_14 !== undefined && (
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">RSI (14)</span>
                  <span
                    className={`text-lg font-bold ${
                      indicators.RSI_14 > 70
                        ? 'text-red-600'
                        : indicators.RSI_14 < 30
                        ? 'text-green-600'
                        : 'text-gray-900'
                    }`}
                  >
                    {indicators.RSI_14.toFixed(2)}
                  </span>
                </div>
                <div className="text-xs text-gray-500">
                  {indicators.RSI_14 > 70
                    ? 'Overbought'
                    : indicators.RSI_14 < 30
                    ? 'Oversold'
                    : 'Neutral'}
                </div>
              </div>
            )}

            {indicators.ADX_14 !== undefined && (
              <div className="pt-3 border-t">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">ADX (14)</span>
                  <span className="text-lg font-bold text-gray-900">
                    {indicators.ADX_14.toFixed(2)}
                  </span>
                </div>
                <div className="text-xs text-gray-500">
                  {indicators.ADX_14 > 25
                    ? 'Strong Trend'
                    : indicators.ADX_14 > 20
                    ? 'Moderate Trend'
                    : 'Weak Trend'}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Moving Averages Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            📊 Moving Averages
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {indicators.SMA_20 !== undefined && (
              <div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">SMA (20)</span>
                  <span className="text-lg font-bold text-gray-900">
                    ৳{indicators.SMA_20.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            {indicators.SMA_50 !== undefined && (
              <div className="pt-3 border-t">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">SMA (50)</span>
                  <span className="text-lg font-bold text-gray-900">
                    ৳{indicators.SMA_50.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            {indicators.SMA_200 !== undefined && (
              <div className="pt-3 border-t">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">SMA (200)</span>
                  <span className="text-lg font-bold text-gray-900">
                    ৳{indicators.SMA_200.toFixed(2)}
                  </span>
                </div>
              </div>
            )}

            {indicators.SMA_20 && indicators.SMA_50 && (
              <div className="pt-3 border-t">
                <div className="text-xs text-gray-500">
                  {indicators.SMA_20 > indicators.SMA_50
                    ? '📈 Short-term above medium-term (Bullish)'
                    : '📉 Short-term below medium-term (Bearish)'}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Volatility Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            📉 Volatility & MACD
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {indicators.ATR_14 !== undefined && (
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">ATR (14)</span>
                  <span className="text-lg font-bold text-gray-900">
                    {indicators.ATR_14.toFixed(2)}
                  </span>
                </div>
                <div className="text-xs text-gray-500">Average True Range</div>
              </div>
            )}

            {indicators.MACD_histogram_12_26_9 !== undefined && (
              <div className="pt-3 border-t">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-gray-600">MACD Histogram</span>
                  <span
                    className={`text-lg font-bold ${
                      indicators.MACD_histogram_12_26_9 > 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {indicators.MACD_histogram_12_26_9.toFixed(3)}
                  </span>
                </div>
                <div className="text-xs text-gray-500">
                  {indicators.MACD_histogram_12_26_9 > 0 ? 'Bullish' : 'Bearish'}
                </div>
              </div>
            )}

            {indicators.MACD_line_12_26_9 !== undefined &&
              indicators.MACD_signal_12_26_9 !== undefined && (
                <div className="pt-3 border-t space-y-1">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-600">MACD Line</span>
                    <span className="font-medium">
                      {indicators.MACD_line_12_26_9.toFixed(3)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-gray-600">Signal Line</span>
                    <span className="font-medium">
                      {indicators.MACD_signal_12_26_9.toFixed(3)}
                    </span>
                  </div>
                </div>
              )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
