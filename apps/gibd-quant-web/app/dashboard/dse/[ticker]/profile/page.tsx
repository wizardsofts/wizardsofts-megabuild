'use client';

import { use } from 'react';
import Link from 'next/link';
import { Card, CardHeader, CardBody } from '@wizwebui/core';

/**
 * Company Profile Page - Comprehensive company information
 *
 * URL: /dashboard/dse/{ticker}/profile
 * Example: /dashboard/dse/BATBC/profile
 *
 * Features:
 * - Three-column layout (responsive)
 * - Capital structure information
 * - Company overview and board of directors
 * - Market statistics and shareholding structure
 *
 * Component Library: wizwebui v0.2.0
 */

interface ProfilePageProps {
  params: {
    ticker: string;
  };
}

// Mock data - Replace with API calls in production
const companyData = {
  overview: {
    name: 'British American Tobacco Bangladesh Company Limited',
    ticker: 'BATBC',
    description: 'British American Tobacco Bangladesh Company Limited (BATBC) is one of the largest multinational corporations in Bangladesh. It manufactures and markets high-quality tobacco products. Listed on the Dhaka Stock Exchange, it is a blue-chip stock known for its consistent performance and contribution to the national exchequer.',
    listingYear: '1977',
    marketCategory: 'A',
    electronicShare: 'Yes',
    lastAGM: '25-03-2025',
  },
  capital: {
    authorizedCap: '5,400.00 Mn',
    paidUpCap: '5,400.00 Mn',
    faceValue: '10.00',
    outstandingSec: '540,000,000',
    marketCap: '134,406.00 Mn',
  },
  corporate: {
    headOffice: 'New DOHS Road, Mohakhali, Dhaka-1206, Bangladesh',
    website: 'batbangladesh.com',
  },
  directors: [
    { name: 'Mr. Golam Mainuddin', position: 'Chairman' },
    { name: 'Shehzad Munim', position: 'Managing Director' },
    { name: 'Mr. K. H. Masud Siddiqui', position: 'Independent Director' },
    { name: 'Ms. Amun Mustafiz', position: 'Director' },
  ],
  marketStats: {
    lastTradePrice: '248.60',
    closePrice: '248.60',
    yesterdayClose: '248.60',
    tradeVolume: '5,320',
    tradeValue: '1.32',
  },
  shareholding: [
    { category: 'Sponsor', percentage: 72.91, color: '#000000' },
    { category: 'Institute', percentage: 12.03, color: '#0056b3' },
    { category: 'Foreign', percentage: 6.84, color: '#9e9e9e' },
    { category: 'Public', percentage: 7.58, color: '#e0e0e0' },
  ],
};

export default function ProfilePage({ params }: ProfilePageProps) {
  const { ticker } = use(params);

  return (
    <div className="px-3 sm:px-4 md:px-5 mt-3 md:mt-5">
      {/* Three-column grid - Responsive */}
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr_340px] gap-4 md:gap-6">

        {/* Left Column */}
        <div className="space-y-4 md:space-y-6">
          {/* Capital Structure */}
          <Card variant="panel">
            <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
              Capital Structure
            </CardHeader>
            <CardBody className="p-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Authorized Cap</span>
                  <span className="text-sm font-semibold">{companyData.capital.authorizedCap}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Paid-up Cap</span>
                  <span className="text-sm font-semibold">{companyData.capital.paidUpCap}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Face Value</span>
                  <span className="text-sm font-semibold">{companyData.capital.faceValue}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Outstanding Sec</span>
                  <span className="text-sm font-semibold">{companyData.capital.outstandingSec}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Market Cap</span>
                  <span className="text-sm font-semibold">{companyData.capital.marketCap}</span>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Corporate Info */}
          <Card variant="panel">
            <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
              Corporate Info
            </CardHeader>
            <CardBody className="p-4">
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-600 mb-1">Head Office</div>
                  <div className="text-sm font-medium">{companyData.corporate.headOffice}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600 mb-1">Website</div>
                  <Link
                    href={`https://${companyData.corporate.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {companyData.corporate.website}
                  </Link>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Middle Column */}
        <div className="space-y-4 md:space-y-6">
          {/* Company Overview */}
          <Card variant="panel">
            <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
              Company Overview
            </CardHeader>
            <CardBody className="p-4">
              <p className="text-sm text-gray-700 leading-relaxed mb-4">
                {companyData.overview.description}
              </p>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Listing Year</div>
                  <div className="text-base font-semibold">{companyData.overview.listingYear}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Market Category</div>
                  <div className="text-base font-semibold">{companyData.overview.marketCategory}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Electronic Share</div>
                  <div className="text-base font-semibold">{companyData.overview.electronicShare}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Last AGM</div>
                  <div className="text-base font-semibold">{companyData.overview.lastAGM}</div>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Board of Directors */}
          <Card variant="panel">
            <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
              Board of Directors
            </CardHeader>
            <CardBody className="p-4">
              <div className="space-y-3">
                {companyData.directors.map((director, index) => (
                  <div
                    key={index}
                    className="flex justify-between items-center border-b border-gray-100 pb-3 last:border-0 last:pb-0"
                  >
                    <span className="text-sm font-medium">{director.name}</span>
                    <span className="text-sm text-gray-600">{director.position}</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-4 md:space-y-6">
          {/* Market Statistics */}
          <Card variant="panel">
            <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
              Market Statistics
            </CardHeader>
            <CardBody className="p-4">
              <div className="space-y-3">
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Last Trade Price</span>
                  <span className="text-sm font-semibold">{companyData.marketStats.lastTradePrice}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Close Price</span>
                  <span className="text-sm font-semibold">{companyData.marketStats.closePrice}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Yesterday Close</span>
                  <span className="text-sm font-semibold">{companyData.marketStats.yesterdayClose}</span>
                </div>
                <div className="flex justify-between items-center border-b border-gray-100 pb-2">
                  <span className="text-sm text-gray-600">Trade Volume</span>
                  <span className="text-sm font-semibold">{companyData.marketStats.tradeVolume}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Trade Value (mn)</span>
                  <span className="text-sm font-semibold">{companyData.marketStats.tradeValue}</span>
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Shareholding Structure */}
          <Card variant="panel">
            <CardHeader variant="compact" uppercase className="text-xs text-gray-600">
              Shareholding Structure
            </CardHeader>
            <CardBody className="p-4">
              {/* Horizontal Bar Chart */}
              <div className="mb-4">
                <div className="flex h-6 rounded overflow-hidden">
                  {companyData.shareholding.map((item, index) => (
                    <div
                      key={index}
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: item.color,
                      }}
                      title={`${item.category}: ${item.percentage}%`}
                    />
                  ))}
                </div>
              </div>

              {/* Legend */}
              <div className="space-y-2">
                {companyData.shareholding.map((item, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-sm"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-gray-700">{item.category}</span>
                    </div>
                    <span className="text-sm font-semibold">{item.percentage}%</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
