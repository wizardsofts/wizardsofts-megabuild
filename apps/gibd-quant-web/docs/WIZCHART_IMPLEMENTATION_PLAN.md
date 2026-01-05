# wizchart - Custom Financial Charting Library

**Package:** `@wizardsofts/wizchart`
**Repository:** `/Users/mashfiqurrahman/Workspace/wizardsofts/wizchart`
**Base:** Fork of react-financial-charts with enhancements
**Strategy:** In-house library development (similar to wizwebui)

**Created:** 2026-01-05
**Status:** Phase 0 Complete ✅ - Ready for Phase 1

---

## Table of Contents

1. [Vision & Strategy](#vision--strategy)
2. [Feature Superset](#feature-superset)
3. [Phase-Wise Implementation](#phase-wise-implementation)
4. [Library Architecture](#library-architecture)
5. [Setup & Cloning](#setup--cloning)
6. [Development Workflow](#development-workflow)
7. [Publishing Strategy](#publishing-strategy)

---

## Vision & Strategy

### Why Build Our Own?

**Problems with External Libraries:**
- ❌ TradingView Lightweight Charts: Limited indicators, requires custom implementation
- ❌ Highcharts Stock: Expensive licensing ($490-10K/year), vendor lock-in
- ❌ ApexCharts: Not financial-focused, limited indicators
- ❌ react-financial-charts: Smaller community, limited maintenance

**Benefits of wizchart:**
- ✅ **Full Control:** Customize every feature to our exact needs
- ✅ **Cost Savings:** No licensing fees, no recurring costs
- ✅ **Integration:** Seamless integration with wizwebui design system
- ✅ **Performance:** Optimize specifically for DSE stocks and our data patterns
- ✅ **Knowledge:** Deep expertise in financial charting for future products
- ✅ **IP Asset:** Valuable intellectual property for WizardSofts

### Strategic Approach

**Phase 0:** Fork react-financial-charts as base (30 indicators, React-first)
**Phase 1-4:** Add features from all researched libraries (superset)
**Phase 5+:** Innovate beyond existing libraries (AI-powered features)

---

## Feature Superset

Comprehensive feature list combining best features from all researched libraries:
- TradingView Lightweight Charts
- Highcharts Stock
- ApexCharts
- react-financial-charts
- Syncfusion
- Plotly.js
- amCharts
- D3.js

### 1. Chart Types

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Candlestick** | All | ⭐⭐⭐⭐⭐ | Base |
| **OHLC (Open-High-Low-Close)** | All | ⭐⭐⭐⭐⭐ | Base |
| **Line Chart** | All | ⭐⭐⭐⭐⭐ | Base |
| **Area Chart** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Heiken Ashi** | Highcharts, Syncfusion | ⭐⭐⭐⭐ | Phase 2 |
| **Renko** | Highcharts, Syncfusion | ⭐⭐⭐ | Phase 3 |
| **Kagi** | Highcharts | ⭐⭐⭐ | Phase 3 |
| **Point & Figure** | Highcharts | ⭐⭐⭐ | Phase 3 |
| **Volume Chart** | All | ⭐⭐⭐⭐⭐ | Base |
| **Volume Profile** | TradingView, Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Histogram** | All | ⭐⭐⭐⭐ | Base |
| **Baseline** | TradingView | ⭐⭐⭐ | Phase 2 |

### 2. Technical Indicators (90+ Total)

#### Base Indicators (react-financial-charts - 30 indicators) ✅ Included
- Moving Averages (SMA, EMA, WMA)
- Bollinger Bands
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- Stochastic Oscillator
- ATR (Average True Range)
- SAR (Parabolic SAR)
- Force Index
- Elder Ray
- TRIX
- And 20 more...

#### Phase 1: Essential Indicators (20 indicators)
| Indicator | Source | Use Case |
|-----------|--------|----------|
| **Keltner Channels** | Highcharts | Volatility bands |
| **Ichimoku Cloud** | Highcharts, Syncfusion | Trend & support/resistance |
| **ADX (Average Directional Index)** | Highcharts | Trend strength |
| **CCI (Commodity Channel Index)** | Highcharts | Overbought/oversold |
| **Williams %R** | Highcharts | Momentum |
| **OBV (On-Balance Volume)** | Highcharts | Volume-price trend |
| **Aroon Indicator** | Highcharts | Trend identification |
| **Chaikin Money Flow** | Highcharts | Buy/sell pressure |
| **MFI (Money Flow Index)** | Highcharts | Volume-weighted RSI |
| **Pivot Points** | Highcharts | Support/resistance levels |
| **Fibonacci Retracement (Dynamic)** | Highcharts | Auto-calculated levels |
| **VWAP (Volume Weighted Avg Price)** | TradingView | Intraday benchmark |
| **Supertrend** | Custom | Trend following |
| **Donchian Channels** | Highcharts | Breakout indicator |
| **Standard Deviation** | Highcharts | Volatility |
| **Linear Regression** | Highcharts | Trend line |
| **Price Channel** | Highcharts | Support/resistance |
| **Momentum** | Highcharts | Rate of price change |
| **ROC (Rate of Change)** | Highcharts | Momentum |
| **EMA Cross (5/10/20)** | Custom | Signal generator |

#### Phase 2: Advanced Indicators (20 indicators)
- Elliott Wave
- Gann Fan
- Andrews' Pitchfork
- Zig Zag
- Hurst Exponent
- Volume Oscillator
- Ease of Movement
- Commodity Selection Index
- Detrended Price Oscillator
- Know Sure Thing (KST)
- Plus 10 more specialized indicators

#### Phase 3: Custom DSE-Specific Indicators (20 indicators)
- Circuit Breaker Levels (DSE ±10%)
- Market Breadth (Advancing/Declining ratio)
- Sector Rotation Index
- IPO Performance Tracker
- Block Deal Detection
- Institutional Activity Index
- News Sentiment Overlay
- Plus 13 more Bangladesh-specific

### 3. Drawing Tools

| Tool | Source | Priority | Phase |
|------|--------|----------|-------|
| **Trendline** | All | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Horizontal Line** | All | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Vertical Line** | All | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Rectangle** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Fibonacci Retracement** | Highcharts, TradingView | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Fibonacci Extension** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Fibonacci Fan** | Highcharts | ⭐⭐⭐ | Phase 2 |
| **Fibonacci Time Zones** | Highcharts | ⭐⭐⭐ | Phase 3 |
| **Gann Fan** | Highcharts | ⭐⭐⭐ | Phase 3 |
| **Andrews' Pitchfork** | Highcharts | ⭐⭐⭐ | Phase 3 |
| **Ellipse** | Highcharts | ⭐⭐⭐ | Phase 2 |
| **Text Annotation** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Arrow** | Highcharts | ⭐⭐⭐⭐ | Phase 1 |
| **Callout** | Highcharts | ⭐⭐⭐ | Phase 2 |
| **Measure Tool** | TradingView | ⭐⭐⭐⭐ | Phase 2 |
| **Brush Tool** | Custom | ⭐⭐⭐ | Phase 3 |
| **Eraser** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Drawing Layers** | Custom | ⭐⭐⭐ | Phase 2 |
| **Drawing Locking** | Custom | ⭐⭐⭐ | Phase 2 |
| **Copy/Paste Drawings** | Custom | ⭐⭐⭐⭐ | Phase 2 |

### 4. Interactivity & UX

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Zoom (Pinch/Mouse Wheel)** | All | ⭐⭐⭐⭐⭐ | Base |
| **Pan (Drag)** | All | ⭐⭐⭐⭐⭐ | Base |
| **Crosshair** | All | ⭐⭐⭐⭐⭐ | Base |
| **Tooltip (Hover)** | All | ⭐⭐⭐⭐⭐ | Base |
| **Range Selector** | Highcharts | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Time Period Buttons (1H, 4H, 1D, 1W, 1M)** | Custom | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Auto-scaling** | All | ⭐⭐⭐⭐⭐ | Base |
| **Price Scaling (Linear/Log)** | Highcharts, TradingView | ⭐⭐⭐⭐ | Phase 1 |
| **Volume Scaling** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Multi-pane Layout** | react-financial | ⭐⭐⭐⭐⭐ | Base |
| **Synchronized Charts** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Chart Comparison (Overlay)** | Highcharts, TradingView | ⭐⭐⭐⭐ | Phase 2 |
| **Full Screen Mode** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Dark/Light Theme Toggle** | All | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Touch Gestures (Mobile)** | All | ⭐⭐⭐⭐⭐ | Base |
| **Keyboard Shortcuts** | TradingView | ⭐⭐⭐⭐ | Phase 2 |
| **Context Menu (Right-Click)** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Undo/Redo** | Custom | ⭐⭐⭐⭐ | Phase 2 |

### 5. Data & Real-Time Features

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Historical Data Loading** | All | ⭐⭐⭐⭐⭐ | Base |
| **Lazy Loading (Infinite Scroll)** | Custom | ⭐⭐⭐⭐ | Phase 1 |
| **Real-Time Updates (WebSocket)** | Highcharts, TradingView | ⭐⭐⭐⭐⭐ | Phase 3 |
| **Data Gaps Handling** | Highcharts | ⭐⭐⭐⭐ | Phase 1 |
| **Missing Data Interpolation** | Plotly | ⭐⭐⭐ | Phase 2 |
| **Data Grouping** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Aggregation (OHLC from ticks)** | Custom | ⭐⭐⭐⭐ | Phase 2 |
| **Time Zone Support** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Trading Hours Highlighting** | TradingView | ⭐⭐⭐⭐ | Phase 2 |
| **Session Breaks** | TradingView | ⭐⭐⭐ | Phase 3 |
| **Replay Mode (Historical)** | Custom | ⭐⭐⭐ | Phase 4 |

### 6. Export & Sharing

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Export PNG** | All | ⭐⭐⭐⭐⭐ | Phase 1 |
| **Export JPG** | All | ⭐⭐⭐⭐ | Phase 1 |
| **Export SVG** | Highcharts, D3 | ⭐⭐⭐⭐ | Phase 1 |
| **Export PDF** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **Export CSV** | Highcharts | ⭐⭐⭐⭐ | Phase 1 |
| **Copy to Clipboard (Image)** | Custom | ⭐⭐⭐⭐ | Phase 2 |
| **Share Chart URL** | Custom | ⭐⭐⭐⭐ | Phase 2 |
| **Embed Code** | Custom | ⭐⭐⭐ | Phase 3 |
| **Print** | Highcharts | ⭐⭐⭐ | Phase 2 |

### 7. Alerts & Notifications

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Price Alerts** | TradingView | ⭐⭐⭐⭐⭐ | Phase 3 |
| **Indicator Alerts (RSI cross, etc.)** | TradingView | ⭐⭐⭐⭐ | Phase 3 |
| **Volume Spike Alerts** | Custom | ⭐⭐⭐⭐ | Phase 3 |
| **Pattern Detection (Head & Shoulders, etc.)** | Custom | ⭐⭐⭐ | Phase 4 |
| **Drawing Tool Alerts (Price crosses trendline)** | Custom | ⭐⭐⭐ | Phase 4 |

### 8. AI/ML Features (Innovation)

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Auto Support/Resistance Detection** | Custom AI | ⭐⭐⭐⭐ | Phase 4 |
| **Pattern Recognition** | Custom AI | ⭐⭐⭐⭐ | Phase 4 |
| **Trend Prediction Overlay** | Custom (DivinerReturns) | ⭐⭐⭐⭐⭐ | Phase 4 |
| **Anomaly Detection** | Custom AI | ⭐⭐⭐ | Phase 5 |
| **Similar Chart Finder** | Custom AI | ⭐⭐⭐ | Phase 5 |
| **News Sentiment Overlay** | Custom (GIBD News) | ⭐⭐⭐⭐ | Phase 4 |

### 9. Performance Optimizations

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Canvas Rendering** | TradingView, Highcharts | ⭐⭐⭐⭐⭐ | Base |
| **WebGL Rendering (>1M points)** | Plotly | ⭐⭐⭐ | Phase 3 |
| **Data Decimation** | Highcharts | ⭐⭐⭐⭐ | Phase 1 |
| **Virtual Scrolling** | Custom | ⭐⭐⭐⭐ | Phase 2 |
| **Worker Thread Calculations** | Custom | ⭐⭐⭐ | Phase 3 |
| **Progressive Rendering** | Custom | ⭐⭐⭐ | Phase 2 |
| **Memoization** | React | ⭐⭐⭐⭐ | Base |

### 10. Accessibility

| Feature | Source | Priority | Phase |
|---------|--------|----------|-------|
| **Keyboard Navigation** | All | ⭐⭐⭐⭐ | Phase 2 |
| **Screen Reader Support** | Highcharts | ⭐⭐⭐⭐ | Phase 2 |
| **ARIA Labels** | All | ⭐⭐⭐⭐ | Phase 2 |
| **Color Blind Mode** | Custom | ⭐⭐⭐ | Phase 3 |
| **High Contrast Mode** | Custom | ⭐⭐⭐ | Phase 3 |

---

## Phase-Wise Implementation

### Phase 0: Setup & Foundation (Week 1) ✅ COMPLETE

**Timeline:** 1 week (Completed: 2026-01-05)
**Goal:** Clone react-financial-charts, set up library infrastructure

**Tasks:**
- [x] Clone react-financial-charts to `/Users/mashfiqurrahman/Workspace/wizardsofts/wizchart`
- [x] Rename packages from `@react-financial-charts/*` to `@wizardsofts/wizchart-*`
- [x] Update package metadata (author: WizardSofts, repository: GitLab Server 84)
- [x] Set up monorepo structure (Lerna workspace verified)
- [x] Verify TypeScript & build tools (all 11 packages compile successfully)
- [x] Verify Storybook configuration
- [x] Set up local npm linking for development
- [x] Document development setup in WIZCHART_README.md
- [ ] Configure ESLint, Prettier to match wizwebui standards (deferred to Phase 1)
- [ ] Set up Jest + React Testing Library (deferred to Phase 1)

**Deliverables:**
- ✅ Cloned repository with build system working (all 11 packages built)
- ✅ Storybook configured and ready to run
- ✅ Local package installable in gibd-quant-web (npm links created)
- ✅ 2,322 dependencies installed
- ✅ Committed to git with initial Phase 0 setup

**Commit:** `71642a7` - "feat: Complete Phase 0 - Rename packages and establish wizchart foundation"

---

### Phase 1: Core Chart Types & Essential Indicators (Weeks 2-5) 📊

**Timeline:** 4 weeks
**Goal:** Production-ready basic charting with 50 indicators

#### Week 2: Chart Types & Time Periods
**Features:**
- [x] Candlestick (from base)
- [x] OHLC (from base)
- [x] Line (from base)
- [x] Volume (from base)
- [ ] Area chart
- [ ] Time period selector (1H, 4H, 1D, 1W, 1M)
- [ ] Range selector component
- [ ] Price scaling (Linear/Log)
- [ ] Full screen mode
- [ ] Dark/Light theme integration with wizwebui

**Target:** Basic chart component usable in gibd-quant-web Chart tab

#### Week 3: Essential Indicators (20 new)
**Indicators:**
- Keltner Channels ⭐
- Ichimoku Cloud ⭐
- ADX (Average Directional Index)
- CCI (Commodity Channel Index)
- Williams %R
- OBV (On-Balance Volume)
- Aroon Indicator
- Chaikin Money Flow
- MFI (Money Flow Index)
- Pivot Points
- Fibonacci Retracement (Dynamic)
- VWAP
- Supertrend
- Donchian Channels
- Standard Deviation
- Linear Regression
- Price Channel
- Momentum
- ROC (Rate of Change)
- EMA Cross Signals

**Implementation:**
- Indicator calculation functions
- Overlay vs. separate pane logic
- Indicator settings UI
- Performance optimization (memoization)

#### Week 4: Basic Drawing Tools
**Tools:**
- Trendline (click + drag)
- Horizontal line
- Vertical line
- Rectangle
- Fibonacci Retracement (manual)
- Text annotation
- Arrow
- Eraser

**Features:**
- Drawing persistence (localStorage)
- Drawing editing (move, resize, delete)
- Color picker
- Line style (solid, dashed, dotted)
- Line width

#### Week 5: Export & Polish
**Features:**
- Export PNG/JPG
- Export SVG
- Export CSV (OHLC data)
- Lazy loading for large datasets
- Data gaps handling
- Mobile touch gestures optimization
- Bug fixes & performance tuning

**Deliverable:** v1.0.0 - Production-ready wizchart for gibd-quant-web

---

### Phase 2: Advanced Features & UX (Weeks 6-9) 🚀

**Timeline:** 4 weeks
**Goal:** Advanced interactivity, more chart types, 70 total indicators

#### Week 6: Advanced Interactivity
- [ ] Synchronized charts (multiple tickers)
- [ ] Chart comparison (overlay stocks)
- [ ] Keyboard shortcuts
- [ ] Context menu (right-click)
- [ ] Undo/Redo for drawings
- [ ] Copy/Paste drawings
- [ ] Drawing layers & locking

#### Week 7: More Chart Types & Indicators
**Chart Types:**
- Heiken Ashi
- Volume Profile
- Baseline
- Histogram enhancements

**Indicators (20 new):**
- Elliott Wave
- Gann Fan
- Andrews' Pitchfork
- Zig Zag
- Hurst Exponent
- Volume Oscillator
- Ease of Movement
- Commodity Selection Index
- Detrended Price Oscillator
- Know Sure Thing (KST)
- Plus 10 more

#### Week 8: Advanced Drawing Tools
- Fibonacci Extension
- Fibonacci Fan
- Ellipse
- Callout
- Measure Tool
- Fibonacci Time Zones

#### Week 9: Export & Time Features
- Export PDF
- Copy to Clipboard (image)
- Share Chart URL
- Time zone support
- Trading hours highlighting
- Missing data interpolation
- Progressive rendering

**Deliverable:** v2.0.0 - Feature-rich professional charting library

---

### Phase 3: Real-Time & DSE-Specific (Weeks 10-13) 🔴

**Timeline:** 4 weeks
**Goal:** Real-time updates, DSE-specific indicators, alerts

#### Week 10: Real-Time Data
- [ ] WebSocket integration
- [ ] Real-time candlestick updates
- [ ] Real-time indicator updates
- [ ] Session breaks visualization
- [ ] Circuit breaker visual alerts

#### Week 11: DSE-Specific Features
**Indicators (20 new):**
- Circuit Breaker Levels (DSE ±10%) ⭐
- Market Breadth (Advancing/Declining)
- Sector Rotation Index
- IPO Performance Tracker
- Block Deal Detection
- Institutional Activity Index
- Plus 14 more Bangladesh-specific

**Features:**
- DSE trading hours (10 AM - 2:30 PM BDT)
- Friday half-day highlighting
- Market holidays calendar

#### Week 12: Alerts System
- Price alerts (above/below)
- Indicator alerts (RSI cross, MACD signal)
- Volume spike alerts
- Drawing tool alerts (price crosses trendline)
- Alert notification system

#### Week 13: Exotic Chart Types
- Renko charts
- Kagi charts
- Point & Figure
- Data grouping & aggregation

**Deliverable:** v3.0.0 - Real-time DSE-ready charting platform

---

### Phase 4: AI/ML Integration (Weeks 14-17) 🤖

**Timeline:** 4 weeks
**Goal:** AI-powered features, pattern recognition, predictions

#### Week 14: DivinerReturns Integration
- [ ] Prediction overlay on chart
- [ ] Confidence interval visualization
- [ ] Predicted price path
- [ ] Backtest accuracy overlay

#### Week 15: Pattern Recognition
- [ ] Head & Shoulders detection
- [ ] Double Top/Bottom
- [ ] Triangle patterns
- [ ] Flag/Pennant patterns
- [ ] Auto support/resistance detection

#### Week 16: News Sentiment Integration
- [ ] News sentiment overlay
- [ ] Corporate action markers
- [ ] Earnings date highlighting
- [ ] Dividend announcements

#### Week 17: Advanced AI
- [ ] Anomaly detection
- [ ] Similar chart finder
- [ ] Trend strength prediction
- [ ] Volume anomaly detection

**Deliverable:** v4.0.0 - AI-powered intelligent charting

---

### Phase 5: Innovation & Scaling (Weeks 18+) 💡

**Timeline:** Ongoing
**Goal:** Cutting-edge features, performance at scale

**Features:**
- WebGL rendering for >1M data points
- Worker thread calculations
- Replay mode (historical backtesting)
- Pattern detection alerts
- Color blind mode
- High contrast mode
- Screen reader full support
- Embed code generation
- API marketplace integration

**Deliverable:** v5.0.0+ - Industry-leading charting platform

---

## Library Architecture

### Directory Structure

```
wizardsofts/wizchart/
├── packages/
│   └── wizchart/
│       ├── src/
│       │   ├── components/
│       │   │   ├── Chart/
│       │   │   │   ├── Chart.tsx
│       │   │   │   ├── Candlestick.tsx
│       │   │   │   ├── OHLC.tsx
│       │   │   │   ├── Line.tsx
│       │   │   │   ├── Area.tsx
│       │   │   │   └── Volume.tsx
│       │   │   ├── Indicators/
│       │   │   │   ├── MovingAverage.tsx
│       │   │   │   ├── BollingerBands.tsx
│       │   │   │   ├── MACD.tsx
│       │   │   │   ├── RSI.tsx
│       │   │   │   ├── KeltnerChannels.tsx
│       │   │   │   └── ... (90+ indicators)
│       │   │   ├── DrawingTools/
│       │   │   │   ├── Trendline.tsx
│       │   │   │   ├── FibonacciRetracement.tsx
│       │   │   │   ├── Rectangle.tsx
│       │   │   │   └── ... (20+ tools)
│       │   │   ├── Controls/
│       │   │   │   ├── TimePeriodSelector.tsx
│       │   │   │   ├── IndicatorSelector.tsx
│       │   │   │   ├── DrawingToolbar.tsx
│       │   │   │   ├── ExportMenu.tsx
│       │   │   │   └── SettingsPanel.tsx
│       │   │   └── Utils/
│       │   │       ├── Crosshair.tsx
│       │   │       ├── Tooltip.tsx
│       │   │       ├── RangeSelector.tsx
│       │   │       └── Zoom.tsx
│       │   ├── hooks/
│       │   │   ├── useChartData.ts
│       │   │   ├── useIndicators.ts
│       │   │   ├── useDrawings.ts
│       │   │   ├── useRealTime.ts
│       │   │   └── useAlerts.ts
│       │   ├── utils/
│       │   │   ├── calculations/
│       │   │   │   ├── indicators.ts (90+ indicator calculations)
│       │   │   │   ├── patterns.ts (pattern recognition)
│       │   │   │   ├── support-resistance.ts
│       │   │   │   └── statistics.ts
│       │   │   ├── data/
│       │   │   │   ├── transformers.ts
│       │   │   │   ├── aggregation.ts
│       │   │   │   └── validation.ts
│       │   │   ├── rendering/
│       │   │   │   ├── canvas.ts
│       │   │   │   ├── webgl.ts (future)
│       │   │   │   └── svg.ts
│       │   │   └── export/
│       │   │       ├── png.ts
│       │   │       ├── svg.ts
│       │   │       ├── pdf.ts
│       │   │       └── csv.ts
│       │   ├── types/
│       │   │   ├── chart.ts
│       │   │   ├── indicator.ts
│       │   │   ├── drawing.ts
│       │   │   └── data.ts
│       │   ├── themes/
│       │   │   ├── light.ts
│       │   │   ├── dark.ts
│       │   │   └── custom.ts
│       │   └── index.ts
│       ├── stories/
│       │   ├── Chart.stories.tsx
│       │   ├── Indicators.stories.tsx
│       │   └── DrawingTools.stories.tsx
│       ├── tests/
│       │   ├── components/
│       │   ├── utils/
│       │   └── integration/
│       ├── docs/
│       │   ├── getting-started.md
│       │   ├── api-reference.md
│       │   ├── indicators.md
│       │   ├── drawing-tools.md
│       │   └── advanced.md
│       ├── package.json
│       ├── tsconfig.json
│       ├── rollup.config.js
│       └── README.md
├── .storybook/
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── build.yml
│       └── publish.yml
├── package.json (root)
└── README.md
```

### Technology Stack

**Core:**
- React 18
- TypeScript 5.7
- Canvas API (primary rendering)
- D3.js (calculations, not rendering)

**Build:**
- Rollup (bundle library)
- Vite (dev server)
- SWC (fast compilation)

**Testing:**
- Jest
- React Testing Library
- Playwright (E2E)

**Documentation:**
- Storybook 7
- TypeDoc

**Integration:**
- wizwebui theme system
- Tailwind CSS utility classes (where applicable)

---

## Setup & Cloning

### Step 1: Clone react-financial-charts

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts
git clone https://github.com/reactivemarkets/react-financial-charts.git wizchart
cd wizchart
git remote rename origin upstream
```

### Step 2: Initialize as WizardSofts Project

```bash
# Rename package
sed -i '' 's/@react-financial-charts/@wizardsofts\/wizchart/g' packages/*/package.json

# Update package metadata
# Edit package.json:
# - name: "@wizardsofts/wizchart"
# - description: "Professional financial charting library for React"
# - author: "WizardSofts"
# - repository: "https://github.com/wizardsofts/wizchart"
```

### Step 3: Install Dependencies

```bash
npm install
npm run build
```

### Step 4: Link Locally

```bash
cd packages/wizchart
npm link

# In gibd-quant-web
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/apps/gibd-quant-web
npm link @wizardsofts/wizchart
```

### Step 5: Verify Setup

```bash
# Start Storybook
npm run storybook

# Run tests
npm test

# Build library
npm run build
```

---

## Development Workflow

### Daily Development

```bash
# In wizchart repo
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizchart
npm run dev  # Watch mode

# In gibd-quant-web
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/apps/gibd-quant-web
npm run dev  # Uses linked wizchart
```

### Testing Changes

```bash
# Unit tests
npm test

# E2E tests (in gibd-quant-web)
npm run test:e2e

# Visual tests (Storybook)
npm run storybook
```

### Versioning

Follow Semantic Versioning:
- **v1.0.0:** Production-ready Phase 1 features
- **v2.0.0:** Advanced features (Phase 2)
- **v3.0.0:** Real-time & DSE-specific (Phase 3)
- **v4.0.0:** AI/ML integration (Phase 4)
- **v5.0.0+:** Innovation features (Phase 5)

---

## Publishing Strategy

### Internal Use (Phase 0-1)

**Method:** Local npm link
**Reason:** Rapid iteration, not ready for public

### Private Registry (Phase 2-3)

**Method:** GitLab Package Registry
**Setup:**
```bash
npm config set @wizardsofts:registry http://10.0.0.84:8090/api/v4/projects/PROJECT_ID/packages/npm/
npm publish --registry http://10.0.0.84:8090/api/v4/projects/PROJECT_ID/packages/npm/
```

### Public npm (Phase 4+)

**Method:** Publish to npmjs.com
**Reason:** Open source contribution, community adoption

```bash
npm login
npm publish --access public
```

### Versioning Strategy

| Phase | Version | Stability | Audience |
|-------|---------|-----------|----------|
| Phase 0 | 0.x.x | Alpha | Internal only |
| Phase 1 | 1.x.x | Beta | gibd-quant-web |
| Phase 2 | 2.x.x | Stable | WizardSofts projects |
| Phase 3 | 3.x.x | Stable | Internal + select partners |
| Phase 4+ | 4.x.x+ | Stable | Public npm |

---

## Success Metrics

### Technical Metrics
- Bundle size < 200KB gzipped
- Render 10,000 candlesticks at 60fps
- Initial load < 2 seconds
- Real-time update latency < 100ms
- Test coverage > 80%

### Feature Metrics
- 90+ technical indicators (Phase 3)
- 20+ drawing tools (Phase 2)
- 10+ chart types (Phase 3)
- Real-time WebSocket support (Phase 3)
- AI pattern recognition (Phase 4)

### Adoption Metrics
- Used in gibd-quant-web (Phase 1)
- Used in 3+ WizardSofts projects (Phase 2)
- 100+ GitHub stars (Phase 4)
- 1,000+ npm downloads/month (Phase 4)

---

## Risk Mitigation

### Technical Risks

**Risk:** React Financial Charts base may have bugs/limitations
**Mitigation:** Start with fork, gradually replace internals if needed

**Risk:** Performance issues with 90+ indicators
**Mitigation:** Lazy loading, worker threads, memoization, WebGL for large datasets

**Risk:** Bundle size explosion
**Mitigation:** Tree-shaking, code splitting, dynamic imports

### Resource Risks

**Risk:** 18+ weeks is long timeline
**Mitigation:** Phase 1 (5 weeks) delivers production-ready minimum, iterate from there

**Risk:** Maintaining library alongside product development
**Mitigation:** Allocate dedicated time, use in gibd-quant-web to dog-food features

---

## Next Steps

1. ✅ **Decide library name:** wizchart
2. **Clone react-financial-charts** (next task)
3. **Set up repository structure**
4. **Create Phase 0 implementation plan**
5. **Start Phase 1 development**

---

**Document Author:** Claude Opus 4.5
**Created:** 2026-01-05
**Status:** Planning - Ready for Phase 0 execution
**Parent Roadmap:** [apps/gibd-quant-web/FUTURE_SCOPE.md](FUTURE_SCOPE.md)
