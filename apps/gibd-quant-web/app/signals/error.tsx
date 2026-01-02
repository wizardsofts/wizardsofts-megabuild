"use client";

/**
 * Error Boundary for Signals Page
 *
 * LEARNING MODULE 3:
 * -----------------
 * In Next.js App Router, `error.tsx` is a special file that:
 * - Catches errors thrown during rendering
 * - Shows a fallback UI instead of crashing
 * - Provides a "Try again" button to retry
 *
 * IMPORTANT: Error boundaries must be Client Components ("use client")
 * because they use React's error boundary feature which requires state.
 *
 * The `reset` function is provided by Next.js to retry rendering.
 *
 * File path: frontend/app/signals/error.tsx
 * See: frontend/LEARNING.md#module-3-error-handling
 */

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function SignalsError({ error, reset }: ErrorProps) {
  return (
    <div className="container mx-auto px-4 py-8">
      <Card className="max-w-lg mx-auto border-red-200">
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Signals</CardTitle>
          <CardDescription>
            Something went wrong while fetching trading signals.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Error message */}
          <div className="p-3 bg-red-50 rounded-lg text-sm text-red-800">
            <strong>Error:</strong> {error.message}
          </div>

          {/* Possible causes */}
          <div className="text-sm text-gray-600">
            <p className="font-medium mb-2">Possible causes:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Backend server is not running (port 5000)</li>
              <li>Database connection failed</li>
              <li>Network connectivity issues</li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button onClick={reset} variant="default">
              Try Again
            </Button>
            <Button
              onClick={() => (window.location.href = "/")}
              variant="outline"
            >
              Go Home
            </Button>
          </div>

          {/* Debug info (development only) */}
          {process.env.NODE_ENV === "development" && error.digest && (
            <p className="text-xs text-gray-400">Digest: {error.digest}</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
