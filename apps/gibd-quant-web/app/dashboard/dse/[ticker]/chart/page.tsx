'use client';

import { use } from 'react';
import CompanyChart from '@/components/company/CompanyChart';

interface ChartPageProps {
  params: {
    ticker: string;
  };
}

export default function ChartPage({ params }: ChartPageProps) {
  const { ticker } = use(params);

  return (
    <div className="px-4 md:px-5 mt-3 md:mt-5">
      <div className="max-w-7xl mx-auto">
        <CompanyChart ticker={ticker} />
      </div>
    </div>
  );
}
