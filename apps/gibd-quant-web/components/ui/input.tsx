import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Input Component - Text input field
 *
 * LEARNING MODULE 2:
 * -----------------
 * A basic input component that extends the native HTML input.
 * Used for search boxes, forms, and chat input.
 *
 * Features:
 * - Consistent styling with Tailwind
 * - Focus ring for accessibility
 * - Disabled state styling
 *
 * Usage:
 * ```tsx
 * <Input placeholder="Search stocks..." />
 * <Input type="number" min={0} max={100} />
 * ```
 *
 * File path: frontend/components/ui/input.tsx
 * See: frontend/LEARNING.md#module-2-input-component
 */

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2",
          "text-sm text-gray-900 placeholder:text-gray-400",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-900 focus-visible:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";

export { Input };
