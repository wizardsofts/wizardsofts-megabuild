/**
 * useDebounce Hook
 *
 * LEARNING MODULE 4:
 * -----------------
 * A custom React hook that delays updating a value until a specified time
 * has passed since the last change.
 *
 * Why use debounce?
 * - Prevents excessive API calls while user is typing
 * - Improves performance by reducing unnecessary re-renders
 * - Common pattern for search inputs
 *
 * How it works:
 * 1. User types "A" -> timer starts (300ms)
 * 2. User types "B" (within 300ms) -> timer resets
 * 3. User stops typing -> after 300ms, value updates to "AB"
 *
 * File path: frontend/hooks/useDebounce.ts
 * See: frontend/LEARNING.md#module-4-debounce
 */

"use client";

import { useState, useEffect } from "react";

/**
 * Debounce a value by a specified delay
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default 300ms)
 * @returns The debounced value
 *
 * @example
 * const [search, setSearch] = useState("");
 * const debouncedSearch = useDebounce(search, 300);
 *
 * // Effect only runs when user stops typing for 300ms
 * useEffect(() => {
 *   fetchResults(debouncedSearch);
 * }, [debouncedSearch]);
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up a timer to update the debounced value
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Clean up: cancel the timer if value changes before delay completes
    // This is the key to debouncing - each new value cancels the previous timer
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
