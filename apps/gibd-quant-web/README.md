# Quant-Flow Frontend

A Next.js frontend for the Quant-Flow trading signal analysis system, featuring AI-powered Generative UI with Vercel AI SDK and LangChain.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server (runs on port 3001)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Prerequisites

1. **Node.js 18+** - Required for Next.js 14
2. **FastAPI Backend** - Running on port 5000
3. **Ollama** (for AI features) - Running on port 11434

```bash
# Install Ollama (macOS)
brew install ollama

# Pull a model
ollama pull llama3.1

# Start Ollama server
ollama serve
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout (wraps all pages)
│   ├── page.tsx            # Home page (/)
│   ├── signals/            # /signals route
│   ├── dashboard/          # /dashboard route
│   ├── chat/               # /chat route
│   ├── multi-criteria/     # /multi-criteria route (compound query builder)
│   └── api/                # API routes
├── components/             # React components
│   ├── layout/             # Layout components (Header, Footer)
│   ├── signals/            # Signal display components
│   ├── chat/               # Chat UI components
│   └── multi-criteria/     # Multi-criteria query builder components
├── lib/                    # Utility functions and API client
├── hooks/                  # Custom React hooks
├── LEARNING.md             # Learning guide for each module
└── README.md               # This file
```

## Learning Path

This frontend is designed as an incremental learning experience. See [LEARNING.md](./LEARNING.md) for detailed explanations of each module:

1. **Module 1**: Next.js Setup & Basics
2. **Module 2**: React Components & Tailwind
3. **Module 3**: Data Fetching from FastAPI
4. **Module 4**: Interactive Client Components
5. **Module 5**: Charts & Visualization
6. **Module 6**: LangChain + Ollama
7. **Module 7**: Vercel AI SDK Streaming
8. **Module 8**: Generative UI
9. **Module 9**: Advanced LangChain Agents
10. **Module 10**: Production Polish

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:5000

# Ollama configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Google Analytics (optional)
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Google AdSense / AdMob (optional)
NEXT_PUBLIC_ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX
NEXT_PUBLIC_ADSENSE_BANNER_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT=XXXXXXXXXX
NEXT_PUBLIC_ADSENSE_INFEED_SLOT=XXXXXXXXXX
```

## Architecture & Component Libraries

This application follows a **three-tier UI component architecture** to ensure maintainability, reusability, and npm publishability:

### Component Hierarchy
1. **WizWebUI** (`@wizwebui/core`) - Low-level UI primitives (Button, Input, Card, Table, etc.)
2. **WizChart** (`@wizardsofts/wizchart-*`) - Domain-specific charting components and interactive tools
3. **Application Components** - Business logic and page-specific components using library components

### Key Principle
**All UI components must come from either WizWebUI or WizChart libraries.** Custom UI components are not created without explicit approval. This ensures:
- Consistency across applications
- Easier library maintenance and updates
- Reusability across other projects
- Cleaner separation of concerns

### Example: AddIndicatorPanel Component
The `AddIndicatorPanel` component is a library component from `@wizardsofts/wizchart-interactive` that handles technical indicator selection for charts:

```typescript
import { AddIndicatorPanel, INDICATOR_TEMPLATES, type IndicatorConfig } from '@wizardsofts/wizchart-interactive';

// Usage in CompanyChart component
<AddIndicatorPanel
  indicators={indicators}
  onAddIndicator={(indicator) => setIndicators([...indicators, indicator])}
  onRemoveIndicator={(id) => setIndicators(indicators.filter(i => i.id !== id))}
/>
```

**Supported Indicators:**
- SMA (Simple Moving Average)
- EMA (Exponential Moving Average)
- BB (Bollinger Bands)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)

See [wizchart documentation](../../../wizardsofts/wizchart) for component details.

## Features

### Coming Soon Mode

When accessed via the production domain (`guardianinvestmentbd.com`), the app displays a Coming Soon page instead of the full application. This allows development to continue while the site is publicly accessible.

**How it works:**
- Middleware ([middleware.ts](./middleware.ts)) checks the request host
- Production domains show `/coming-soon` page
- Local/IP access shows the full application

**To disable Coming Soon mode:**
1. Delete `middleware.ts`, OR
2. Remove the domain from the `comingSoonDomains` array in middleware

**Contact displayed:** info@guardianinvestmentbd.com

### Fixed Layout & Navigation

The application features a minimal, fixed layout design:

- **Fixed Header**: One-line navigation bar that stays at the top while scrolling
  - Compact logo and navigation menu
  - Ticker search input
  - Backdrop blur for modern appearance

- **Fixed Footer**: One-line footer that stays at the bottom while scrolling
  - Copyright and disclaimer text
  - Quick links (About, Disclaimer, Privacy, GitHub)
  - Responsive design for mobile and desktop

### Analytics & Tracking

Built-in analytics integration for tracking user behavior:

- **Google Analytics (GA4)**:
  - Automatic pageview tracking on route changes
  - Custom event tracking for user interactions
  - Set `NEXT_PUBLIC_GA_MEASUREMENT_ID` to enable

- **Google AdSense / AdMob**:
  - Display ads support with multiple placement options
  - Banner, sidebar, and in-feed ad formats
  - Set `NEXT_PUBLIC_ADSENSE_CLIENT_ID` to enable

- **Click Tracking**:
  - Automatic tracking of all link clicks
  - Button click events
  - Form submissions
  - All events sent to Google Analytics

**Analytics API**:
```typescript
import { trackEvent, trackButtonClick, trackLinkClick, trackFormSubmit } from '@/lib/analytics';

// Track custom events
trackEvent('category', 'action', 'label', value);

// Track specific interactions
trackButtonClick('Submit');
trackLinkClick('/signals', 'View Signals');
trackFormSubmit('ticker-search');
```

### Multi-Criteria Query Builder (`/multi-criteria`)

Build complex stock queries by combining multiple natural language criteria with AND/OR logic:

- **Suggestion Chips**: Quick-select common queries organized by category (threshold, trend, ranking, comparison, sector)
- **AND/OR Logic**: Combine up to 10 criteria with configurable match mode
- **Real-time Feedback**: See individual results per criterion before executing the compound query
- **Export Options**: Export results to CSV, PDF, or Word document
- **Column Visibility**: Show/hide columns in the results table
- **Sortable Results**: Click column headers to sort by any field
- **Responsive UI**: Works seamlessly on desktop and tablet

Example compound queries:
- "stocks with RSI above 70" AND "top 20 stocks by volume"
- "stocks outperforming sector" OR "decreasing SMA_20 for 3 days"

### AI Chat (`/chat`)

Natural language query interface powered by LangChain and Ollama:
- Stream responses with Vercel AI SDK
- Generative UI for interactive results
- Context-aware follow-up questions

### Signal Dashboard (`/signals`)

View all trading signals with filters and sorting:
- BUY/SELL/HOLD signal indicators
- Confidence scores and total scores
- Sector and category filters

## Development

The frontend proxies `/api/v1/*` requests to the backend (default: `http://localhost:5010`) to avoid CORS issues during development.

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Vercel AI SDK** - Streaming chat and generative UI
- **LangChain.js** - LLM orchestration
- **Ollama** - Local LLM inference
