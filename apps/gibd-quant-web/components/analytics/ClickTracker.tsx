'use client';

import { useEffect } from 'react';
import { trackButtonClick, trackLinkClick, trackFormSubmit } from '@/lib/analytics';

/**
 * Global Click Tracker Component
 *
 * Features:
 * - Automatically tracks clicks on links, buttons, and forms
 * - Uses event delegation for performance
 * - Extracts meaningful labels from elements
 */

export function ClickTracker() {
  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;

      // Track link clicks
      const link = target.closest('a');
      if (link) {
        const href = link.getAttribute('href') || '';
        const label = link.textContent?.trim() || link.getAttribute('aria-label') || href;
        trackLinkClick(href, label);
        return;
      }

      // Track button clicks
      const button = target.closest('button');
      if (button) {
        const label =
          button.textContent?.trim() ||
          button.getAttribute('aria-label') ||
          button.getAttribute('type') ||
          'button';
        trackButtonClick(label);
        return;
      }

      // Track input button clicks (submit, reset, button)
      const input = target.closest('input[type="submit"], input[type="button"], input[type="reset"]');
      if (input) {
        const inputElement = input as HTMLInputElement;
        const label =
          inputElement.value ||
          inputElement.getAttribute('aria-label') ||
          inputElement.type;
        trackButtonClick(label);
        return;
      }
    };

    const handleSubmit = (event: SubmitEvent) => {
      const form = event.target as HTMLFormElement;
      const formName =
        form.getAttribute('name') ||
        form.getAttribute('id') ||
        form.getAttribute('aria-label') ||
        'form';
      trackFormSubmit(formName);
    };

    // Add event listeners with capturing to catch events early
    document.addEventListener('click', handleClick, true);
    document.addEventListener('submit', handleSubmit, true);

    // Cleanup
    return () => {
      document.removeEventListener('click', handleClick, true);
      document.removeEventListener('submit', handleSubmit, true);
    };
  }, []);

  // This component doesn't render anything
  return null;
}
