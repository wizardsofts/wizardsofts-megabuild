import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge, SignalBadge } from "@/components/ui/badge";

/**
 * Home Page - The main landing page of Guardian Investment BD
 *
 * LEARNING MODULE 2:
 * -----------------
 * This page demonstrates using the components we created:
 * - Button with different variants
 * - Card with compound components
 * - Badge and SignalBadge for status indicators
 * - Link from next/link for navigation
 *
 * Notice how we import components using the `@/` path alias:
 * - `@/components/ui/button` instead of `../../components/ui/button`
 * - This is configured in tsconfig.json
 *
 * File path: frontend/app/page.tsx
 * See: frontend/LEARNING.md#module-2-home-page
 */

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-12">
      {/* Hero Section */}
      <section className="text-center max-w-3xl mx-auto mb-16">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          AI-Powered Trading Signals
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Quantitative analysis for Dhaka Stock Exchange with Generative UI
        </p>

        {/* Signal Type Badges */}
        <div className="flex justify-center gap-4 mb-8">
          <SignalBadge type="BUY" />
          <SignalBadge type="HOLD" />
          <SignalBadge type="SELL" />
        </div>

        {/* CTA Buttons */}
        <div className="flex justify-center gap-4">
          <Link href="/signals">
            <Button size="lg">View Signals</Button>
          </Link>
          <Link href="/chat">
            <Button variant="outline" size="lg">
              Try AI Chat
            </Button>
          </Link>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {/* Signals Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Signals
              <Badge variant="outline">Live</Badge>
            </CardTitle>
            <CardDescription>
              Real-time trading signals from the analysis engine
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              View BUY, SELL, and HOLD signals with confidence scores,
              entry prices, and target levels.
            </p>
            <Link href="/signals">
              <Button variant="outline" size="sm" className="w-full">
                View Signals →
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Charts Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📈 Charts
              <Badge variant="outline">Analytics</Badge>
            </CardTitle>
            <CardDescription>
              Performance metrics and sector analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Interactive charts showing signal performance, sector heatmaps,
              and backtesting results.
            </p>
            <Link href="/charts">
              <Button variant="outline" size="sm" className="w-full">
                View Charts →
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* AI Chat Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              💬 AI Chat
              <Badge>Generative UI</Badge>
            </CardTitle>
            <CardDescription>
              Ask questions, get visual answers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              Chat with AI that responds with interactive components -
              signal cards, charts, and tables.
            </p>
            <Link href="/chat">
              <Button variant="outline" size="sm" className="w-full">
                Start Chatting →
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>

      {/* Tech Stack Section */}
      <section className="mt-16 text-center">
        <h2 className="text-sm font-medium text-gray-500 mb-4">BUILT WITH</h2>
        <div className="flex justify-center flex-wrap gap-3">
          <Badge variant="outline">Next.js 14</Badge>
          <Badge variant="outline">Vercel AI SDK</Badge>
          <Badge variant="outline">LangChain</Badge>
          <Badge variant="outline">Ollama</Badge>
          <Badge variant="outline">Tailwind CSS</Badge>
          <Badge variant="outline">TypeScript</Badge>
        </div>
      </section>
    </div>
  );
}
