# BondWala Coming Soon Page - Documentation

## Overview
The BondWala page on wizardsofts.com has been updated to display a "Coming Soon" message instead of download links, as the app is not yet available for public release.

## Changes Made

### 1. Dynamic Launch Date
- **Previous**: Static date "January 5, 2026"
- **Current**: Dynamic calculation showing 7 days from the current visit date
- **Implementation**: Uses React `useEffect` hook to calculate and format the date on client-side
- **Format**: "Month Day, Year" (e.g., "January 6, 2026")

### 2. Hero Section Updates
- Replaced "Download Now" button with static display showing "Coming Soon - {launchDate}"
- Retained "Learn More" button pointing to #how-it-works section
- Button is now a `<div>` instead of `<a>` (no longer clickable)

### 3. Download Section Updates
- **Section Title**: Changed from "Download BondWala Now" to "Coming Soon"
- **Description**: Updated to mention the dynamic launch date
- **Visual Element**: Added prominent date display box with:
  - "Expected Launch Date" label
  - Large formatted date in primary brand color
  - "Stay tuned for updates!" message
- **Download Links**: Hidden (commented out) for both:
  - Google Play Store
  - Apple App Store

### 4. Feature Request Section
- Already removed in previous update
- Not present in current version

## Technical Implementation

### File Modified
- `apps/ws-wizardsofts-web/app/bondwala/page.tsx`

### Key Code Changes

```typescript
// Added state for dynamic date
const [launchDate, setLaunchDate] = useState<string>("");

// Calculate 7 days from now on component mount
useEffect(() => {
  const now = new Date();
  const launch = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  const formatted = launch.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  setLaunchDate(formatted);
}, []);
```

### Fallback Handling
- When JavaScript is disabled or before `useEffect` runs, displays:
  - Hero: "Coming Soon - January 2026"
  - Download section: "soon" and "Coming Soon"

## Testing

### Unit Tests Added
File: `apps/ws-wizardsofts-web/tests/unit/bondwala.test.tsx`

**Test Coverage** (9 tests):
1. ✓ Renders coming soon message
2. ✓ Displays dynamic launch date (7 days from mock date)
3. ✓ Shows fallback text when date is not loaded
4. ✓ Renders expected launch date section
5. ✓ Renders BondWala description
6. ✓ Renders Learn More button
7. ✓ Verifies download links are hidden
8. ✓ Renders FAQ section
9. ✓ Renders support section

### Running Tests
```bash
cd apps/ws-wizardsofts-web
npm test -- bondwala.test.tsx
```

## Future Updates

When the app is ready for release:

1. **Update Launch Date**:
   - Change the `useEffect` calculation to a fixed date
   - Or remove dynamic calculation and use a hardcoded date

2. **Enable Download Links**:
   - Uncomment the download section JSX
   - Update Google Play URL to actual app link
   - Update App Store URL to actual app link

3. **Update Hero Section**:
   - Change "Coming Soon" div back to "Download Now" button
   - Point button to #download section

### Example Code for Re-enabling Downloads

```tsx
// Replace static div with download button
<a
  href="#download"
  className="inline-block rounded-md bg-white px-8 py-3 font-semibold text-primary hover:bg-gray-100 transition-colors"
>
  Download Now
</a>

// Uncomment the download links section and update URLs
<div className="mt-8 flex flex-col gap-4 sm:flex-row sm:justify-center">
  <a
    href="https://play.google.com/store/apps/details?id=com.wizardsofts.bondwala"
    target="_blank"
    rel="noopener noreferrer"
    className="inline-block rounded-md bg-primary px-8 py-4 font-semibold text-white hover:bg-primary-600 transition-colors"
  >
    <div className="text-sm text-white/80">Get it on</div>
    <div>Google Play</div>
  </a>
  <a
    href="https://apps.apple.com/app/bondwala/id123456789"
    target="_blank"
    rel="noopener noreferrer"
    className="inline-block rounded-md bg-gray-900 px-8 py-4 font-semibold text-white hover:bg-gray-800 transition-colors"
  >
    <div className="text-sm text-white/80">Download on</div>
    <div>App Store</div>
  </a>
</div>
```

## Deployment

The changes are deployed through the GitLab CI/CD pipeline:

### Build & Test Stage
- Runs `npm install` and `npm run build`
- Executes `npm run lint`
- Runs unit tests including bondwala.test.tsx

### Deploy Stage
- Syncs files to deployment server (10.0.0.84)
- Builds Docker image
- Deploys via Traefik reverse proxy
- Available at: https://www.wizardsofts.com/bondwala

### Health Check
- Verifies website accessibility
- Checks Traefik routing
- Validates Next.js application running

## Contact & Support
- Email: bondwala@wizardsofts.com
- Response time: 24-48 hours

---
**Last Updated**: December 30, 2025
**Version**: 1.0.0
