/**
 * Not Found Page for Company Route
 *
 * Displayed when a company ticker is not found in the database.
 */

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function CompanyNotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader>
          <CardTitle className="text-2xl text-gray-900 flex items-center gap-2">
            <span>🔍</span>
            <span>Company Not Found</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Not found message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              The company you're looking for could not be found in our database.
            </p>
          </div>

          {/* Suggestions */}
          <div className="space-y-2">
            <h3 className="font-semibold text-gray-900">Suggestions:</h3>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
              <li>Check that the ticker symbol is correct (e.g., GP, BATBC, SQURPHARMA)</li>
              <li>Verify the company is listed on the Dhaka Stock Exchange</li>
              <li>Try searching from the signals page to find valid tickers</li>
            </ul>
          </div>

          {/* Action buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Link href="/signals" className="flex-1">
              <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                Browse All Signals
              </Button>
            </Link>
            <Link href="/charts" className="flex-1">
              <Button variant="outline" className="w-full">
                View Charts
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
