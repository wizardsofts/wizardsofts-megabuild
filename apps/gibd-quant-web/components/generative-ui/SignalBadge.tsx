/**
 * Signal Badge Component for Generative UI
 *
 * LEARNING MODULE 7: GENERATIVE UI COMPONENTS
 * -------------------------------------------
 * A simple badge to display trading signals inline.
 *
 * Key concepts:
 * 1. **Inline components** - Small, inline UI for embedding in text
 * 2. **Semantic colors** - Use color to convey meaning instantly
 *
 * File path: frontend/components/generative-ui/SignalBadge.tsx
 */

"use client";

import { cn } from "@/lib/utils";

interface SignalBadgeProps {
  /** The signal type */
  type: "BUY" | "SELL" | "HOLD";
  /** Optional score to display */
  score?: number;
  /** Size variant */
  size?: "sm" | "md" | "lg";
}

/**
 * Inline badge for displaying signal types
 *
 * LEARNING NOTE:
 * This is a "micro" generative UI component.
 * AI can render these inline within text responses:
 *
 * "Based on the analysis, GP shows a <SignalBadge type='BUY' score={0.75} />"
 */
export function SignalBadge({ type, score, size = "md" }: SignalBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-semibold",
        // Size variants
        size === "sm" && "px-2 py-0.5 text-xs",
        size === "md" && "px-2.5 py-1 text-sm",
        size === "lg" && "px-3 py-1.5 text-base",
        // Color variants based on signal type
        type === "BUY" && "bg-green-100 text-green-700 border border-green-200",
        type === "SELL" && "bg-red-100 text-red-700 border border-red-200",
        type === "HOLD" && "bg-gray-100 text-gray-700 border border-gray-200"
      )}
    >
      {/* Signal icon */}
      {type === "BUY" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
            clipRule="evenodd"
          />
        </svg>
      )}
      {type === "SELL" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z"
            clipRule="evenodd"
          />
        </svg>
      )}
      {type === "HOLD" && (
        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
            clipRule="evenodd"
          />
        </svg>
      )}

      {/* Signal text */}
      <span>{type}</span>

      {/* Optional score */}
      {score !== undefined && (
        <span className="opacity-75">({(score * 100).toFixed(0)}%)</span>
      )}
    </span>
  );
}
