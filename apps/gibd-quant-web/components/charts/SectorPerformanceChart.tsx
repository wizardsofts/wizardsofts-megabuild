/**
 * Sector Performance Chart Component
 *
 * LEARNING MODULE 5: CHARTS AND VISUALIZATION
 * -------------------------------------------
 * This component displays a horizontal bar chart comparing sectors.
 *
 * Key concepts:
 * 1. **Horizontal BarChart** - Using layout="vertical"
 * 2. **Data aggregation** - Computing averages per sector
 * 3. **Sorting** - Ordering bars by value
 * 4. **Dynamic height** - Adjusting chart height based on data
 *
 * When to use horizontal bars:
 * - Long category labels (sector names)
 * - Many categories (easier to read)
 * - Ranking comparisons
 *
 * File path: frontend/components/charts/SectorPerformanceChart.tsx
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
  Cell,
  ReferenceLine,
} from "recharts";
import { Signal } from "@/lib/api";

interface SectorPerformanceChartProps {
  /** Array of signals to visualize */
  signals: Signal[];
}

interface SectorData {
  sector: string;
  avgScore: number;
  count: number;
  color: string;
}

/**
 * Get color based on average score
 */
function getScoreColor(score: number): string {
  if (score >= 0.2) return "#22c55e"; // Strong positive
  if (score >= 0) return "#86efac"; // Weak positive
  if (score >= -0.2) return "#fca5a5"; // Weak negative
  return "#ef4444"; // Strong negative
}

/**
 * Displays sector performance as horizontal bars
 *
 * LEARNING NOTE:
 * Horizontal bar charts are ideal when:
 * 1. Labels are long (like sector names)
 * 2. You have many categories
 * 3. You want to emphasize ranking
 */
export function SectorPerformanceChart({
  signals,
}: SectorPerformanceChartProps) {
  /**
   * Aggregate signals by sector
   *
   * LEARNING NOTE:
   * We use a Map to efficiently group and aggregate data:
   * 1. Loop through signals once
   * 2. Accumulate totals and counts per sector
   * 3. Compute averages at the end
   */
  const chartData = useMemo(() => {
    const sectorMap = new Map<string, { total: number; count: number }>();

    signals.forEach((signal) => {
      const sector = signal.sector || "Unknown";
      const score = signal.total_score;

      if (score === undefined || score === null) return;

      const existing = sectorMap.get(sector) || { total: 0, count: 0 };
      sectorMap.set(sector, {
        total: existing.total + score,
        count: existing.count + 1,
      });
    });

    // Convert to array and compute averages
    const data: SectorData[] = Array.from(sectorMap.entries())
      .map(([sector, { total, count }]) => {
        const avgScore = total / count;
        return {
          sector,
          avgScore: Math.round(avgScore * 100) / 100, // Round to 2 decimals
          count,
          color: getScoreColor(avgScore),
        };
      })
      // Sort by average score descending
      .sort((a, b) => b.avgScore - a.avgScore);

    return data;
  }, [signals]);

  // No data case
  if (chartData.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        No sector data available
      </div>
    );
  }

  /**
   * Dynamic height based on number of sectors
   *
   * LEARNING NOTE:
   * For horizontal bar charts, you often want the height
   * to grow with the number of bars. This ensures each
   * bar has enough space to be readable.
   */
  const chartHeight = Math.max(300, chartData.length * 35);

  return (
    <div style={{ height: chartHeight }}>
      <ResponsiveContainer width="100%" height="100%">
        {/**
         * BarChart with layout="vertical" for horizontal bars
         *
         * LEARNING NOTE:
         * The layout="vertical" prop swaps the axes:
         * - XAxis becomes the value axis (horizontal)
         * - YAxis becomes the category axis (vertical)
         */}
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={true} vertical={false} />

          {/**
           * For vertical layout:
           * - XAxis is the value axis (scores)
           * - YAxis is the category axis (sectors)
           */}
          <XAxis
            type="number"
            domain={[-1, 1]}
            ticks={[-1, -0.5, 0, 0.5, 1]}
            tick={{ fontSize: 11 }}
            tickFormatter={(value) => value.toFixed(1)}
            axisLine={{ stroke: "#9ca3af" }}
          />

          <YAxis
            type="category"
            dataKey="sector"
            width={90}
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "#9ca3af" }}
          />

          {/**
           * Custom tooltip with sector details
           */}
          <Tooltip
            formatter={(value, _name, props) => {
              const payload = props?.payload as SectorData | undefined;
              const numValue = typeof value === "number" ? value : 0;
              return [
                `Avg Score: ${numValue.toFixed(2)} (${payload?.count ?? 0} stocks)`,
                payload?.sector ?? "",
              ];
            }}
            contentStyle={{
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "0.375rem",
              padding: "0.5rem",
            }}
          />

          {/**
           * Zero reference line
           *
           * LEARNING NOTE:
           * A vertical reference line at 0 helps readers
           * quickly see which sectors are positive vs negative.
           */}
          <ReferenceLine
            x={0}
            stroke="#374151"
            strokeWidth={1}
          />

          {/**
           * Bars with individual colors
           */}
          <Bar dataKey="avgScore" radius={[0, 4, 4, 0]} barSize={20}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
