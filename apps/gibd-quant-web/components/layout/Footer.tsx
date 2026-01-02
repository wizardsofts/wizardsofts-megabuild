'use client';

import Link from "next/link";
import { trackEvent } from '@/lib/analytics';

/**
 * Footer Component - Minimal fixed footer
 *
 * Features:
 * - Fixed at bottom
 * - One-line minimal design with disclaimer and important links
 * - Click tracking for all links
 */

export function Footer() {
  const handleLinkClick = (label: string) => {
    trackEvent('footer', 'footer_link_click', label);
  };

  return (
    <footer className="fixed bottom-0 left-0 right-0 z-40 w-full border-t border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80">
      <div className="container mx-auto px-4 py-2">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-gray-600">
          {/* Disclaimer */}
          <div className="flex items-center gap-2">
            <span>© {new Date().getFullYear()} Guardian Investment BD</span>
            <span className="hidden sm:inline">•</span>
            <span className="text-center sm:text-left">
              Not financial advice. For educational purposes only.
            </span>
          </div>

          {/* Important Links */}
          <div className="flex items-center gap-3">
            <Link
              href="/about"
              className="hover:text-gray-900 transition-colors"
              onClick={() => handleLinkClick('About')}
            >
              About
            </Link>
            <span>•</span>
            <Link
              href="/disclaimer"
              className="hover:text-gray-900 transition-colors"
              onClick={() => handleLinkClick('Disclaimer')}
            >
              Disclaimer
            </Link>
            <span>•</span>
            <Link
              href="/privacy"
              className="hover:text-gray-900 transition-colors"
              onClick={() => handleLinkClick('Privacy')}
            >
              Privacy
            </Link>
            <span className="hidden md:inline">•</span>
            <a
              href="https://github.com/wizardsofts/quant-flow"
              target="_blank"
              rel="noopener noreferrer"
              className="hidden md:inline hover:text-gray-900 transition-colors"
              onClick={() => handleLinkClick('GitHub')}
            >
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
