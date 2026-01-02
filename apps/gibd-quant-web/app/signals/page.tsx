import { getSignals, getSectors, getCategories } from "@/lib/api";
import { SignalsList } from "@/components/signals/SignalsList";

/**
 * Signals Page - Displays trading signals from the backend
 *
 * LEARNING MODULE 3 & 4:
 * ---------------------
 * This demonstrates the HYBRID pattern: Server + Client Components together.
 *
 * How it works:
 * 1. This page is a SERVER Component (async, fetches data)
 * 2. It passes data to SignalsList, a CLIENT Component
 * 3. SignalsList handles filtering/searching client-side
 *
 * Benefits:
 * - Fast initial load (server-rendered HTML with data)
 * - Interactive filtering without page reloads
 * - No loading spinners for filter changes
 * - SEO friendly (data in initial HTML)
 *
 * File path: frontend/app/signals/page.tsx
 * See: frontend/LEARNING.md#module-4-hybrid-rendering
 */

// This tells Next.js to not cache this page (always fetch fresh data)
export const dynamic = "force-dynamic";

export default async function SignalsPage() {
  // Fetch signals, sectors, and categories from the backend API in parallel
  // This runs on the SERVER, not in the browser!
  const [response, sectors, categories] = await Promise.all([
    getSignals({ limit: 500 }),
    getSectors(),
    getCategories(),
  ]);
  const signals = response.signals;

  // Debug: log first few signals to see sector/category
  console.log(
    "Server: First 3 signals:",
    signals.slice(0, 3).map((s) => ({
      ticker: s.ticker,
      sector: s.sector,
      category: s.category,
    }))
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Trading Signals</h1>
        <p className="text-gray-600 mt-2">
          Latest signals from the AdaptiveSignalEngine
        </p>
      </div>

      {/* Interactive Signals List (Client Component) */}
      <SignalsList
        signals={signals}
        total={response.total}
        sectors={sectors}
        categories={categories}
      />
    </div>
  );
}
