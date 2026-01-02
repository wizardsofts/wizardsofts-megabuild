/**
 * Indicator Display Component for Generative UI
 *
 * LEARNING MODULE 7: GENERATIVE UI COMPONENTS
 * -------------------------------------------
 * Displays technical indicators with visual interpretation.
 *
 * Key concepts:
 * 1. **Data visualization** - Show numbers with visual context
 * 2. **Threshold indicators** - Color zones show meaning
 * 3. **Tooltips/labels** - Add explanatory text
 *
 * File path: frontend/components/generative-ui/IndicatorDisplay.tsx
 */

"use client";

import { cn } from "@/lib/utils";

interface IndicatorDisplayProps {
  /** Indicator name (RSI, MACD, ADX, etc.) */
  name: string;
  /** Current value */
  value: number;
  /** Minimum possible value (for scale) */
  min?: number;
  /** Maximum possible value (for scale) */
  max?: number;
  /** Description or interpretation */
  description?: string;
  /** Warning threshold (shows yellow) */
  warningThreshold?: number;
  /** Danger threshold (shows red) */
  dangerThreshold?: number;
  /** Whether higher values are "good" or "bad" */
  higherIsBetter?: boolean;
}

/**
 * Visual display for technical indicators
 *
 * LEARNING NOTE:
 * This component takes raw indicator data and presents it
 * with visual context. AI can use this to explain indicators:
 *
 * "The RSI for GP is currently:"
 * <IndicatorDisplay name="RSI" value={72} max={100} description="Overbought territory" />
 */
export function IndicatorDisplay({
  name,
  value,
  min = 0,
  max = 100,
  description,
  warningThreshold,
  dangerThreshold,
  higherIsBetter = true,
}: IndicatorDisplayProps) {
  // Calculate percentage for progress bar
  const percentage = ((value - min) / (max - min)) * 100;

  // Determine status color
  const getStatusColor = () => {
    if (dangerThreshold !== undefined) {
      const inDanger = higherIsBetter
        ? value <= dangerThreshold
        : value >= dangerThreshold;
      if (inDanger) return "red";
    }
    if (warningThreshold !== undefined) {
      const inWarning = higherIsBetter
        ? value <= warningThreshold
        : value >= warningThreshold;
      if (inWarning) return "yellow";
    }
    return "green";
  };

  const statusColor = getStatusColor();

  return (
    <div className="w-full max-w-xs p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-600">{name}</span>
        <span
          className={cn(
            "text-lg font-bold",
            statusColor === "green" && "text-green-600",
            statusColor === "yellow" && "text-yellow-600",
            statusColor === "red" && "text-red-600"
          )}
        >
          {value.toFixed(2)}
        </span>
      </div>

      {/* Progress bar with zones */}
      <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
        {/* Danger zone (if applicable) */}
        {dangerThreshold !== undefined && (
          <div
            className="absolute h-full bg-red-200"
            style={{
              left: higherIsBetter ? "0%" : `${((dangerThreshold - min) / (max - min)) * 100}%`,
              width: higherIsBetter
                ? `${((dangerThreshold - min) / (max - min)) * 100}%`
                : `${((max - dangerThreshold) / (max - min)) * 100}%`,
            }}
          />
        )}

        {/* Warning zone (if applicable) */}
        {warningThreshold !== undefined && (
          <div
            className="absolute h-full bg-yellow-200"
            style={{
              left: higherIsBetter
                ? `${((dangerThreshold || min - min) / (max - min)) * 100}%`
                : `${((warningThreshold - min) / (max - min)) * 100}%`,
              width: higherIsBetter
                ? `${(((warningThreshold - (dangerThreshold || min)) / (max - min)) * 100)}%`
                : `${(((dangerThreshold || max) - warningThreshold) / (max - min)) * 100}%`,
            }}
          />
        )}

        {/* Good zone - remaining area */}
        <div
          className="absolute h-full bg-green-200"
          style={{
            left: higherIsBetter
              ? `${((warningThreshold || dangerThreshold || min - min) / (max - min)) * 100}%`
              : "0%",
            right: higherIsBetter
              ? "0%"
              : `${((100 - ((warningThreshold || dangerThreshold || max) - min) / (max - min)) * 100)}%`,
          }}
        />

        {/* Value indicator */}
        <div
          className={cn(
            "absolute h-full w-1 rounded-full",
            statusColor === "green" && "bg-green-600",
            statusColor === "yellow" && "bg-yellow-600",
            statusColor === "red" && "bg-red-600"
          )}
          style={{ left: `${Math.min(Math.max(percentage, 0), 100)}%` }}
        />
      </div>

      {/* Scale labels */}
      <div className="flex justify-between mt-1 text-xs text-gray-400">
        <span>{min}</span>
        <span>{max}</span>
      </div>

      {/* Description */}
      {description && (
        <p className="mt-2 text-xs text-gray-500 italic">{description}</p>
      )}
    </div>
  );
}
