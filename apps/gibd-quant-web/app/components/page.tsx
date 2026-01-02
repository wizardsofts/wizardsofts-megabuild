/**
 * Generative UI Components Demo Page
 *
 * LEARNING MODULE 7: GENERATIVE UI COMPONENTS
 * -------------------------------------------
 * This page showcases all the generative UI components
 * that can be rendered by AI responses.
 *
 * Key concepts:
 * 1. **Component library** - Reusable components for AI output
 * 2. **Visual consistency** - Same look across AI responses
 * 3. **Type safety** - Props define what AI can pass
 *
 * File path: frontend/app/components/page.tsx
 */

import {
  StockCard,
  SignalBadge,
  IndicatorDisplay,
  SignalsList,
} from "@/components/generative-ui";
import Link from "next/link";

/**
 * Demo page showing all generative UI components
 *
 * LEARNING NOTE:
 * In a production app, these components would be rendered
 * dynamically by an AI parser. Here we show them statically
 * to demonstrate their appearance and functionality.
 */
export default function ComponentsPage() {
  // Sample data for demonstration
  const sampleSignals = [
    { ticker: "GP", signal: "BUY" as const, score: 0.85, sector: "Telecom" },
    { ticker: "BATBC", signal: "BUY" as const, score: 0.72, sector: "Tobacco" },
    { ticker: "SQURPHARMA", signal: "HOLD" as const, score: 0.15, sector: "Pharma" },
    { ticker: "BEXIMCO", signal: "SELL" as const, score: -0.65, sector: "Pharma" },
    { ticker: "BRAC", signal: "SELL" as const, score: -0.48, sector: "Bank" },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <nav className="text-sm text-gray-500 mb-2">
          <Link href="/" className="hover:text-gray-700">
            Home
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900">Components</span>
        </nav>
        <h1 className="text-3xl font-bold text-gray-900">
          Generative UI Components
        </h1>
        <p className="text-gray-600 mt-1">
          These components can be rendered by AI to create rich, interactive responses
        </p>
      </div>

      {/* Component Sections */}
      <div className="space-y-12">
        {/* Section 1: Stock Card */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold">
              1
            </span>
            StockCard
          </h2>
          <p className="text-gray-600 mb-4">
            Rich display of stock information with signal, indicators, and price.
          </p>

          <div className="flex flex-wrap gap-4">
            <StockCard
              ticker="GP"
              name="Grameenphone Ltd."
              price={425.50}
              change={2.35}
              signal="BUY"
              confidence={0.85}
              rsi={62}
              sector="Telecommunication"
            />

            <StockCard
              ticker="BEXIMCO"
              name="BEXIMCO Ltd."
              price={128.75}
              change={-1.82}
              signal="SELL"
              confidence={0.72}
              rsi={78}
              sector="Pharmaceuticals"
            />

            <StockCard
              ticker="BATBC"
              name="British American Tobacco BD"
              price={512.25}
              change={0.15}
              signal="HOLD"
              confidence={0.45}
              rsi={52}
              sector="Tobacco"
            />
          </div>
        </section>

        {/* Section 2: Signal Badge */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold">
              2
            </span>
            SignalBadge
          </h2>
          <p className="text-gray-600 mb-4">
            Inline badges for embedding signals in text responses.
          </p>

          <div className="space-y-4">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-gray-600">Size variants:</span>
              <SignalBadge type="BUY" size="sm" />
              <SignalBadge type="BUY" size="md" />
              <SignalBadge type="BUY" size="lg" />
            </div>

            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-gray-600">Signal types:</span>
              <SignalBadge type="BUY" score={0.85} />
              <SignalBadge type="HOLD" score={0.15} />
              <SignalBadge type="SELL" score={0.72} />
            </div>

            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-gray-700">
                Based on technical analysis, GP shows a{" "}
                <SignalBadge type="BUY" score={0.85} /> signal with strong
                momentum, while BEXIMCO indicates a{" "}
                <SignalBadge type="SELL" score={0.72} /> due to overbought RSI
                conditions.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: Indicator Display */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold">
              3
            </span>
            IndicatorDisplay
          </h2>
          <p className="text-gray-600 mb-4">
            Visual display of technical indicators with thresholds and interpretation.
          </p>

          <div className="flex flex-wrap gap-4">
            <IndicatorDisplay
              name="RSI (14)"
              value={72}
              min={0}
              max={100}
              description="Overbought territory - consider taking profits"
              warningThreshold={70}
              dangerThreshold={30}
              higherIsBetter={false}
            />

            <IndicatorDisplay
              name="RSI (14)"
              value={28}
              min={0}
              max={100}
              description="Oversold territory - potential buying opportunity"
              warningThreshold={30}
              dangerThreshold={20}
              higherIsBetter={true}
            />

            <IndicatorDisplay
              name="ADX (14)"
              value={35}
              min={0}
              max={100}
              description="Strong trend present"
              warningThreshold={20}
              dangerThreshold={10}
              higherIsBetter={true}
            />
          </div>
        </section>

        {/* Section 4: Signals List */}
        <section>
          <h2 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold">
              4
            </span>
            SignalsList
          </h2>
          <p className="text-gray-600 mb-4">
            Compact list view for showing multiple signals at once.
          </p>

          <div className="flex flex-wrap gap-4">
            <SignalsList
              title="Today&apos;s Top Signals"
              signals={sampleSignals}
              limit={5}
            />

            <SignalsList
              title="BUY Signals Only"
              signals={sampleSignals.filter((s) => s.signal === "BUY")}
            />
          </div>
        </section>
      </div>

      {/* Learning callout */}
      <div className="mt-12 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <h3 className="font-semibold text-blue-900 mb-2">
          Module 7: Generative UI Components
        </h3>
        <p className="text-blue-800 text-sm">
          These components enable rich AI responses beyond plain text. Key learnings:
        </p>
        <ul className="text-blue-800 text-sm mt-2 space-y-1 list-disc list-inside">
          <li>Define TypeScript interfaces for AI-generated props</li>
          <li>Create visually consistent components for AI to render</li>
          <li>Use semantic colors and visual indicators</li>
          <li>Support both inline (badges) and block (cards) layouts</li>
        </ul>
        <p className="text-blue-700 text-sm mt-2">
          See{" "}
          <code className="bg-blue-100 px-1 rounded">
            frontend/LEARNING.md#module-7-generative-ui
          </code>{" "}
          for details.
        </p>
      </div>
    </div>
  );
}
