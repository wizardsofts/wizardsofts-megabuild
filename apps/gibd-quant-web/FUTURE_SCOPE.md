# GIBD Quant Web - Future Scope & Roadmap

**Application:** Guardian Investment BD - Web Platform
**Stack:** Next.js 15, React 18, TypeScript, wizwebui, Tailwind CSS
**Last Updated:** 2026-01-05

---

## Table of Contents

1. [Stock Chart Implementation](#stock-chart-implementation)
2. [DivinerReturns Dashboard](#divinerreturns-dashboard)
3. [Portfolio Analytics](#portfolio-analytics)
4. [Social Trading Features](#social-trading-features)
5. [Mobile Optimization](#mobile-optimization)
6. [Performance & UX](#performance--ux)
7. [Implementation Timeline](#implementation-timeline)

---

## Stock Chart Implementation

**Status:** 📋 Planned | **Priority:** ⭐⭐⭐⭐⭐ Critical
**Research:** [docs/CHART_LIBRARY_RESEARCH.md](docs/CHART_LIBRARY_RESEARCH.md)

### Selected Library: TradingView Lightweight Charts

**Rationale:**
- Free & open source (Apache 2.0)
- Best performance (~50KB gzipped)
- Professional-grade candlestick charts
- Active maintenance by TradingView
- React wrapper available

### Implementation Phases

#### Phase 1: Basic Candlestick Chart (Week 1)
```bash
npm install lightweight-charts lightweight-charts-react-wrapper
```

**Features:**
- [ ] Candlestick/OHLC chart component
- [ ] Time period selector (1H, 4H, 1D, 1W, 1M)
- [ ] Volume chart below main chart
- [ ] Responsive design (mobile + desktop)
- [ ] Integration with ticker page Chart tab

**Target:** `/dashboard/dse/[ticker]` → Chart tab

**Mockup Reference:** Provided screenshot showing time period buttons + candlestick chart

#### Phase 2: Technical Indicators (Week 2)
```bash
npm install ta-lib  # Or ta.js for technical analysis
```

**Indicators to Implement:**
- [ ] Exponential Moving Average (EMA 20, 50, 200)
- [ ] Bollinger Bands
- [ ] Keltner Index
- [ ] Relative Strength Index (RSI)
- [ ] MACD (Moving Average Convergence Divergence)
- [ ] Stochastic Oscillator

**Implementation:**
- Calculate indicators server-side or client-side
- Overlay as line series on candlestick chart
- Toggle indicators via UI controls
- Color-coded legend

#### Phase 3: Drawing Tools (Week 3)

**Features:**
- [ ] Trendline drawing
- [ ] Horizontal/vertical lines (support/resistance)
- [ ] Fibonacci retracements
- [ ] Rectangle annotations
- [ ] Text labels

**Implementation:**
- Use `lightweight-charts-drawing-tools` plugin
- Or custom implementation with markers/price lines API
- Save drawings to localStorage or backend

#### Phase 4: Advanced Features (Week 4)

**Features:**
- [ ] Multiple chart types (Candlestick, Line, Area, Heiken Ashi)
- [ ] Chart comparison (overlay multiple stocks)
- [ ] Screenshot/export functionality
- [ ] Real-time price updates (WebSocket)
- [ ] Alerts based on price levels or indicators

**Integration:**
- Connect to existing FastAPI backend for historical data
- WebSocket for real-time updates
- Save user preferences (indicators, drawings)

### Technical Specifications

**Data Format:**
```typescript
interface CandlestickData {
  time: string; // ISO 8601 or Unix timestamp
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}
```

**API Endpoints (Existing/New):**
- `GET /api/stocks/{ticker}/ohlc?period=1D&start=YYYY-MM-DD&end=YYYY-MM-DD`
- `GET /api/stocks/{ticker}/indicators?type=EMA&period=20`
- `WS /ws/stocks/{ticker}/realtime` (future)

**Component Structure:**
```
app/dashboard/dse/[ticker]/chart/
  ├── ChartContent.tsx          # Main chart tab content
  ├── StockChart.tsx            # Lightweight Charts wrapper
  ├── TimePeriodSelector.tsx    # 1H, 4H, 1D, 1W, 1M buttons
  ├── IndicatorSelector.tsx     # Dropdown to add/remove indicators
  ├── DrawingTools.tsx          # Toolbar for drawing
  └── ChartSettings.tsx         # Chart type, colors, preferences
```

---

## DivinerReturns Dashboard

**Status:** 🟡 Planning | **Priority:** ⭐⭐⭐⭐⭐ Critical
**Backend:** ✅ API Ready | **Frontend:** 🔴 Not Started

### Overview

DivinerReturns is a quantile regression model predicting 1-5 day stock returns with confidence intervals for 247 DSE stocks. The backend API is production-ready and needs user-facing dashboard.

**API Endpoints (Deployed):**
- `POST /api/predict/returns` - Single stock prediction
- `POST /api/predict/returns/batch` - Multiple stocks (screener)

### Features to Implement

#### 1. Stock Screener (Phase 1 - Q1 2026)

**Timeline:** 2-4 weeks

**Layout:** Full-page table with filters

**Columns:**
- Ticker
- Current Price
- 1-Day Prediction (10th/50th/90th percentile)
- 3-Day Prediction
- 5-Day Prediction
- Confidence Score
- Risk Level (Low/Medium/High)

**Filters:**
- Prediction range (e.g., returns > 5%)
- Confidence level (> 70%)
- Risk tolerance (Low/Medium/High)
- Sector (Food & Allied, Banking, Pharma, etc.)
- Market cap range

**Sorting:**
- By predicted return (highest first)
- By confidence (most confident)
- By current price

**Actions:**
- Click ticker → Navigate to `/dashboard/dse/{ticker}`
- Add to watchlist
- Export to CSV/PDF

**Example Mock:**
```
┌─────────┬────────┬─────────────────────┬─────────────────────┬─────────────────────┬────────────┬──────────┐
│ Ticker  │ Price  │ 1-Day Return        │ 3-Day Return        │ 5-Day Return        │ Confidence │ Risk     │
├─────────┼────────┼─────────────────────┼─────────────────────┼─────────────────────┼────────────┼──────────┤
│ BATBC   │ 248.60 │ +2.3% (1.5%-3.2%)   │ +5.1% (3.2%-7.4%)   │ +8.2% (5.1%-11.5%)  │ 78%        │ Low      │
│ SQURPHARMA │ 125.30 │ +1.8% (0.9%-2.5%) │ +3.5% (1.8%-5.2%)   │ +4.9% (2.5%-7.8%)   │ 72%        │ Medium   │
└─────────┴────────┴─────────────────────┴─────────────────────┴─────────────────────┴────────────┴──────────┘
```

**Implementation:**
```typescript
// app/dashboard/screener/page.tsx
import { Table } from '@wizwebui/core';

interface Prediction {
  ticker: string;
  current_price: number;
  predictions_1d: { p10: number; p50: number; p90: number };
  predictions_3d: { p10: number; p50: number; p90: number };
  predictions_5d: { p10: number; p50: number; p90: number };
  confidence: number;
  risk_level: 'Low' | 'Medium' | 'High';
}

export default async function ScreenerPage() {
  const predictions = await fetch('/api/predict/returns/batch', {
    method: 'POST',
    body: JSON.stringify({ tickers: allDSEStocks }),
  });

  return <ScreenerTable data={predictions} />;
}
```

#### 2. Individual Stock Prediction View (Phase 1 - Q1 2026)

**Timeline:** 1 week

**Location:** `/dashboard/dse/[ticker]` → New "Predictions" tab

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│ BATBC Price Predictions                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Current Price: 248.60 BDT                                   │
│  Last Updated: 2026-01-05 14:30 UTC                         │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Prediction Horizon                                   │  │
│  │  ○ 1 Day  ○ 2 Days  ● 3 Days  ○ 4 Days  ○ 5 Days    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │      Confidence Interval (3-Day Prediction)           │  │
│  │                                                        │  │
│  │  10th Percentile: 252.30 BDT (+1.5%)                  │  │
│  │  50th Percentile: 260.80 BDT (+4.9%) ← Most Likely    │  │
│  │  90th Percentile: 271.20 BDT (+9.1%)                  │  │
│  │                                                        │  │
│  │  [============================|=========]             │  │
│  │  Low                       Median      High           │  │
│  │                                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Risk Assessment: Medium                                     │
│  Confidence Score: 75%                                       │
│  Model Version: v2.1.0 (2026-01-01)                         │
│                                                              │
│  [Add to Watchlist]  [Set Alert]  [View Backtest]          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- [ ] Visual confidence interval bar chart
- [ ] Prediction horizon selector (1-5 days)
- [ ] Predicted price vs. current price comparison
- [ ] Risk level indicator (color-coded)
- [ ] Confidence score badge
- [ ] Historical accuracy chart (how accurate were past predictions?)

#### 3. Prediction Tracking & Transparency (Phase 2 - Q1 2026)

**Timeline:** 1-2 weeks

**Features:**
- [ ] Track prediction accuracy over time
- [ ] Display past predictions vs. actual outcomes
- [ ] "How accurate was our 3-day prediction from last week?" widget
- [ ] Prediction error metrics (RMSE, MAE)
- [ ] Coverage statistics (% of actual prices within confidence interval)

**Example:**
```
Prediction Accuracy (Last 30 Days)
┌─────────────────────────────────────────┐
│ Horizon │ RMSE  │ Coverage │ Avg Error │
├─────────┼───────┼──────────┼───────────┤
│ 1 Day   │ 2.3%  │ 78%      │ 1.8%      │
│ 3 Days  │ 4.1%  │ 76%      │ 3.2%      │
│ 5 Days  │ 5.5%  │ 75%      │ 4.5%      │
└─────────┴───────┴──────────┴───────────┘
```

#### 4. Mobile Push Notifications (Phase 2 - Q1 2026)

**Timeline:** 1-2 weeks

**Features:**
- [ ] Daily prediction updates for watchlist stocks
- [ ] Alert when predicted return crosses threshold (e.g., > 5%)
- [ ] Price target alerts (when predicted price matches user-set target)
- [ ] Risk level change notifications

**Implementation:**
- Use Firebase Cloud Messaging (FCM) or OneSignal
- Backend Celery task for daily predictions
- User preferences for notification frequency

---

## Portfolio Analytics

**Status:** 🔴 Not Started | **Priority:** ⭐⭐⭐⭐ High
**Depends On:** DivinerReturns Dashboard, TARP-DRL completion

### Features

#### 1. Portfolio Risk Analyzer (Phase 2 - Q2 2026)

**Timeline:** 3-4 weeks

**Features:**
- [ ] Upload portfolio (CSV or manual entry)
- [ ] Portfolio risk score (VaR, CVaR, volatility)
- [ ] Diversification analysis (sector exposure, concentration risk)
- [ ] Predicted portfolio return over 1-5 days
- [ ] Rebalancing suggestions based on DivinerReturns predictions

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ My Portfolio                                                 │
├─────────────────────────────────────────────────────────────┤
│  Total Value: 1,250,000 BDT                                  │
│  Number of Holdings: 8                                       │
│  Risk Score: Medium (6/10)                                   │
│                                                              │
│  ┌─────────────────────────────────────────┐                │
│  │ Holdings                                │                │
│  ├───────────┬─────────┬──────┬───────────┤                │
│  │ Ticker    │ Shares  │ Value│ Weight    │                │
│  ├───────────┼─────────┼──────┼───────────┤                │
│  │ BATBC     │ 500     │ 124K │ 9.9%      │                │
│  │ SQURPHARMA│ 1000    │ 125K │ 10.0%     │                │
│  │ ...       │ ...     │ ...  │ ...       │                │
│  └───────────┴─────────┴──────┴───────────┘                │
│                                                              │
│  ┌─────────────────────────────────────────┐                │
│  │ Sector Exposure                         │                │
│  │ [=====] Banking 25%                     │                │
│  │ [====] Pharma 20%                       │                │
│  │ [===] Food & Allied 15%                 │                │
│  │ [==] Telecom 10%                        │                │
│  │ [======] Others 30%                     │                │
│  └─────────────────────────────────────────┘                │
│                                                              │
│  Predicted 5-Day Portfolio Return: +4.2% (+/- 2.1%)         │
│  Suggested Rebalancing: Sell 100 BATBC, Buy 50 SQURPHARMA   │
│                                                              │
│  [Rebalance Portfolio]  [Export Report]                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 2. Paper Trading Mode (Phase 3 - Q3 2026)

**Timeline:** 4-6 weeks

**Features:**
- [ ] Virtual trading with real DSE prices
- [ ] Track performance vs. benchmarks (DSEX, DSES)
- [ ] Commission simulation (0.5% buy/sell)
- [ ] Trading journal (notes on trades)
- [ ] Leaderboard (compare with other users)

---

## Social Trading Features

**Status:** 🔴 Not Started | **Priority:** ⭐⭐⭐ Medium

### Features

- [ ] User profiles (bio, trading stats, followers)
- [ ] Follow other traders
- [ ] Share trading ideas (ticker + thesis)
- [ ] Comment system on stocks
- [ ] Top traders leaderboard (by returns, Sharpe ratio)
- [ ] Copy trading (auto-replicate trades from followed users)

**Privacy:** Users can choose to make portfolio public/private

---

## Mobile Optimization

**Status:** ✅ In Progress | **Priority:** ⭐⭐⭐⭐ High

### Completed
- ✅ Mobile responsive ticker page with tabs
- ✅ "More" dropdown for additional tabs on mobile
- ✅ Click-outside handler to close dropdown
- ✅ Scrollbar layout shift fix (no page bounce)

### Future Enhancements
- [ ] Progressive Web App (PWA) support
- [ ] Add to Home Screen prompt
- [ ] Offline mode (cache stock data)
- [ ] Touch gestures for chart (pinch to zoom, swipe to pan)
- [ ] Native mobile app (React Native) - Q2 2026

---

## Performance & UX

**Status:** 🟢 Ongoing | **Priority:** ⭐⭐⭐⭐ High

### Performance Optimizations

- [ ] **Image Optimization:** Use Next.js `<Image>` component with lazy loading
- [ ] **Code Splitting:** Dynamic imports for large components (chart library)
- [ ] **API Caching:** Implement SWR or React Query for data fetching
- [ ] **Server-Side Rendering (SSR):** Pre-render critical pages for SEO
- [ ] **Static Site Generation (SSG):** Generate static pages for stock listings

### UX Improvements

- [ ] **Loading States:** Skeleton loaders instead of spinners
- [ ] **Error Handling:** User-friendly error messages with retry options
- [ ] **Empty States:** Helpful messages when no data available
- [ ] **Accessibility (a11y):** WCAG 2.1 AA compliance
  - Keyboard navigation
  - ARIA labels
  - Screen reader support
  - Color contrast ratios

### Testing

- [ ] **E2E Testing:** Playwright tests for critical user flows
- [ ] **Unit Testing:** Jest/Vitest for components and utilities
- [ ] **Visual Regression:** Screenshot comparison for UI changes
- [ ] **Performance Testing:** Lighthouse CI in pipeline

**Current Status:** ✅ Test automation completed for ticker page (10/10 tests passing)

---

## Implementation Timeline

### Q1 2026 (Jan-Mar) - Foundation

**Week 1-2: Chart Implementation**
- [ ] Phase 1: Basic candlestick chart with time periods
- [ ] Phase 2: Technical indicators (EMA, Bollinger, Keltner)

**Week 3-4: DivinerReturns Screener**
- [ ] Stock screener with filters
- [ ] Batch prediction API integration
- [ ] Export functionality

**Week 5-6: Individual Predictions**
- [ ] Predictions tab in ticker page
- [ ] Confidence interval visualization
- [ ] Risk assessment display

**Week 7-8: Prediction Tracking**
- [ ] Historical accuracy charts
- [ ] Transparency metrics
- [ ] Mobile push notifications setup

### Q2 2026 (Apr-Jun) - Analytics & Social

**Week 1-4: Portfolio Analytics**
- [ ] Portfolio risk analyzer
- [ ] Sector exposure charts
- [ ] Rebalancing suggestions

**Week 5-8: Social Trading MVP**
- [ ] User profiles
- [ ] Follow system
- [ ] Trading ideas feed

**Week 9-12: Mobile App**
- [ ] React Native app (iOS + Android)
- [ ] Push notifications
- [ ] Offline mode

### Q3 2026 (Jul-Sep) - Advanced Features

**Week 1-6: Paper Trading**
- [ ] Virtual trading platform
- [ ] Performance tracking
- [ ] Leaderboard

**Week 7-12: Chart Advanced Features**
- [ ] Drawing tools
- [ ] Chart comparison
- [ ] Real-time updates (WebSocket)

### Q4 2026 (Oct-Dec) - Scale & Polish

- [ ] Performance optimization
- [ ] A/B testing framework
- [ ] Premium subscription features
- [ ] Auto-trading integration (if regulatory approval obtained)

---

## Success Metrics

### User Engagement
- Daily Active Users (DAU)
- Average session duration
- Page views per session
- Bounce rate < 40%

### Feature Adoption
- % users using stock screener
- % users with portfolios tracked
- % users following predictions
- % users with active alerts

### Business Metrics
- Conversion to premium (target: 5% of MAU)
- Average Revenue Per User (ARPU)
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)

---

## Tech Debt & Maintenance

### Current Known Issues
- ⚠️ Console warnings in SignalCard.tsx (missing formatDate, formatPercent, formatCurrency exports)
- ⚠️ wizwebui package uses local file reference (may break in CI/CD)

### Future Maintenance Tasks
- [ ] Upgrade to Next.js 16 when stable
- [ ] Migrate to App Router completely (if not already)
- [ ] Update wizwebui to published npm package
- [ ] Replace mock data with real API calls
- [ ] Add comprehensive error boundaries

---

## Documentation

### Existing Docs
- [CHART_LIBRARY_RESEARCH.md](docs/CHART_LIBRARY_RESEARCH.md) - Chart library comparison
- [TEST_RESULTS.md](TEST_RESULTS.md) - Test automation report
- [CLAUDE.md](CLAUDE.md) - Development guidelines
- [MOBILE_RESPONSIVE_IMPLEMENTATION.md](docs/MOBILE_RESPONSIVE_IMPLEMENTATION.md)
- [WIZWEBUI_INTEGRATION_ISSUES.md](docs/WIZWEBUI_INTEGRATION_ISSUES.md)

### Docs to Create
- [ ] API Integration Guide (how to connect to backend services)
- [ ] Deployment Guide (production deployment checklist)
- [ ] Component Library Documentation (wizwebui usage examples)
- [ ] Performance Best Practices
- [ ] Security Guidelines (XSS, CSRF, input validation)

---

## Contributing

**Process:**
1. Create feature branch from `master`
2. Implement feature following [CLAUDE.md](CLAUDE.md) guidelines
3. Write tests (unit + E2E)
4. Create merge request with detailed description
5. Pass CI/CD pipeline (linting, tests, security scans)
6. Code review approval required
7. Merge to `master`

**Coding Standards:**
- 100% wizwebui components (no custom UI libraries)
- 100% Tailwind CSS (no inline styles except data visualizations)
- TypeScript strict mode enabled
- Next.js 15 async params pattern
- Responsive design (mobile-first)

---

**Document Maintainer:** GIBD Quant Team
**Review Frequency:** Monthly
**Next Review:** 2026-02-01
**Parent Roadmap:** [../../FUTURE_SCOPE.md](../../FUTURE_SCOPE.md)
