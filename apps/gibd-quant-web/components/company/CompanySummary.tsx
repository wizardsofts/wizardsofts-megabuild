/**
 * Company Summary Component
 *
 * Displays comprehensive summary including:
 * - Technical indicators (RSI, SMA, MACD, ADX, ATR)
 * - Current signal analysis with confidence and scores
 * - Recent trading signals history
 *
 * Mobile-first responsive design with 1/2 column grid.
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { TechnicalIndicators, CompanySignalsResponse } from '@/lib/types';

interface CompanySummaryProps {
  indicators: TechnicalIndicators | null;
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

export default function CompanySummary({
  indicators,
  signals,
  analysis,
}: CompanySummaryProps) {
  return (
    <div className="space-y-6">
      {/* Technical Indicators & Current Analysis Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Technical Indicators Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              📊 Technical Indicators
            </CardTitle>
          </CardHeader>
          <CardContent>
            {indicators ? (
              <div className="space-y-3">
                {/* Momentum Indicators */}
                {indicators.RSI_14 !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">RSI (14)</span>
                    <span
                      className={`text-sm font-semibold ${
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
                )}

                {indicators.ADX_14 !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">ADX (14)</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {indicators.ADX_14.toFixed(2)}
                    </span>
                  </div>
                )}

                {/* Moving Averages */}
                <div className="pt-3 border-t">
                  <p className="text-xs font-medium text-gray-500 mb-2">Moving Averages</p>
                  {indicators.SMA_20 !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">SMA (20)</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ৳{indicators.SMA_20.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {indicators.SMA_50 !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">SMA (50)</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ৳{indicators.SMA_50.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {indicators.SMA_200 !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">SMA (200)</span>
                      <span className="text-sm font-semibold text-gray-900">
                        ৳{indicators.SMA_200.toFixed(2)}
                      </span>
                    </div>
                  )}
                </div>

                {/* MACD */}
                {indicators.MACD_line_12_26_9 !== undefined && (
                  <div className="pt-3 border-t">
                    <p className="text-xs font-medium text-gray-500 mb-2">MACD (12,26,9)</p>
                    <div className="space-y-1">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Line</span>
                        <span className="text-sm font-semibold text-gray-900">
                          {indicators.MACD_line_12_26_9.toFixed(3)}
                        </span>
                      </div>
                      {indicators.MACD_signal_12_26_9 !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Signal</span>
                          <span className="text-sm font-semibold text-gray-900">
                            {indicators.MACD_signal_12_26_9.toFixed(3)}
                          </span>
                        </div>
                      )}
                      {indicators.MACD_histogram_12_26_9 !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Histogram</span>
                          <span
                            className={`text-sm font-semibold ${
                              indicators.MACD_histogram_12_26_9 > 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {indicators.MACD_histogram_12_26_9.toFixed(3)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Volatility */}
                {indicators.ATR_14 !== undefined && (
                  <div className="pt-3 border-t">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">ATR (14)</span>
                      <span className="text-sm font-semibold text-gray-900">
                        {indicators.ATR_14.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No indicator data available</p>
            )}
          </CardContent>
        </Card>

        {/* Current Analysis Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              🎯 Current Signal Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            {analysis ? (
              <div className="space-y-4">
                {/* Signal Type */}
                {analysis.signal_type && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Signal</span>
                    <Badge
                      variant={
                        analysis.signal_type === 'BUY'
                          ? 'buy'
                          : analysis.signal_type === 'SELL'
                          ? 'sell'
                          : 'hold'
                      }
                    >
                      {analysis.signal_type}
                    </Badge>
                  </div>
                )}

                {/* Confidence */}
                {analysis.confidence !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Confidence</span>
                    <span className="text-sm font-semibold text-gray-900">
                      {(analysis.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                )}

                {/* Total Score */}
                {analysis.total_score !== undefined && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Total Score</span>
                    <span
                      className={`text-sm font-semibold ${
                        analysis.total_score > 0
                          ? 'text-green-600'
                          : analysis.total_score < 0
                          ? 'text-red-600'
                          : 'text-gray-900'
                      }`}
                    >
                      {analysis.total_score.toFixed(3)}
                    </span>
                  </div>
                )}

                {/* Component Scores */}
                {analysis.decision_tree && (
                  <div className="pt-3 border-t">
                    <p className="text-xs font-medium text-gray-500 mb-2">Component Scores</p>
                    <div className="space-y-1">
                      {analysis.decision_tree.trend_score !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Trend</span>
                          <span className="text-sm font-semibold text-gray-900">
                            {analysis.decision_tree.trend_score.toFixed(3)}
                          </span>
                        </div>
                      )}
                      {analysis.decision_tree.momentum_score !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Momentum</span>
                          <span className="text-sm font-semibold text-gray-900">
                            {analysis.decision_tree.momentum_score.toFixed(3)}
                          </span>
                        </div>
                      )}
                      {analysis.decision_tree.volatility_score !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Volatility</span>
                          <span className="text-sm font-semibold text-gray-900">
                            {analysis.decision_tree.volatility_score.toFixed(3)}
                          </span>
                        </div>
                      )}
                      {analysis.decision_tree.volume_score !== undefined && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Volume</span>
                          <span className="text-sm font-semibold text-gray-900">
                            {analysis.decision_tree.volume_score.toFixed(3)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No analysis data available</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Signals Section (Full Width) */}
      {signals.total > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              📈 Recent Signals ({signals.total})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {signals.signals.slice(0, 10).map((signal, idx) => (
                <div
                  key={idx}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 bg-gray-50 rounded-lg gap-2"
                >
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={
                        signal.signal_type === 'BUY'
                          ? 'buy'
                          : signal.signal_type === 'SELL'
                          ? 'sell'
                          : 'hold'
                      }
                      className="shrink-0"
                    >
                      {signal.signal_type}
                    </Badge>
                    <span className="text-sm text-gray-600">{signal.signal_date}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Entry: </span>
                      <span className="font-medium">৳{signal.entry_price.toFixed(2)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Conf: </span>
                      <span className="font-medium">
                        {typeof signal.confidence === 'number'
                          ? (signal.confidence * 100).toFixed(0)
                          : signal.confidence}
                        %
                      </span>
                    </div>
                    {signal.return_pct !== null && signal.return_pct !== undefined && (
                      <div>
                        <span
                          className={`font-medium ${
                            signal.return_pct > 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {signal.return_pct > 0 ? '+' : ''}
                          {signal.return_pct.toFixed(2)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
