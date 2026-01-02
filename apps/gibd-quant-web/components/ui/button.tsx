import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Button Component - Reusable button with variants
 *
 * LEARNING MODULE 2:
 * -----------------
 * This is a reusable component pattern common in React:
 * 1. Define TypeScript interface for props
 * 2. Use `cn()` to merge default and custom classes
 * 3. Spread `...props` to pass through HTML attributes
 *
 * Key concepts:
 * - `React.ButtonHTMLAttributes<HTMLButtonElement>` gives us all native button props
 * - `variant` prop controls the visual style
 * - `size` prop controls the size
 *
 * File path: frontend/components/ui/button.tsx
 * See: frontend/LEARNING.md#module-2-button-component
 */

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "buy" | "sell";
  size?: "sm" | "md" | "lg";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    return (
      <button
        className={cn(
          // Base styles
          "inline-flex items-center justify-center rounded-md font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",

          // Variant styles
          {
            // Default - gray/neutral
            default:
              "bg-gray-900 text-white hover:bg-gray-800 focus-visible:ring-gray-900",
            // Outline - bordered
            outline:
              "border border-gray-300 bg-white text-gray-900 hover:bg-gray-50",
            // Ghost - transparent
            ghost: "text-gray-900 hover:bg-gray-100",
            // Buy - green
            buy: "bg-buy text-white hover:bg-buy-dark focus-visible:ring-buy",
            // Sell - red
            sell: "bg-sell text-white hover:bg-sell-dark focus-visible:ring-sell",
          }[variant],

          // Size styles
          {
            sm: "h-8 px-3 text-sm",
            md: "h-10 px-4",
            lg: "h-12 px-6 text-lg",
          }[size],

          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";

export { Button, type ButtonProps };
