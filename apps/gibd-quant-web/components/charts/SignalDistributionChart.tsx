/**
 * Signal Distribution Chart Component
 *
 * LEARNING MODULE 5: CHARTS AND VISUALIZATION
 * -------------------------------------------
 * This module teaches you how to create interactive charts in React.
 *
 * Key concepts:
 * 1. **Recharts** - A composable charting library built on React components
 * 2. **"use client"** - Charts need browser APIs, must be client components
 * 3. **ResponsiveContainer** - Makes charts resize with their parent
 * 4. **useMemo** - Compute chart data efficiently from props
 *
 * Why Recharts?
 * - Built specifically for React (uses React components)
 * - Declarative API (describe what you want, not how to draw)
 * - Highly customizable with good defaults
 * - Great TypeScript support
 *
 * File path: frontend/components/charts/SignalDistributionChart.tsx
 * See: frontend/LEARNING.md#module-5-charts
 */

"use client";

import { useMemo } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { Signal } from "@/lib/api";

interface SignalDistributionChartProps {
  /** Array of signals to visualize */
  signals: Signal[];
}

/**
 * Color palette for signal types
 * Using CSS custom properties would be ideal, but Recharts needs hex/rgb values
 */
const COLORS = {
  BUY: "#22c55e",   // green-500
  SELL: "#ef4444",  // red-500
  HOLD: "#f59e0b",  // amber-500
};

/**
 * Displays a pie chart showing the distribution of BUY, SELL, HOLD signals
 *
 * LEARNING NOTE:
 * The chart components are composed declaratively:
 * - PieChart: Container for pie charts
 * - Pie: The actual pie, with data and styling
 * - Cell: Individual slices (we map over data to color each)
 * - Legend: Shows what each color means
 * - Tooltip: Shows details on hover
 */
export function SignalDistributionChart({
  signals,
}: SignalDistributionChartProps) {
  /**
   * Transform signals array into chart data format
   *
   * LEARNING NOTE:
   * useMemo ensures we only recalculate when signals change.
   * This is important for charts because:
   * 1. Counting operations on large arrays are expensive
   * 2. New data arrays would cause unnecessary re-renders
   */
  const chartData = useMemo(() => {
    const counts = {
      BUY: 0,
      SELL: 0,
      HOLD: 0,
    };

    signals.forEach((signal) => {
      if (signal.signal_type in counts) {
        counts[signal.signal_type as keyof typeof counts]++;
      }
    });

    // Convert to array format that Recharts expects
    return [
      { name: "BUY", value: counts.BUY, color: COLORS.BUY },
      { name: "HOLD", value: counts.HOLD, color: COLORS.HOLD },
      { name: "SELL", value: counts.SELL, color: COLORS.SELL },
    ].filter((item) => item.value > 0); // Remove zero-value slices
  }, [signals]);

  // Don't render if no data
  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        No signals to display
      </div>
    );
  }

  return (
    <div className="h-64">
      {/**
       * ResponsiveContainer makes the chart fill its parent
       * The width="100%" and height="100%" make it responsive
       *
       * LEARNING NOTE:
       * Always wrap charts in ResponsiveContainer for responsive behavior.
       * It uses ResizeObserver internally to detect size changes.
       */}
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          {/**
           * Pie component configuration:
           * - data: Array of {name, value} objects
           * - cx/cy: Center position (50% = centered)
           * - innerRadius: Makes it a donut chart (0 = full pie)
           * - outerRadius: Size of the pie
           * - dataKey: Which property contains the numeric value
           * - label: Show percentage labels on slices
           */}
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={40}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
            label={({ name, percent }) =>
              `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
            }
            labelLine={true}
          >
            {/**
             * Map over data to color each slice
             *
             * LEARNING NOTE:
             * Cell components let you customize individual slices.
             * We use the index to get the corresponding color from our data.
             */}
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color}
                stroke={entry.color}
                strokeWidth={1}
              />
            ))}
          </Pie>

          {/**
           * Tooltip shows details on hover
           * formatter customizes what's displayed
           */}
          <Tooltip
            formatter={(value, name) => [
              `${value} signals`,
              String(name),
            ]}
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "0.375rem",
              padding: "0.5rem",
            }}
          />

          {/**
           * Legend shows what each color means
           * verticalAlign and align position it
           */}
          <Legend
            verticalAlign="bottom"
            align="center"
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
