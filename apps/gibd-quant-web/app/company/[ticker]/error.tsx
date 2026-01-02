/**
 * Error Boundary for Company Page
 *
 * Handles errors gracefully with retry functionality and helpful messages.
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function CompanyError({ error, reset }: ErrorProps) {
  const router = useRouter();

  useEffect(() => {
    // Log error to console for debugging
    console.error('Company page error:', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader>
          <CardTitle className="text-2xl text-red-600 flex items-center gap-2">
            <span>⚠️</span>
            <span>Something went wrong</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Error message */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800 font-medium">
              {error.message || 'An unexpected error occurred while loading the company page.'}
            </p>
            {error.digest && (
              <p className="text-xs text-red-600 mt-2">Error ID: {error.digest}</p>
            )}
          </div>

          {/* Common causes */}
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900">Common causes:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
              <li>Invalid ticker symbol</li>
              <li>Company data not available in the database</li>
              <li>Network connection issues</li>
              <li>Backend service temporarily unavailable</li>
            </ul>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              onClick={reset}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            >
              Try Again
            </Button>
            <Button
              onClick={() => router.push('/signals')}
              variant="outline"
              className="flex-1"
            >
              ← Back to Signals
            </Button>
          </div>

          {/* Help text */}
          <p className="text-xs text-gray-500 text-center">
            If this error persists, please try a different ticker or contact support.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
