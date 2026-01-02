/**
 * Signal Card Component
 *
 * LEARNING MODULE 4:
 * -----------------
 * A reusable component that displays a single trading signal.
 *
 * Key concepts:
 * 1. **Props interface** - TypeScript defines what props are expected
 * 2. **Composition** - Uses Card, Badge components we created
 * 3. **Conditional rendering** - Shows optional fields only if present
 *
 * File path: frontend/components/signals/SignalCard.tsx
 * See: frontend/LEARNING.md#module-4-component-composition
 */

import Link from 'next/link';
import { Signal } from "@/lib/api";
import { SignalBadge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatCurrency, formatDate, formatPercent } from "@/lib/utils";

interface SignalCardProps {
  signal: Signal;
}

/**
 * Helper function to safely get confidence as a number
 */
function getConfidenceValue(confidence: number | string): number {
  return typeof confidence === "string" ? parseFloat(confidence) : confidence;
}

export function SignalCard({ signal }: SignalCardProps) {
  const confidenceValue = getConfidenceValue(signal.confidence);
  const confidencePercent = confidenceValue * 100;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          {/* Ticker Symbol - Bold and prominent, clickable link to company page */}
          <CardTitle className="text-2xl font-bold">
            <Link
              href={`/company/${signal.ticker}`}
              className="text-gray-900 hover:text-blue-600 hover:underline transition-colors"
            >
              {signal.ticker || "N/A"}
            </Link>
          </CardTitle>
          {/* Signal Type Badge */}
          <SignalBadge type={signal.signal_type} />
        </div>
        <CardDescription>
          <span>{signal.signal_date ? formatDate(signal.signal_date) : 'N/A'}</span>
          {signal.sector && (
            <span className="ml-2 text-xs px-1.5 py-0.5 bg-gray-100 rounded">
              {signal.sector}
            </span>
          )}
          {signal.category && (
            <span className="ml-1 text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">
              {signal.category}
            </span>
          )}
        </CardDescription>
      </CardHeader>

      <CardContent>
        {/* Confidence Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Confidence</span>
            <span className="font-medium">{formatPercent(confidencePercent)}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${
                signal.signal_type === "BUY"
                  ? "bg-buy"
                  : signal.signal_type === "SELL"
                    ? "bg-sell"
                    : "bg-hold"
              }`}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        {/* Price Info */}
        <div className="space-y-2 text-sm">
          {/* Entry Price - Always show prominently */}
          <div className="flex justify-between">
            <span className="text-gray-600">Entry Price</span>
            <span className="font-semibold text-gray-900">
              {signal.entry_price ? formatCurrency(signal.entry_price) : "N/A"}
            </span>
          </div>

          {/* Target Price - Hide if same as entry */}
          {signal.target_price != null && signal.target_price !== signal.entry_price && (
            <div className="flex justify-between">
              <span className="text-gray-600">Target</span>
              <span className="text-buy-dark font-medium">
                {formatCurrency(signal.target_price)}
              </span>
            </div>
          )}

          {/* Stop Loss - Hide if same as entry */}
          {signal.stop_loss != null && signal.stop_loss !== signal.entry_price && (
            <div className="flex justify-between">
              <span className="text-gray-600">Stop Loss</span>
              <span className="text-sell-dark font-medium">
                {formatCurrency(signal.stop_loss)}
              </span>
            </div>
          )}

          {/* Risk/Reward Ratio */}
          {signal.risk_reward_ratio != null && signal.risk_reward_ratio > 0 && (
            <div className="flex justify-between">
              <span className="text-gray-600">Risk/Reward</span>
              <span className="font-medium">1:{signal.risk_reward_ratio.toFixed(2)}</span>
            </div>
          )}
        </div>

        {/* Outcome (if closed) */}
        {signal.outcome_result && (
          <div className="mt-4 pt-3 border-t">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Outcome</span>
              <span
                className={`text-sm font-medium ${
                  signal.return_pct && signal.return_pct > 0
                    ? "text-buy-dark"
                    : "text-sell-dark"
                }`}
              >
                {signal.outcome_result.replace("_", " ")}
                {signal.return_pct != null && <> ({formatPercent(signal.return_pct)})</>}
              </span>
            </div>
          </div>
        )}

        {/* Warnings */}
        {signal.warnings && signal.warnings.length > 0 && (
          <div className="mt-4 pt-3 border-t">
            <div className="text-xs text-amber-600">{signal.warnings[0]}</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
