/**
 * Signal Filter Component
 *
 * LEARNING MODULE 4:
 * -----------------
 * This is a Client Component that provides interactive filtering.
 *
 * Key concepts:
 * 1. **"use client"** - Required for components using hooks/interactivity
 * 2. **useState** - Manages local component state
 * 3. **Controlled inputs** - React controls the input value
 * 4. **Callback props** - Parent passes handlers to children
 *
 * Client vs Server Components:
 * - Server Components: Fetch data, can't use hooks
 * - Client Components: Interactive, use hooks like useState
 *
 * File path: frontend/components/signals/SignalFilter.tsx
 * See: frontend/LEARNING.md#module-4-client-components
 */

"use client";

import { useState } from "react";
import { SignalType } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// Default thresholds matching the backend
export const DEFAULT_BUY_THRESHOLD = 0.4;
export const DEFAULT_SELL_THRESHOLD = -0.4;

interface SignalFilterProps {
  /** Current signal type filter */
  signalType: SignalType;
  /** Callback when signal type changes */
  onSignalTypeChange: (type: SignalType) => void;
  /** Current ticker search value */
  tickerSearch: string;
  /** Callback when ticker search changes */
  onTickerSearchChange: (search: string) => void;
  /** Current buy threshold */
  buyThreshold: number;
  /** Callback when buy threshold changes */
  onBuyThresholdChange: (threshold: number) => void;
  /** Current sell threshold */
  sellThreshold: number;
  /** Callback when sell threshold changes */
  onSellThresholdChange: (threshold: number) => void;
  /** Available sectors for filtering */
  sectors: string[];
  /** Currently selected sectors (multi-select) */
  selectedSectors: string[];
  /** Callback when sectors change */
  onSectorsChange: (sectors: string[]) => void;
  /** Available categories for filtering */
  categories: string[];
  /** Currently selected categories (multi-select) */
  selectedCategories: string[];
  /** Callback when categories change */
  onCategoriesChange: (categories: string[]) => void;
}

/**
 * Multi-select dropdown component
 */
function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
  formatOption,
}: {
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  formatOption?: (option: string) => string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter((s) => s !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  const clearAll = () => {
    onChange([]);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="h-10 min-w-[160px] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center justify-between gap-2"
      >
        <span className="truncate">
          {selected.length === 0
            ? placeholder
            : selected.length === 1
              ? formatOption
                ? formatOption(selected[0])
                : selected[0]
              : `${selected.length} selected`}
        </span>
        <svg
          className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop to close on outside click */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute z-20 mt-1 w-full min-w-[200px] max-h-60 overflow-auto rounded-md border border-gray-200 bg-white shadow-lg">
            {selected.length > 0 && (
              <button
                type="button"
                onClick={clearAll}
                className="w-full px-3 py-2 text-left text-sm text-blue-600 hover:bg-gray-50 border-b border-gray-100"
              >
                Clear all ({selected.length})
              </button>
            )}
            {options.map((option) => (
              <label
                key={option}
                className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(option)}
                  onChange={() => toggleOption(option)}
                  className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">
                  {formatOption ? formatOption(option) : option}
                </span>
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Filter controls for the signals list
 *
 * LEARNING NOTE:
 * This component demonstrates the "lifting state up" pattern.
 * The parent component owns the state, this component just displays
 * controls and calls callbacks when user interacts.
 */
export function SignalFilter({
  signalType,
  onSignalTypeChange,
  tickerSearch,
  onTickerSearchChange,
  buyThreshold,
  onBuyThresholdChange,
  sellThreshold,
  onSellThresholdChange,
  sectors,
  selectedSectors,
  onSectorsChange,
  categories,
  selectedCategories,
  onCategoriesChange,
}: SignalFilterProps) {
  const [showThresholds, setShowThresholds] = useState(false);

  // Signal type options
  const signalTypes: { value: SignalType; label: string }[] = [
    { value: "all", label: "All" },
    { value: "BUY", label: "BUY" },
    { value: "HOLD", label: "HOLD" },
    { value: "SELL", label: "SELL" },
  ];

  const resetThresholds = () => {
    onBuyThresholdChange(DEFAULT_BUY_THRESHOLD);
    onSellThresholdChange(DEFAULT_SELL_THRESHOLD);
  };

  const isDefaultThresholds =
    buyThreshold === DEFAULT_BUY_THRESHOLD &&
    sellThreshold === DEFAULT_SELL_THRESHOLD;

  return (
    <div className="space-y-4 mb-6">
      {/* Main Filter Row */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Ticker Search with Clear Button */}
        <div className="flex-1 relative">
          <Input
            type="text"
            placeholder="Search by ticker (e.g., GP, BATBC)"
            value={tickerSearch}
            onChange={(e) => onTickerSearchChange(e.target.value)}
            className="w-full pr-10"
          />
          {/* Clear button - only show when there's text */}
          {tickerSearch && (
            <button
              type="button"
              onClick={() => onTickerSearchChange("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
              aria-label="Clear search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Sector Filter (Multi-select) */}
        <MultiSelect
          options={sectors}
          selected={selectedSectors}
          onChange={onSectorsChange}
          placeholder="All Sectors"
        />

        {/* Category Filter (Multi-select) */}
        <MultiSelect
          options={categories.filter((c) => c !== "-")}
          selected={selectedCategories}
          onChange={onCategoriesChange}
          placeholder="All Categories"
          formatOption={(cat) => `Category ${cat}`}
        />

        {/* Signal Type Filter Buttons */}
        <div className="flex gap-2">
          {signalTypes.map((type) => (
            <Button
              key={type.value}
              variant={signalType === type.value ? "default" : "outline"}
              size="sm"
              onClick={() => onSignalTypeChange(type.value)}
              className={
                signalType === type.value
                  ? type.value === "BUY"
                    ? "bg-buy hover:bg-buy-dark"
                    : type.value === "SELL"
                      ? "bg-sell hover:bg-sell-dark"
                      : type.value === "HOLD"
                        ? "bg-hold hover:bg-hold-dark"
                        : ""
                  : ""
              }
            >
              {type.label}
            </Button>
          ))}
        </div>

        {/* Settings Toggle */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowThresholds(!showThresholds)}
          className={showThresholds ? "bg-gray-100" : ""}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4 mr-1"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
              clipRule="evenodd"
            />
          </svg>
          Thresholds
        </Button>
      </div>

      {/* Threshold Controls - Collapsible */}
      {showThresholds && (
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">
              Signal Thresholds
            </h3>
            {!isDefaultThresholds && (
              <Button variant="outline" size="sm" onClick={resetThresholds}>
                Reset to Default
              </Button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Buy Threshold */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                BUY Threshold (score &ge;)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="-1"
                  max="1"
                  step="0.1"
                  value={buyThreshold}
                  onChange={(e) =>
                    onBuyThresholdChange(parseFloat(e.target.value))
                  }
                  className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-buy"
                />
                <span className="w-12 text-sm font-medium text-buy-dark text-right">
                  {buyThreshold.toFixed(1)}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Lower = more BUY signals (default: {DEFAULT_BUY_THRESHOLD})
              </p>
            </div>

            {/* Sell Threshold */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">
                SELL Threshold (score &le;)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="-1"
                  max="1"
                  step="0.1"
                  value={sellThreshold}
                  onChange={(e) =>
                    onSellThresholdChange(parseFloat(e.target.value))
                  }
                  className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-sell"
                />
                <span className="w-12 text-sm font-medium text-sell-dark text-right">
                  {sellThreshold.toFixed(1)}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Higher = more SELL signals (default: {DEFAULT_SELL_THRESHOLD})
              </p>
            </div>
          </div>

          <p className="text-xs text-gray-500 mt-3 p-2 bg-white rounded border">
            <strong>Note:</strong> These thresholds filter the displayed signals
            client-side. To regenerate signals with different thresholds, use
            the CLI:{" "}
            <code className="bg-gray-100 px-1 rounded">
              quant-flow scan --buy-threshold {buyThreshold} --sell-threshold{" "}
              {sellThreshold}
            </code>
          </p>
        </div>
      )}
    </div>
  );
}
