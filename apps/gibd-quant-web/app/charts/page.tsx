/**
 * Charts Dashboard Page (Server Component)
 *
 * LEARNING MODULE 5: CHARTS AND VISUALIZATION
 * -------------------------------------------
 * This page demonstrates the hybrid rendering pattern with charts.
 *
 * Key concepts:
 * 1. **Server-side data fetching** - Same pattern as signals page
 * 2. **Passing data to Client Components** - Charts need "use client"
 * 3. **Dashboard layout** - Organizing multiple charts
 *
 * Data flow:
 * 1. Server Component fetches all signals
 * 2. Passes signals to multiple chart Client Components
 * 3. Each chart transforms data for its visualization
 *
 * File path: frontend/app/charts/page.tsx
 * See: frontend/LEARNING.md#module-5-charts
 */

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  SignalDistributionChart,
  ScoreHistogramChart,
  SectorPerformanceChart,
} from "@/components/charts";
import { Signal, getSignals as fetchSignals } from "@/lib/api";
import Link from "next/link";

/**
 * Fetch signals from the API
 * Uses the centralized API client which handles server/client URL differences
 */
async function getSignals(): Promise<Signal[]> {
  try {
    const response = await fetchSignals({ limit: 1000 });
    return response.signals || [];
  } catch (error) {
    console.error("Failed to fetch signals:", error);
    return [];
  }
}

/**
 * Charts Dashboard Page
 *
 * LEARNING NOTE:
 * This is a Server Component that fetches data and passes it
 * to Client Components (charts). The charts handle their own
 * data transformation and rendering.
 */
export default async function ChartsPage() {
  const signals = await getSignals();

  // Calculate summary stats
  const totalSignals = signals.length;
  const buyCount = signals.filter((s) => s.signal_type === "BUY").length;
  const sellCount = signals.filter((s) => s.signal_type === "SELL").length;
  const holdCount = signals.filter((s) => s.signal_type === "HOLD").length;

  // Calculate average score
  const avgScore =
    signals.length > 0
      ? signals.reduce((sum, s) => sum + (s.total_score || 0), 0) / signals.length
      : 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <nav className="text-sm text-gray-500 mb-2">
          <Link href="/" className="hover:text-gray-700">
            Home
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900">Charts</span>
        </nav>
        <h1 className="text-3xl font-bold text-gray-900">Signal Analytics</h1>
        <p className="text-gray-600 mt-1">
          Visual analysis of {totalSignals} trading signals
        </p>
      </div>

      {/**
       * Summary Stats Cards
       *
       * LEARNING NOTE:
       * Quick stats at the top provide context before diving into charts.
       * Users can see the key numbers at a glance.
       */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{totalSignals}</div>
            <p className="text-sm text-gray-500">Total Signals</p>
          </CardContent>
        </Card>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-green-700">{buyCount}</div>
            <p className="text-sm text-green-600">BUY Signals</p>
          </CardContent>
        </Card>
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="text-2xl font-bold text-red-700">{sellCount}</div>
            <p className="text-sm text-red-600">SELL Signals</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{avgScore.toFixed(2)}</div>
            <p className="text-sm text-gray-500">Avg Score</p>
          </CardContent>
        </Card>
      </div>

      {/**
       * Charts Grid
       *
       * LEARNING NOTE:
       * We use a responsive grid to arrange charts:
       * - Single column on mobile
       * - Two columns on large screens
       * - Full width for wide charts
       */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Signal Distribution Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Signal Distribution</CardTitle>
            <CardDescription>
              Breakdown of BUY, HOLD, and SELL signals
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SignalDistributionChart signals={signals} />
          </CardContent>
        </Card>

        {/* Score Histogram */}
        <Card>
          <CardHeader>
            <CardTitle>Score Distribution</CardTitle>
            <CardDescription>
              Histogram of signal scores from -1 to +1
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScoreHistogramChart
              signals={signals}
              buyThreshold={0.4}
              sellThreshold={-0.4}
            />
          </CardContent>
        </Card>
      </div>

      {/* Sector Performance - Full Width */}
      <Card>
        <CardHeader>
          <CardTitle>Sector Performance</CardTitle>
          <CardDescription>
            Average signal score by sector (sorted by performance)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SectorPerformanceChart signals={signals} />
        </CardContent>
      </Card>

      {/* Learning callout */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">
          Module 5: Charts and Visualization
        </h3>
        <p className="text-blue-800 text-sm">
          This page demonstrates Recharts integration with Next.js. Key learnings:
        </p>
        <ul className="text-blue-800 text-sm mt-2 space-y-1 list-disc list-inside">
          <li>Charts are Client Components (need browser APIs)</li>
          <li>Server Component fetches data, passes to chart components</li>
          <li>useMemo optimizes data transformation</li>
          <li>ResponsiveContainer enables responsive charts</li>
        </ul>
        <p className="text-blue-700 text-sm mt-2">
          See <code className="bg-blue-100 px-1 rounded">frontend/LEARNING.md#module-5-charts</code> for details.
        </p>
      </div>
    </div>
  );
}
