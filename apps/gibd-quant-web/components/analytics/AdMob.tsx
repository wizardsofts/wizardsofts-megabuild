'use client';

import Script from 'next/script';
import { useEffect } from 'react';

/**
 * AdMob/AdSense Component
 *
 * Features:
 * - Loads Google AdSense script
 * - Displays responsive ads
 * - Only loads if ADSENSE_CLIENT_ID is set
 */

declare global {
  interface Window {
    adsbygoogle?: unknown[];
  }
}

interface AdMobProps {
  /**
   * Ad slot ID (data-ad-slot)
   */
  adSlot: string;
  /**
   * Ad format (auto, fluid, rectangle, etc.)
   */
  adFormat?: 'auto' | 'fluid' | 'rectangle' | 'vertical' | 'horizontal';
  /**
   * Full width responsive (only for auto format)
   */
  fullWidthResponsive?: boolean;
  /**
   * Custom className
   */
  className?: string;
}

export function AdMobScript() {
  const clientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID;

  if (!clientId) {
    return null;
  }

  return (
    <Script
      async
      src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${clientId}`}
      crossOrigin="anonymous"
      strategy="afterInteractive"
    />
  );
}

export function AdMobAd({
  adSlot,
  adFormat = 'auto',
  fullWidthResponsive = true,
  className = '',
}: AdMobProps) {
  const clientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID;

  useEffect(() => {
    if (clientId) {
      try {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      } catch (err) {
        console.error('AdSense error:', err);
      }
    }
  }, [clientId]);

  // Don't render if no client ID
  if (!clientId) {
    return null;
  }

  return (
    <ins
      className={`adsbygoogle ${className}`}
      style={{ display: 'block' }}
      data-ad-client={clientId}
      data-ad-slot={adSlot}
      data-ad-format={adFormat}
      data-full-width-responsive={fullWidthResponsive ? 'true' : 'false'}
    />
  );
}

/**
 * Predefined ad components for common placements
 */

export function AdBanner({ className = '' }: { className?: string }) {
  return (
    <AdMobAd
      adSlot={process.env.NEXT_PUBLIC_ADSENSE_BANNER_SLOT || ''}
      adFormat="horizontal"
      className={className}
    />
  );
}

export function AdSidebar({ className = '' }: { className?: string }) {
  return (
    <AdMobAd
      adSlot={process.env.NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT || ''}
      adFormat="vertical"
      className={className}
    />
  );
}

export function AdInFeed({ className = '' }: { className?: string }) {
  return (
    <AdMobAd
      adSlot={process.env.NEXT_PUBLIC_ADSENSE_INFEED_SLOT || ''}
      adFormat="fluid"
      className={className}
    />
  );
}
