/**
 * Stock Card Component for Generative UI
 *
 * LEARNING MODULE 7: GENERATIVE UI COMPONENTS
 * -------------------------------------------
 * This component can be rendered by the AI to show stock information.
 *
 * Key concepts:
 * 1. **Generative UI** - AI generates structured data, React renders it
 * 2. **Type-safe props** - Define clear interfaces for AI-generated data
 * 3. **Rich visualization** - Show data with charts, badges, indicators
 *
 * File path: frontend/components/generative-ui/StockCard.tsx
 */

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StockCardProps {
  /** Stock ticker symbol */
  ticker: string;
  /** Company name */
  name?: string;
  /** Current price */
  price?: number;
  /** Price change percentage */
  change?: number;
  /** Trading signal type */
  signal?: "BUY" | "SELL" | "HOLD";
  /** Signal confidence score (0-1) */
  confidence?: number;
  /** RSI value */
  rsi?: number;
  /** Sector name */
  sector?: string;
}

/**
 * A rich stock information card that AI can render
 *
 * LEARNING NOTE:
 * Generative UI works by:
 * 1. AI outputs structured JSON matching this component's props
 * 2. A parser identifies the component type and props
 * 3. React renders the appropriate component
 *
 * This creates a much richer experience than plain text!
 */
export function StockCard({
  ticker,
  name,
  price,
  change,
  signal,
  confidence,
  rsi,
  sector,
}: StockCardProps) {
  const isPositiveChange = change && change > 0;
  const isNegativeChange = change && change < 0;

  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-bold">{ticker}</CardTitle>
          {signal && (
            <span
              className={cn(
                "px-2 py-1 rounded-full text-xs font-semibold",
                signal === "BUY" && "bg-green-100 text-green-700",
                signal === "SELL" && "bg-red-100 text-red-700",
                signal === "HOLD" && "bg-gray-100 text-gray-700"
              )}
            >
              {signal}
            </span>
          )}
        </div>
        {name && <p className="text-sm text-gray-500">{name}</p>}
        {sector && (
          <p className="text-xs text-gray-400">{sector}</p>
        )}
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Price and Change */}
        {price !== undefined && (
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold">৳{price.toFixed(2)}</span>
            {change !== undefined && (
              <span
                className={cn(
                  "text-sm font-medium",
                  isPositiveChange && "text-green-600",
                  isNegativeChange && "text-red-600",
                  !isPositiveChange && !isNegativeChange && "text-gray-500"
                )}
              >
                {isPositiveChange ? "+" : ""}
                {change.toFixed(2)}%
              </span>
            )}
          </div>
        )}

        {/* Indicators */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          {rsi !== undefined && (
            <div className="flex flex-col">
              <span className="text-gray-500">RSI</span>
              <span
                className={cn(
                  "font-medium",
                  rsi > 70 && "text-red-600",
                  rsi < 30 && "text-green-600",
                  rsi >= 30 && rsi <= 70 && "text-gray-700"
                )}
              >
                {rsi.toFixed(1)}
                {rsi > 70 && " (Overbought)"}
                {rsi < 30 && " (Oversold)"}
              </span>
            </div>
          )}

          {confidence !== undefined && (
            <div className="flex flex-col">
              <span className="text-gray-500">Confidence</span>
              <span className="font-medium">
                {(confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>

        {/* Confidence Bar */}
        {confidence !== undefined && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={cn(
                "h-2 rounded-full transition-all",
                signal === "BUY" && "bg-green-500",
                signal === "SELL" && "bg-red-500",
                signal === "HOLD" && "bg-gray-400"
              )}
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
