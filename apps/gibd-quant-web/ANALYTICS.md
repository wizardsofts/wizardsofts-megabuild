# Analytics & Tracking Documentation

This document describes the analytics and tracking features integrated into Quant-Flow.

## Overview

Quant-Flow includes comprehensive analytics tracking to understand user behavior and optimize the application. The system supports Google Analytics (GA4) and Google AdSense/AdMob integration.

## Features

### 1. Fixed Layout

#### Header
- **Position**: Fixed at the top of the viewport
- **Design**: Minimal one-line navigation
- **Components**:
  - Logo and branding (Quant-Flow DSE)
  - Navigation menu (Signals, Charts, Chat, Multi-Criteria)
  - Ticker search input (desktop only)
- **Styling**: Backdrop blur for modern glass-morphism effect

#### Footer
- **Position**: Fixed at the bottom of the viewport
- **Design**: Minimal one-line layout
- **Components**:
  - Copyright notice
  - Disclaimer text
  - Quick links (About, Disclaimer, Privacy, GitHub)
- **Responsive**: Adapts for mobile and desktop layouts

### 2. Google Analytics (GA4)

#### Setup

1. Get your GA4 Measurement ID from [Google Analytics](https://analytics.google.com/)
2. Add to `.env.local`:
   ```bash
   NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
   ```

#### Features

- **Automatic Pageview Tracking**: Tracks route changes automatically
- **Custom Event Tracking**: Track user interactions throughout the app
- **Performance Monitoring**: Track API response times and errors

#### Implementation

The analytics system is integrated in:
- `lib/analytics.ts` - Core tracking functions
- `components/analytics/GoogleAnalytics.tsx` - GA4 script loader and pageview tracker
- `components/analytics/ClickTracker.tsx` - Global click tracking component

#### Events Tracked

| Event Type | Category | Action | Label |
|------------|----------|--------|-------|
| Pageview | - | config | Page path |
| Navigation | navigation | header_nav_click | Link name |
| Ticker Search | search | ticker_search | Ticker symbol |
| Link Click | link | click | Link text/URL |
| Button Click | button | click | Button text |
| Form Submit | form | submit | Form name |
| Footer Link | footer | footer_link_click | Link name |

### 3. Google AdSense / AdMob

#### Setup

1. Get your AdSense Client ID from [Google AdSense](https://www.google.com/adsense/)
2. Create ad units and get slot IDs
3. Add to `.env.local`:
   ```bash
   NEXT_PUBLIC_ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
   NEXT_PUBLIC_ADSENSE_BANNER_SLOT=XXXXXXXXXX
   NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=XXXXXXXXXX
   NEXT_PUBLIC_ADSENSE_INFEED_SLOT=XXXXXXXXXX
   ```

#### Ad Components

```typescript
import { AdBanner, AdSidebar, AdInFeed } from '@/components/analytics/AdMob';

// Banner ad (horizontal)
<AdBanner className="my-4" />

// Sidebar ad (vertical)
<AdSidebar className="my-4" />

// In-feed ad (fluid)
<AdInFeed className="my-4" />

// Custom ad with specific slot
<AdMobAd
  adSlot="XXXXXXXXXX"
  adFormat="auto"
  fullWidthResponsive={true}
  className="my-4"
/>
```

### 4. Click Tracking

Automatic click tracking is enabled globally via the `ClickTracker` component. All clicks on the following elements are automatically tracked:

- **Links** (`<a>` tags): Captures href and link text
- **Buttons** (`<button>` tags): Captures button text or aria-label
- **Form Submits**: Captures form name or ID

The tracker uses event delegation for optimal performance and works with dynamically added elements.

## API Reference

### Core Functions

#### `trackEvent(category, action, label, value?)`
Track a custom event.

```typescript
trackEvent('video', 'play', 'intro_video', 30);
```

#### `trackButtonClick(buttonName)`
Track button clicks.

```typescript
trackButtonClick('Submit Order');
```

#### `trackLinkClick(href, label)`
Track link clicks.

```typescript
trackLinkClick('/signals', 'View All Signals');
```

#### `trackFormSubmit(formName)`
Track form submissions.

```typescript
trackFormSubmit('contact_form');
```

#### `trackSearch(query, resultsCount?)`
Track search queries.

```typescript
trackSearch('RSI above 70', 15);
```

#### `trackError(errorMessage, errorType)`
Track errors.

```typescript
trackError('Failed to fetch signals', 'api_error');
```

#### `trackTiming(category, variable, value, label?)`
Track timing/performance metrics.

```typescript
trackTiming('api', 'fetch_signals', 1500, 'signals_page');
```

## Integration Examples

### Track Custom Events in Components

```typescript
'use client';

import { trackEvent } from '@/lib/analytics';

export function MyComponent() {
  const handleAction = () => {
    // Your logic here
    trackEvent('user_action', 'clicked_special_button', 'feature_x');
  };

  return <button onClick={handleAction}>Click Me</button>;
}
```

### Track API Performance

```typescript
import { trackTiming } from '@/lib/analytics';

async function fetchSignals() {
  const startTime = performance.now();

  try {
    const response = await fetch('/api/signals');
    const data = await response.json();

    const duration = performance.now() - startTime;
    trackTiming('api', 'fetch_signals', duration, 'success');

    return data;
  } catch (error) {
    const duration = performance.now() - startTime;
    trackTiming('api', 'fetch_signals', duration, 'error');
    throw error;
  }
}
```

## Privacy & GDPR Compliance

### Important Notes

1. **Cookie Consent**: Consider implementing a cookie consent banner before loading analytics scripts
2. **Privacy Policy**: Update your privacy policy to disclose analytics usage
3. **Opt-out**: Provide users with an option to opt-out of tracking
4. **Data Retention**: Configure data retention settings in Google Analytics

### Disable Analytics

To disable analytics, simply don't set the environment variables:
- Analytics scripts won't load if `NEXT_PUBLIC_GA_MEASUREMENT_ID` is not set
- Ad scripts won't load if `NEXT_PUBLIC_ADSENSE_CLIENT_ID` is not set

## Testing

Unit tests for analytics functions are located in `__tests__/lib/analytics.test.ts`.

Run tests:
```bash
npm test
```

## Troubleshooting

### Analytics not working

1. **Check environment variables**: Ensure `NEXT_PUBLIC_GA_MEASUREMENT_ID` is set correctly
2. **Check browser console**: Look for errors related to gtag or Google Analytics
3. **Verify script loading**: Check Network tab in DevTools for gtag/js requests
4. **Ad blockers**: Some browser extensions block analytics scripts

### Click tracking not working

1. **Check console for errors**: The ClickTracker component logs errors to console
2. **Verify gtag is loaded**: Check `window.gtag` exists in browser console
3. **Check event delegation**: Ensure clicks bubble up to document level

## Performance Considerations

- **Lazy Loading**: Analytics scripts use `strategy="afterInteractive"` to load after the page is interactive
- **Event Delegation**: Click tracking uses event delegation to minimize overhead
- **Conditional Loading**: Scripts only load when environment variables are set

## Additional Resources

- [Google Analytics 4 Documentation](https://support.google.com/analytics/answer/10089681)
- [Google AdSense Help Center](https://support.google.com/adsense/)
- [Next.js Analytics Integration](https://nextjs.org/docs/app/building-your-application/optimizing/analytics)
