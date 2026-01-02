/**
 * Loading State for Signals Page
 *
 * LEARNING MODULE 3:
 * -----------------
 * In Next.js App Router, `loading.tsx` is a special file that:
 * - Automatically shows while the page is loading data
 * - Wraps the page in a React Suspense boundary
 * - No need to manually manage loading states!
 *
 * This works because React Server Components can be async.
 * While the async page.tsx is loading, Next.js shows loading.tsx.
 *
 * File path: frontend/app/signals/loading.tsx
 * See: frontend/LEARNING.md#module-3-loading-states
 */

import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function SignalsLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        {/* Title skeleton */}
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-2" />
        <div className="h-4 w-96 bg-gray-100 rounded animate-pulse" />
      </div>

      {/* Signal cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-6 w-16 bg-gray-200 rounded" />
                <div className="h-6 w-12 bg-gray-200 rounded-full" />
              </div>
              <div className="h-4 w-24 bg-gray-100 rounded mt-2" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="h-4 w-full bg-gray-100 rounded" />
                <div className="h-4 w-3/4 bg-gray-100 rounded" />
                <div className="h-4 w-1/2 bg-gray-100 rounded" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
