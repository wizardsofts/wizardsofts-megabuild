# gibd-quant-web Development Guidelines

**Last Updated**: December 30, 2025
**Project**: Guardian Investment Bangladesh - Quant Analysis Platform
**Domain**: https://www.guardianinvestmentbd.com

---

## 🚀 Deployment & Security Rules

**CRITICAL**: This project follows strict deployment and security standards.

### Deployment - CI/CD ONLY

❌ **NEVER**:
- Use SSH to deploy services
- Run docker-compose commands on production
- Bypass CI/CD pipeline for "quick fixes"
- Deploy without running tests

✅ **ALWAYS**:
- Use GitLab CI/CD pipeline for all deployments
- Push code changes to GitLab repository
- Trigger deployments from GitLab UI
- Verify health checks pass
- **Verify HTTPS/SSL certificates after every deployment** (see below)

### Post-Deployment HTTPS Verification

**CRITICAL**: After every deployment, MUST verify HTTPS is working correctly:

```bash
# 1. Check domain certificate
openssl s_client -connect www.guardianinvestmentbd.com:443 -servername www.guardianinvestmentbd.com 2>/dev/null | openssl x509 -noout -dates

# 2. Verify secure connection (should show HTTP/2 200)
curl -I https://www.guardianinvestmentbd.com 2>&1 | head -5

# 3. Test all major routes
curl -sI https://www.guardianinvestmentbd.com/ | grep HTTP
curl -sI https://www.guardianinvestmentbd.com/charts | grep HTTP
curl -sI https://www.guardianinvestmentbd.com/signals | grep HTTP
curl -sI https://www.guardianinvestmentbd.com/multi-criteria | grep HTTP

# 4. Check certificate issuer (should be Let's Encrypt)
openssl s_client -connect www.guardianinvestmentbd.com:443 -servername www.guardianinvestmentbd.com 2>/dev/null | openssl x509 -noout -issuer
```

**If "not secure" warning appears**:
1. Check Traefik Let's Encrypt configuration in `infrastructure/traefik/`
2. Verify DNS: `nslookup www.guardianinvestmentbd.com` should resolve to correct IP
3. Check Traefik logs: `docker logs traefik 2>&1 | grep -i "acme\|certificate\|guardianinvestmentbd"`
4. Verify ports 80/443 accessible for ACME challenge
5. Check Traefik dashboard: http://<server-ip>:8080
6. Force certificate renewal: Delete `infrastructure/traefik/acme.json` and restart Traefik

**See [AGENT_GUIDELINES.md](../../AGENT_GUIDELINES.md#httpsssl-verification-steps) for detailed troubleshooting**

### Port Binding - Via Traefik ONLY

This web application runs on internal port 3000 but MUST NOT be directly accessible:

```yaml
# docker-compose.yml
services:
  frontend:
    ports:
      - "3000:3000"  # Internal port mapping
    networks:
      - microservices-overlay  # ✅ Traefik network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.gibd-quant-web.rule=Host(`www.guardianinvestmentbd.com`)"
      - "traefik.http.routers.gibd-quant-web.entrypoints=websecure"
      - "traefik.http.routers.gibd-quant-web.tls.certresolver=letsencrypt"
```

### Reference Documents

**MUST READ**:
- [CONSTITUTION.md](../../CONSTITUTION.md) - Project standards
- [AGENT_GUIDELINES.md](../../AGENT_GUIDELINES.md) - AI agent rules

---

## 🛠️ Technology Stack

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- **wizwebui** - Component library (`@wizwebui/core`)
- **Recharts** - Financial data visualization (price & volume charts)
- Docker (Production)

## ⛔ UI Component Rules - MANDATORY

**CRITICAL**: This project uses the `wizwebui` component library exclusively.

### Absolute Rules

1. **NEVER create custom UI components** without explicit user approval
2. **ALWAYS use `@wizwebui/core` components**:
   - Button, Input, Card, Table, Tabs, Badge, Select, Checkbox, etc.
3. **BEFORE building ANY component**:
   - Check if wizwebui has it
   - If missing, ASK USER FIRST
   - Wait for approval before proceeding

### If Component Missing from wizwebui

```
STOP and ask:
"wizwebui doesn't have <ComponentName>. Options:
 A) Create generic version and add to wizwebui
 B) Use alternative wizwebui component
 C) Wait for wizwebui update

Which do you prefer?"
```

### Adding Components to wizwebui

If approved to add component:
1. Navigate to `/packages/wizwebui/src/components/`
2. Create generic, reusable version
3. Follow wizwebui patterns (variant, density, theme)
4. Export from `index.ts`
5. Build: `npm run build`
6. Update app dependency

### Acceptable Customizations

- ✅ Theme configuration (`ThemeProvider`)
- ✅ Layout compositions using wizwebui
- ✅ Utility CSS (if essential)
- ❌ Custom Button, Input, Form, etc.

### Violation = Immediate Refactor

**NO EXCEPTIONS**. See root `CLAUDE.md` for details.

## 📁 Project Structure

```
app/
  page.tsx                      # Homepage/Dashboard
  charts/                       # Stock charts
  signals/                      # Trading signals
  multi-criteria/               # Multi-criteria analysis
  chat/                         # AI chat interface
  dashboard/
    dse/
      [ticker]/
        page.tsx                # Parent ticker page (stock header + tabs)
        profile/
          page.tsx              # Redirects to parent
          ProfileContent.tsx    # Company Profile tab content
        holding/
          page.tsx              # Redirects to parent
          HoldingContent.tsx    # Holdings tab content
        news/
          page.tsx              # Redirects to parent
          NewsContent.tsx       # News tab content with filters
components/                     # React components
public/                         # Static assets
```

### Ticker Page Architecture (Next.js 15 Pattern)

**URL Structure**:
- `/dashboard/dse/BATBC` - Parent page with stock header and all tabs
- `/dashboard/dse/BATBC/profile` - Redirects to parent (profile tab)
- `/dashboard/dse/BATBC/holding` - Redirects to parent (holdings tab)
- `/dashboard/dse/BATBC/news` - Redirects to parent (news tab)

**Component Pattern**:
1. **Parent Page** (`/dashboard/dse/[ticker]/page.tsx`):
   - Stock header (company name, trading code, price, status)
   - Tab navigation (8 tabs: Profile, Analysis, Chart, Holdings, etc.)
   - Mobile-responsive with "More" dropdown for overflow tabs
   - Renders content components via `<TabPanel>`

2. **Content Components** (`*Content.tsx`):
   - Contains ONLY the tab content
   - No headers, no navigation
   - Receives `ticker` as prop
   - Uses wizwebui components + Tailwind only

3. **Redirect Pages** (old tab pages):
   - Use Next.js 15 async params pattern
   - Redirect to parent page for backward compatibility

**Next.js 15 Async Params**:
```typescript
// ✅ CORRECT - Next.js 15 pattern
export default async function Page({ params }: PageProps) {
  const { ticker } = await params;
  // use ticker
}

// ❌ WRONG - Synchronous access
export default function Page({ params }: PageProps) {
  redirect(`/path/${params.ticker}`); // Error!
}
```

**Styling Rules**:
- NO inline styles except data visualizations (conic-gradient, percentage heights)
- ALL colors via Tailwind classes (text-gray-900, bg-blue-600, etc.)
- Responsive design with Tailwind breakpoints (sm:, md:, lg:)
- Theme-based using wizwebui + Tailwind only

## 🧪 Development Commands

```bash
# Navigate to project
cd apps/gibd-quant-web

# Install dependencies
npm install

# Run locally
npm run dev

# Run tests
npm test

# Build for production
npm run build

# Lint code
npm run lint
```

## 📋 Testing Requirements

- Unit tests: Required for critical components
- Integration tests: Required for API integrations
- Tests MUST pass before deployment

**E2E Testing Mandate (CRITICAL)**:
- ✅ **All agents MUST run and pass relevant end-to-end/integration tests** before proceeding to next phase
- ✅ **For features involving backend integration**: Test complete workflow from UI → API → response
- ⚠️ **If tests fail or cannot run**: Development MUST pause, report to user
- 📝 **Document**: Test results, skipped tests (with reasons), any infrastructure issues
- 🚩 **Raise flags**: Business requirement conflicts, API integration issues, deployment blockers

**Example E2E Test Flow**:
```bash
# Run integration tests
npm test

# Test with actual backend services (if available)
npm run test:e2e

# Verify:
# - Component rendering
# - API calls succeed
# - Data displays correctly
# - Error handling works
```

## 🌐 Backend Services Integration

This frontend connects to:
- gibd-quant-signal (Port 5001) - Signal generation
- gibd-quant-nlq (Port 5002) - Natural language queries
- gibd-quant-calibration (Port 5003) - Model calibration
- gibd-quant-agent (Port 5004) - AI agent services

## Recent Changes

- January 6, 2026: Enhanced chart tooltip to display indicator values on hover
  - Updated PriceTooltip component to show active indicator values
  - Added special handling for Bollinger Bands (displays upper/middle/lower band values)
  - Other indicators (SMA, EMA, RSI, MACD) display single calculated value
  - Indicator values color-coded to match their chart line colors
  - Indicator values appear below OHLC data with visual separator
  - Updated `/dashboard/dse/[ticker]/chart/page.tsx` to render CompanyChart component
  - Tested with multiple active indicators (SMA, EMA, BB) - all values display correctly
  - Commit: `252fc3f` feat: Enhance chart tooltip to display indicator values on hover
- January 6, 2026: Implemented multi-indicator support with customizable parameters
  - Users can add/remove multiple indicators dynamically (no limit)
  - Each indicator type + parameter combination creates unique instance (SMA 9, SMA 20, SMA 50 all at once)
  - Inline form (not modal) for indicator configuration with dynamic parameter inputs
  - Supported indicators: SMA, EMA, Bollinger Bands, RSI, MACD with customizable parameters
  - SMA/EMA: Period parameter (e.g., 9, 12, 20, 50)
  - Bollinger Bands: Period + Std Dev (e.g., 20/2, 10/3)
  - MACD: Fast, Slow, Signal periods (e.g., 12/26/9)
  - Color-coded indicator badges showing type and parameters
  - Indicator calculations from OHLCV data in frontend (no backend dependency)
  - Chart legend automatically updates with all active indicators
  - Commit: `3a03f26` feat: Implement multi-indicator support with customizable parameters
- January 5, 2026: Added technical indicator selection to CompanyChart
  - Indicator dropdown with 6 options: None, SMA(20), SMA(50), EMA(20), Bollinger Bands, All
  - Implemented indicator calculations: SMA, EMA, Bollinger Bands (20-period, 2 std dev)
  - Color-coded overlays: SMA(20) green, SMA(50) amber, EMA(20) purple, BB red/gray
  - Responsive layout: Period buttons + indicator dropdown stack on mobile
  - Commit: `1b6ef53` feat: Add technical indicator selection to CompanyChart
- January 5, 2026: Added mock data fallback for CompanyChart
  - Generate realistic price/volume data when backend API unavailable
  - Mock data adapts to selected period (1D = 78 points, 1M = 30 points, etc.)
  - "Demo Data" badge shows when using mock data
  - Graceful degradation: chart always displays functional UI
  - Commit: `9515b5b` feat: Add mock data fallback for CompanyChart when API unavailable
- January 5, 2026: Integrated CompanyChart into dashboard ticker page Chart tab
  - Replaced "Chart - Coming Soon" placeholder with functional CompanyChart component
  - Chart displays period selector (1D, 5D, 1M, 3M, 6M, YTD, 1Y, 5Y, MAX)
  - Recharts-based price line chart and volume bar chart
  - Proper error handling when backend API unavailable
  - Created test page at /test-chart with mock data to demonstrate chart functionality
  - Verified with Playwright browser automation - chart renders correctly
  - Commit: `9999d52` feat: Integrate CompanyChart into dashboard ticker page
- January 5, 2026: Completed test automation for ticker page architecture
  - Created comprehensive test report: [TEST_RESULTS.md](TEST_RESULTS.md)
  - Tested tab navigation (Profile, Holdings, News) - ✅ All passing
  - Tested news filter functionality (Source, Category, Year multi-select) - ✅ All passing
  - Tested mobile responsive features (More dropdown, click-outside handler) - ✅ All passing
  - Applied scrollbar layout shift fix (scrollbar-gutter + overflow-y fallback)
  - Fixed wizwebui package path (../../../../ → ../../../ relative path)
  - 10/10 test cases passed using Playwright MCP browser automation
- January 5, 2026: Implemented News tab with comprehensive filtering
  - Created NewsContent component with three-column layout (filters, articles, quick access)
  - Left filter sidebar: Source, Category, Year filters with multi-select checkboxes
  - Real-time filtering with article count display
  - Mock data includes 7 news articles, 4 corporate actions, 3 upcoming events
  - Quick access panel with AGM/EGM notices, annual reports, dividend history
  - Converted news/page.tsx to redirect pattern (Next.js 15 async params)
  - 100% wizwebui components + Tailwind classes, no inline styles
- January 5, 2026: Restructured ticker pages to eliminate duplication (~800 lines removed)
  - Created parent page at `/dashboard/dse/[ticker]` with shared stock header and tabs
  - Extracted ProfileContent and HoldingContent as tab-only components
  - Converted profile and holding pages to redirects for backward compatibility
  - Fixed Next.js 15 async params in redirect pages
  - Removed all inline styles except data visualizations
  - All UI styling now theme-based using wizwebui + Tailwind only
- January 5, 2026: Implemented mobile-responsive design with burger menu navigation
- January 5, 2026: Migrated Holdings page to wizwebui components
- January 5, 2026: Implemented Company Profile page with three-column layout
- January 5, 2026: Fixed wizwebui component bugs (Table, Card, Badge, Tabs)
- January 5, 2026: Removed Summary tab, made Company Profile the default tab
- December 30, 2025: Deployed to production via CI/CD
- December 30, 2025: Added HTTPS verification guidelines
- December 30, 2025: Fixed coming-soon directory permissions

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
