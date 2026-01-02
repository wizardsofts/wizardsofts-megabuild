/**
 * Signals List Component (Client Component)
 *
 * LEARNING MODULE 4:
 * -----------------
 * This is the main interactive component for the signals page.
 * It combines Server Component data with Client Component interactivity.
 *
 * Key concepts:
 * 1. **Hybrid rendering** - Server fetches data, client handles interaction
 * 2. **useState** - Manages filter state locally
 * 3. **useMemo** - Optimizes filtering by caching results
 * 4. **useDebounce** - Prevents excessive filtering while typing
 *
 * Data flow:
 * 1. Server Component fetches all signals
 * 2. Passes signals to this Client Component
 * 3. This component filters/searches client-side
 * 4. No additional API calls needed!
 *
 * File path: frontend/components/signals/SignalsList.tsx
 * See: frontend/LEARNING.md#module-4-interactive-lists
 */

"use client";

import { useState, useMemo, useEffect } from "react";
import { Signal, SignalType } from "@/lib/api";
import { SignalCard } from "./SignalCard";
import {
  SignalFilter,
  DEFAULT_BUY_THRESHOLD,
  DEFAULT_SELL_THRESHOLD,
} from "./SignalFilter";
import { useDebounce } from "@/hooks/useDebounce";
import { Card, CardContent } from "@/components/ui/card";

interface SignalsListProps {
  /** All signals from the server */
  signals: Signal[];
  /** Total count from API */
  total: number;
  /** Available sectors for filtering */
  sectors?: string[];
  /** Available categories for filtering */
  categories?: string[];
}

/**
 * Reclassify a signal based on custom thresholds
 * Uses total_score if available, otherwise keeps original classification
 */
function reclassifySignal(
  signal: Signal,
  buyThreshold: number,
  sellThreshold: number
): Signal {
  // If no total_score, return as-is
  if (signal.total_score === undefined || signal.total_score === null) {
    return signal;
  }

  // Reclassify based on thresholds
  let newType: "BUY" | "SELL" | "HOLD";
  if (signal.total_score >= buyThreshold) {
    newType = "BUY";
  } else if (signal.total_score <= sellThreshold) {
    newType = "SELL";
  } else {
    newType = "HOLD";
  }

  // Return signal with potentially updated type
  return {
    ...signal,
    signal_type: newType,
  };
}

export function SignalsList({
  signals,
  total,
  sectors = [],
  categories = [],
}: SignalsListProps) {
  // Filter state - these are "controlled" by React
  const [signalType, setSignalType] = useState<SignalType>("all");
  const [tickerSearch, setTickerSearch] = useState("");
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  // Threshold state
  const [buyThreshold, setBuyThreshold] = useState(DEFAULT_BUY_THRESHOLD);
  const [sellThreshold, setSellThreshold] = useState(DEFAULT_SELL_THRESHOLD);

  // Debounce the search to avoid filtering on every keystroke
  const debouncedSearch = useDebounce(tickerSearch, 300);

  // Check if thresholds are non-default (for showing reclassification info)
  const isCustomThresholds =
    buyThreshold !== DEFAULT_BUY_THRESHOLD ||
    sellThreshold !== DEFAULT_SELL_THRESHOLD;

  /**
   * Reclassify and filter signals based on current state
   */
  const filteredSignals = useMemo(() => {
    return signals
      .map((signal) => reclassifySignal(signal, buyThreshold, sellThreshold))
      .filter((signal) => {
        // Filter by signal type
        if (signalType !== "all" && signal.signal_type !== signalType) {
          return false;
        }

        // Filter by ticker search (case-insensitive)
        if (debouncedSearch) {
          const searchLower = debouncedSearch.toLowerCase();
          if (!signal.ticker.toLowerCase().includes(searchLower)) {
            return false;
          }
        }

        // Filter by sectors (if any selected, signal must match one of them)
        if (selectedSectors.length > 0 && !selectedSectors.includes(signal.sector || "")) {
          return false;
        }

        // Filter by categories (if any selected, signal must match one of them)
        if (selectedCategories.length > 0 && !selectedCategories.includes(signal.category || "")) {
          return false;
        }

        return true;
      });
  }, [
    signals,
    signalType,
    debouncedSearch,
    buyThreshold,
    sellThreshold,
    selectedSectors,
    selectedCategories,
  ]);

  // Count signals by type after reclassification
  const signalCounts = useMemo(() => {
    const reclassified = signals.map((s) =>
      reclassifySignal(s, buyThreshold, sellThreshold)
    );
    return {
      BUY: reclassified.filter((s) => s.signal_type === "BUY").length,
      SELL: reclassified.filter((s) => s.signal_type === "SELL").length,
      HOLD: reclassified.filter((s) => s.signal_type === "HOLD").length,
    };
  }, [signals, buyThreshold, sellThreshold]);

  return (
    <div>
      {/* Filter Controls */}
      <SignalFilter
        signalType={signalType}
        onSignalTypeChange={setSignalType}
        tickerSearch={tickerSearch}
        onTickerSearchChange={setTickerSearch}
        buyThreshold={buyThreshold}
        onBuyThresholdChange={setBuyThreshold}
        sellThreshold={sellThreshold}
        onSellThresholdChange={setSellThreshold}
        sectors={sectors}
        selectedSectors={selectedSectors}
        onSectorsChange={setSelectedSectors}
        categories={categories}
        selectedCategories={selectedCategories}
        onCategoriesChange={setSelectedCategories}
      />

      {/* Results Count */}
      <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500 mb-4">
        <span>
          Showing {filteredSignals.length} of {total} signals
        </span>
        {signalType !== "all" && (
          <span className="text-gray-400">({signalType} only)</span>
        )}
        {debouncedSearch && (
          <span className="text-gray-400">matching "{debouncedSearch}"</span>
        )}
        {selectedSectors.length > 0 && (
          <span className="text-gray-400">
            in {selectedSectors.length === 1 ? selectedSectors[0] : `${selectedSectors.length} sectors`}
          </span>
        )}
        {selectedCategories.length > 0 && (
          <span className="text-gray-400">
            Cat. {selectedCategories.length === 1 ? selectedCategories[0] : selectedCategories.join(", ")}
          </span>
        )}

        {/* Signal counts */}
        <span className="ml-auto flex gap-2">
          <span className="px-2 py-0.5 bg-buy/10 text-buy-dark rounded text-xs font-medium">
            {signalCounts.BUY} BUY
          </span>
          <span className="px-2 py-0.5 bg-hold/10 text-hold-dark rounded text-xs font-medium">
            {signalCounts.HOLD} HOLD
          </span>
          <span className="px-2 py-0.5 bg-sell/10 text-sell-dark rounded text-xs font-medium">
            {signalCounts.SELL} SELL
          </span>
        </span>
      </div>

      {/* Reclassification notice */}
      {isCustomThresholds && (
        <div className="mb-4 p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-700">
          Signals reclassified with custom thresholds (BUY &ge; {buyThreshold},
          SELL &le; {sellThreshold}). Original data unchanged.
        </div>
      )}

      {/* Signals Grid */}
      {filteredSignals.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-gray-500">No signals match your filters</p>
            <p className="text-sm text-gray-400 mt-2">
              Try adjusting your search or threshold settings
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredSignals.map((signal, index) => (
            <SignalCard
              key={signal.id ?? `${signal.ticker}-${signal.signal_date}-${index}`}
              signal={signal}
            />
          ))}
        </div>
      )}
    </div>
  );
}
