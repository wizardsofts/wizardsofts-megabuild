/**
 * Company Chart Component
 *
 * Interactive price and volume charts with period selection.
 * Uses Recharts for visualization with responsive design.
 *
 * Features:
 * - Period selector (1D, 5D, 1M, 3M, YTD, 1Y, 5Y, MAX)
 * - Price chart (candlestick/line chart with OHLC data)
 * - Volume bar chart
 * - Auto-fetch data on period change
 * - Mobile-first responsive design
 */

'use client';

import { useState, useEffect, useMemo } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getPriceHistory } from '@/lib/api/company';
import type { ChartPeriod, PriceHistory } from '@/lib/types';

interface CompanyChartProps {
  ticker: string;
  initialPeriod?: ChartPeriod;
}

const PERIODS: Array<{ value: ChartPeriod; label: string }> = [
  { value: '1D', label: '1D' },
  { value: '5D', label: '5D' },
  { value: '1M', label: '1M' },
  { value: '3M', label: '3M' },
  { value: '6M', label: '6M' },
  { value: 'YTD', label: 'YTD' },
  { value: '1Y', label: '1Y' },
  { value: '5Y', label: '5Y' },
  { value: 'MAX', label: 'MAX' },
];

// Mock data for demonstration when backend API is unavailable
const generateMockData = (ticker: string, period: ChartPeriod, dataPoints: number) => {
  const basePrice = 100 + Math.random() * 150;
  const data = [];
  const now = new Date();

  for (let i = dataPoints - 1; i >= 0; i--) {
    const date = new Date(now);

    // Adjust date based on period
    if (period === '1D') {
      date.setMinutes(date.getMinutes() - i * 5);
    } else if (period === '5D') {
      date.setHours(date.getHours() - i * 2);
    } else if (period === '1M') {
      date.setDate(date.getDate() - i);
    } else if (period === '3M') {
      date.setDate(date.getDate() - i * 3);
    } else if (period === '6M') {
      date.setDate(date.getDate() - i * 6);
    } else if (period === 'YTD') {
      date.setDate(date.getDate() - i * 3);
    } else if (period === '1Y') {
      date.setDate(date.getDate() - i * 12);
    } else if (period === '5Y') {
      date.setMonth(date.getMonth() - i * 2);
    } else {
      date.setMonth(date.getMonth() - i * 6);
    }

    const trend = (dataPoints - i) * 0.5;
    const volatility = Math.random() * 10 - 5;
    const price = basePrice + trend + volatility;

    const open = price + (Math.random() * 4 - 2);
    const close = price + (Math.random() * 4 - 2);
    const high = Math.max(open, close) + Math.random() * 3;
    const low = Math.min(open, close) - Math.random() * 3;
    const volume = Math.floor(50000 + Math.random() * 100000);

    data.push({
      date: date.toISOString(),
      open: Math.max(0, open),
      high: Math.max(0, high),
      low: Math.max(0, low),
      close: Math.max(0, close),
      volume,
    });
  }

  return {
    ticker,
    period,
    data,
    data_points: dataPoints,
  };
};

export default function CompanyChart({
  ticker,
  initialPeriod = '1M',
}: CompanyChartProps) {
  const [period, setPeriod] = useState<ChartPeriod>(initialPeriod);
  const [data, setData] = useState<PriceHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingMockData, setUsingMockData] = useState(false);

  // Fetch price history when period changes
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const priceHistory = await getPriceHistory(ticker, period);

        if (!priceHistory) {
          // Fallback to mock data
          console.log('API returned no data, using mock data for', ticker, period);
          const dataPoints = period === '1D' ? 78 : period === '5D' ? 60 : period === '1M' ? 30 : 90;
          const mockData = generateMockData(ticker, period, dataPoints);
          setData(mockData as PriceHistory);
          setUsingMockData(true);
        } else {
          setData(priceHistory);
          setUsingMockData(false);
        }
      } catch (err) {
        // Fallback to mock data on error
        console.log('API error, using mock data for', ticker, period, err);
        const dataPoints = period === '1D' ? 78 : period === '5D' ? 60 : period === '1M' ? 30 : 90;
        const mockData = generateMockData(ticker, period, dataPoints);
        setData(mockData as PriceHistory);
        setUsingMockData(true);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ticker, period]);

  // Calculate price range for Y-axis
  const priceRange = useMemo(() => {
    if (!data || data.data.length === 0) {
      return { min: 0, max: 100 };
    }

    const prices = data.data.flatMap((d) => [d.high, d.low]);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const padding = (max - min) * 0.1; // 10% padding

    return {
      min: Math.floor(min - padding),
      max: Math.ceil(max + padding),
    };
  }, [data]);

  // Format chart data
  const chartData = useMemo(() => {
    if (!data) return [];

    return data.data.map((item) => ({
      date: new Date(item.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      close: item.close,
      volume: item.volume,
      high: item.high,
      low: item.low,
      open: item.open,
    }));
  }, [data]);

  // Custom tooltip for price chart
  const PriceTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.date}</p>
          <div className="mt-1 space-y-1 text-sm">
            <p>
              <span className="text-gray-600">Close: </span>
              <span className="font-medium">৳{data.close.toFixed(2)}</span>
            </p>
            <p>
              <span className="text-gray-600">High: </span>
              <span className="font-medium">৳{data.high.toFixed(2)}</span>
            </p>
            <p>
              <span className="text-gray-600">Low: </span>
              <span className="font-medium">৳{data.low.toFixed(2)}</span>
            </p>
            <p>
              <span className="text-gray-600">Open: </span>
              <span className="font-medium">৳{data.open.toFixed(2)}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom tooltip for volume chart
  const VolumeTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900">{data.date}</p>
          <p className="mt-1 text-sm">
            <span className="text-gray-600">Volume: </span>
            <span className="font-medium">{data.volume.toLocaleString()}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-4">
      {/* Period Selector */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {PERIODS.map((p) => (
          <Button
            key={p.value}
            onClick={() => setPeriod(p.value)}
            variant={period === p.value ? 'default' : 'outline'}
            size="sm"
            className="shrink-0 min-w-[44px] min-h-[44px]"
          >
            {p.label}
          </Button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="h-64 md:h-96 flex items-center justify-center">
            <div className="text-center space-y-2">
              <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full mx-auto" />
              <p className="text-sm text-gray-500">Loading chart data...</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error State */}
      {error && !loading && (
        <Card>
          <CardContent className="h-64 md:h-96 flex items-center justify-center">
            <div className="text-center space-y-2">
              <p className="text-sm text-red-600">{error}</p>
              <Button
                onClick={() => setPeriod('1M')}
                variant="outline"
                size="sm"
              >
                Try 1 Month
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Price Chart */}
      {!loading && !error && data && chartData.length > 0 && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center justify-between">
                <span>📈 Price Chart ({period})</span>
                <div className="flex items-center gap-2">
                  {usingMockData && (
                    <span className="text-xs font-normal px-2 py-1 bg-yellow-100 text-yellow-800 rounded">
                      Demo Data
                    </span>
                  )}
                  <span className="text-sm font-normal text-gray-500">
                    {data.data_points} data points
                  </span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300} className="md:h-96">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <YAxis
                    domain={[priceRange.min, priceRange.max]}
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                    tickFormatter={(value) => `৳${value}`}
                  />
                  <Tooltip content={<PriceTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    name="Close Price"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Volume Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">📊 Trading Volume</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    stroke="#6b7280"
                    tickFormatter={(value) =>
                      value >= 1000000
                        ? `${(value / 1000000).toFixed(1)}M`
                        : value >= 1000
                        ? `${(value / 1000).toFixed(1)}K`
                        : value.toString()
                    }
                  />
                  <Tooltip content={<VolumeTooltip />} />
                  <Bar dataKey="volume" fill="#3b82f6" name="Volume" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </>
      )}

      {/* Empty State */}
      {!loading && !error && (!data || chartData.length === 0) && (
        <Card>
          <CardContent className="h-64 md:h-96 flex items-center justify-center">
            <div className="text-center space-y-2">
              <p className="text-gray-500">No chart data available for this period</p>
              <Button
                onClick={() => setPeriod('1M')}
                variant="outline"
                size="sm"
              >
                Try 1 Month
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
