/**
 * Loading State for Company Page
 *
 * Displays skeleton UI with animated placeholders while data is being fetched.
 */

import { Card, CardContent, CardHeader } from '@/components/ui/card';

export default function CompanyLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header Skeleton */}
        <Card className="mb-6">
          <CardHeader>
            <div className="space-y-4">
              {/* Company name and ticker */}
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="space-y-2">
                  <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
                  <div className="flex gap-2">
                    <div className="h-6 w-20 bg-gray-200 rounded animate-pulse" />
                    <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
                  </div>
                </div>
                <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
              </div>

              {/* Price metrics grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="space-y-2">
                    <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
                    <div className="h-6 w-24 bg-gray-200 rounded animate-pulse" />
                  </div>
                ))}
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Tabs Skeleton */}
        <Card>
          <CardHeader>
            <div className="flex gap-2 overflow-x-auto">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-10 w-32 bg-gray-200 rounded animate-pulse flex-shrink-0"
                />
              ))}
            </div>
          </CardHeader>

          {/* Content Skeleton */}
          <CardContent>
            <div className="space-y-6">
              {/* Chart skeleton */}
              <div className="h-64 md:h-96 bg-gray-200 rounded animate-pulse" />

              {/* Grid skeleton */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="space-y-3">
                    <div className="h-6 w-40 bg-gray-200 rounded animate-pulse" />
                    <div className="space-y-2">
                      <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
                      <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse" />
                      <div className="h-4 w-5/6 bg-gray-200 rounded animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
