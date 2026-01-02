/**
 * Signals List Component for Generative UI
 *
 * LEARNING MODULE 7: GENERATIVE UI COMPONENTS
 * -------------------------------------------
 * Displays a list of trading signals in a compact format.
 *
 * Key concepts:
 * 1. **List rendering** - Show multiple items from AI response
 * 2. **Sorting/filtering** - Pre-process data for display
 * 3. **Compact design** - Fit more info in less space
 *
 * File path: frontend/components/generative-ui/SignalsList.tsx
 */

"use client";

import { cn } from "@/lib/utils";

interface SignalItem {
  ticker: string;
  signal: "BUY" | "SELL" | "HOLD";
  score: number;
  sector?: string;
}

interface SignalsListProps {
  /** List of signals to display */
  signals: SignalItem[];
  /** Title for the list */
  title?: string;
  /** Maximum items to show */
  limit?: number;
}

/**
 * Compact list of trading signals
 *
 * LEARNING NOTE:
 * This is useful when AI wants to show multiple stocks at once.
 * For example, in response to "Show me top BUY signals":
 *
 * <SignalsList
 *   title="Top BUY Signals"
 *   signals={[
 *     { ticker: "GP", signal: "BUY", score: 0.85 },
 *     { ticker: "BATBC", signal: "BUY", score: 0.78 },
 *   ]}
 * />
 */
export function SignalsList({
  signals,
  title,
  limit = 10,
}: SignalsListProps) {
  // Sort by absolute score and limit
  const sortedSignals = [...signals]
    .sort((a, b) => Math.abs(b.score) - Math.abs(a.score))
    .slice(0, limit);

  return (
    <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Header */}
      {title && (
        <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </div>
      )}

      {/* Signal list */}
      <ul className="divide-y divide-gray-100">
        {sortedSignals.map((item, index) => (
          <li
            key={`${item.ticker}-${index}`}
            className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              {/* Rank badge */}
              <span className="w-6 h-6 flex items-center justify-center bg-gray-100 rounded-full text-xs font-medium text-gray-500">
                {index + 1}
              </span>

              {/* Ticker and sector */}
              <div>
                <span className="font-medium text-gray-900">{item.ticker}</span>
                {item.sector && (
                  <span className="ml-2 text-xs text-gray-400">
                    {item.sector}
                  </span>
                )}
              </div>
            </div>

            {/* Signal and score */}
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "px-2 py-0.5 rounded text-xs font-semibold",
                  item.signal === "BUY" && "bg-green-100 text-green-700",
                  item.signal === "SELL" && "bg-red-100 text-red-700",
                  item.signal === "HOLD" && "bg-gray-100 text-gray-700"
                )}
              >
                {item.signal}
              </span>
              <span
                className={cn(
                  "text-sm font-medium",
                  item.score > 0 && "text-green-600",
                  item.score < 0 && "text-red-600",
                  item.score === 0 && "text-gray-500"
                )}
              >
                {item.score > 0 ? "+" : ""}
                {(item.score * 100).toFixed(0)}%
              </span>
            </div>
          </li>
        ))}
      </ul>

      {/* Footer - show if truncated */}
      {signals.length > limit && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-center">
          <span className="text-xs text-gray-500">
            Showing {limit} of {signals.length} signals
          </span>
        </div>
      )}
    </div>
  );
}
