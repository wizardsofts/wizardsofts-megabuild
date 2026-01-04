'use client';

import { use } from 'react';
import Link from 'next/link';

interface SummaryPageProps {
  params: {
    ticker: string;
  };
}

export default function SummaryPage({ params }: SummaryPageProps) {
  const { ticker } = use(params);

  return (
    <div className="px-4 md:px-5 mt-3 md:mt-5">
      <div className="max-w-4xl mx-auto py-12">
        <h1 className="text-2xl font-semibold mb-4">Summary - {ticker}</h1>
        <p className="text-gray-600 mb-6">
          This page is under development. The Holdings page serves as the reference implementation.
        </p>
        <Link
          href={`/dashboard/dse/${ticker}/holding`}
          className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          View Holdings Page
        </Link>
      </div>
    </div>
  );
}
