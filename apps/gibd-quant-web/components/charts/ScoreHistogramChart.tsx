/**
 * Score Histogram Chart Component
 *
 * LEARNING MODULE 5: CHARTS AND VISUALIZATION
 * -------------------------------------------
 * This component displays a bar chart showing the distribution of signal scores.
 *
 * Key concepts:
 * 1. **BarChart** - For categorical/bucketed data
 * 2. **Data binning** - Grouping continuous values into buckets
 * 3. **XAxis/YAxis** - Configuring chart axes
 * 4. **ReferenceLine** - Adding threshold indicators
 *
 * Chart types in Recharts:
 * - PieChart: Part-to-whole relationships
 * - BarChart: Comparing categories or showing distributions
 * - LineChart: Trends over time
 * - AreaChart: Cumulative data or ranges
 * - ScatterChart: Correlation between two variables
 *
 * File path: frontend/components/charts/ScoreHistogramChart.tsx
 */

"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import { Signal } from "@/lib/api";

interface ScoreHistogramChartProps {
  /** Array of signals to visualize */
  signals: Signal[];
  /** Buy threshold line */
  buyThreshold?: number;
  /** Sell threshold line */
  sellThreshold?: number;
}

/**
 * Creates histogram buckets from -1 to 1 in 0.2 increments
 */
function createBuckets(): { min: number; max: number; label: string }[] {
  const buckets = [];
  for (let i = -1; i < 1; i += 0.2) {
    buckets.push({
      min: Math.round(i * 10) / 10, // Fix floating point
      max: Math.round((i + 0.2) * 10) / 10,
      label: `${i.toFixed(1)}`,
    });
  }
  return buckets;
}

/**
 * Get color for a bucket based on its score range
 */
function getBucketColor(min: number, buyThreshold: number, sellThreshold: number): string {
  if (min >= buyThreshold) return "#22c55e"; // green
  if (min + 0.2 <= sellThreshold) return "#ef4444"; // red
  return "#f59e0b"; // amber
}

/**
 * Displays a histogram of signal scores
 *
 * LEARNING NOTE:
 * Histograms are great for seeing:
 * - How data is distributed
 * - Where most values cluster
 * - Outliers or unusual patterns
 */
export function ScoreHistogramChart({
  signals,
  buyThreshold = 0.4,
  sellThreshold = -0.4,
}: ScoreHistogramChartProps) {
  /**
   * Bin the signals into histogram buckets
   *
   * LEARNING NOTE:
   * Data binning groups continuous values into discrete buckets.
   * This is essential for histograms - you count how many values
   * fall into each bucket rather than plotting individual points.
   */
  const chartData = useMemo(() => {
    const buckets = createBuckets();

    // Initialize counts
    const data = buckets.map((bucket) => ({
      ...bucket,
      count: 0,
      color: getBucketColor(bucket.min, buyThreshold, sellThreshold),
    }));

    // Count signals in each bucket
    signals.forEach((signal) => {
      const score = signal.total_score;
      if (score === undefined || score === null) return;

      // Find the right bucket
      const bucketIndex = data.findIndex(
        (b) => score >= b.min && score < b.max
      );

      // Handle edge case: score === 1.0 goes in last bucket
      if (bucketIndex >= 0) {
        data[bucketIndex].count++;
      } else if (score >= 0.8) {
        data[data.length - 1].count++;
      }
    });

    return data;
  }, [signals, buyThreshold, sellThreshold]);

  // Calculate max count for Y axis
  const maxCount = Math.max(...chartData.map((d) => d.count), 1);

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        {/**
         * BarChart composition:
         * - CartesianGrid: Background grid lines
         * - XAxis: Horizontal axis (score buckets)
         * - YAxis: Vertical axis (counts)
         * - Bar: The actual bars
         * - ReferenceLine: Threshold indicators
         */}
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
        >
          {/**
           * CartesianGrid adds background lines
           * strokeDasharray creates dashed lines
           */}
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          {/**
           * XAxis configuration:
           * - dataKey: Which property to use for labels
           * - tick: Style for tick labels
           * - interval: Show every label (0) or skip some
           */}
          <XAxis
            dataKey="label"
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: "#9ca3af" }}
            axisLine={{ stroke: "#9ca3af" }}
          />

          {/**
           * YAxis configuration:
           * - domain: Min and max values [0, auto]
           * - allowDecimals: Only show whole numbers
           */}
          <YAxis
            domain={[0, Math.ceil(maxCount * 1.1)]}
            allowDecimals={false}
            tick={{ fontSize: 12 }}
            tickLine={{ stroke: "#9ca3af" }}
            axisLine={{ stroke: "#9ca3af" }}
            label={{
              value: "Count",
              angle: -90,
              position: "insideLeft",
              style: { fontSize: 12, fill: "#6b7280" },
            }}
          />

          {/**
           * Tooltip shows details on hover
           */}
          <Tooltip
            formatter={(value) => [`${value} signals`, "Count"]}
            labelFormatter={(label) => `Score: ${label} to ${(parseFloat(label) + 0.2).toFixed(1)}`}
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "0.375rem",
              padding: "0.5rem",
            }}
          />

          {/**
           * Bar with individual Cell colors
           *
           * LEARNING NOTE:
           * Using Cell components inside Bar lets us color
           * each bar differently based on its data.
           */}
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>

          {/**
           * ReferenceLine adds threshold indicators
           *
           * LEARNING NOTE:
           * Reference lines are great for showing:
           * - Thresholds or targets
           * - Averages or baselines
           * - Important values to compare against
           *
           * We position these by finding which bucket index
           * corresponds to the threshold value.
           */}
          <ReferenceLine
            x={buyThreshold.toFixed(1)}
            stroke="#22c55e"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: "BUY",
              position: "top",
              fill: "#22c55e",
              fontSize: 11,
            }}
          />
          <ReferenceLine
            x={sellThreshold.toFixed(1)}
            stroke="#ef4444"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{
              value: "SELL",
              position: "top",
              fill: "#ef4444",
              fontSize: 11,
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
