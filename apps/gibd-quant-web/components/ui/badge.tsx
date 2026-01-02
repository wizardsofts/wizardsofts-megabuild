import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Badge Component - Small status indicators
 *
 * LEARNING MODULE 2:
 * -----------------
 * Badges are small labels for status or categories.
 * For Quant-Flow, we use them for:
 * - Signal types (BUY, SELL, HOLD)
 * - Stock tickers
 * - Confidence levels
 *
 * The `signal` variant automatically colors based on signal type.
 *
 * Usage:
 * ```tsx
 * <Badge>Default</Badge>
 * <Badge variant="buy">BUY</Badge>
 * <Badge variant="sell">SELL</Badge>
 * <Badge variant="hold">HOLD</Badge>
 * <Badge variant="outline">GP</Badge>
 * ```
 *
 * File path: frontend/components/ui/badge.tsx
 * See: frontend/LEARNING.md#module-2-badge-component
 */

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "outline" | "buy" | "sell" | "hold";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        // Base styles
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-offset-2",

        // Variant styles
        {
          default: "bg-gray-100 text-gray-900",
          outline: "border border-gray-300 text-gray-900",
          buy: "bg-buy-light text-buy-dark border border-buy",
          sell: "bg-sell-light text-sell-dark border border-sell",
          hold: "bg-hold-light text-hold-dark border border-hold",
        }[variant],

        className
      )}
      {...props}
    />
  );
}

/**
 * SignalBadge - Automatically styled based on signal type
 *
 * Usage:
 * ```tsx
 * <SignalBadge type="BUY" />
 * <SignalBadge type="SELL" />
 * <SignalBadge type="HOLD" />
 * ```
 */
interface SignalBadgeProps extends Omit<BadgeProps, "variant"> {
  type: "BUY" | "SELL" | "HOLD";
}

function SignalBadge({ type, className, ...props }: SignalBadgeProps) {
  const variant = type.toLowerCase() as "buy" | "sell" | "hold";

  return (
    <Badge variant={variant} className={className} {...props}>
      {type}
    </Badge>
  );
}

export { Badge, SignalBadge, type BadgeProps, type SignalBadgeProps };
