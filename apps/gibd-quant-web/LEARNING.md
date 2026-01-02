# Quant-Flow Frontend Learning Guide

This guide teaches you Next.js, React, Vercel AI SDK, and LangChain by building a real trading signal analysis interface. Each module builds on the previous one, with concepts explained as you encounter them in code.

---

## How to Use This Guide

1. **Read the concept** - Understand what you're learning
2. **Review the code** - Look at the annotated source files
3. **Try the exercise** - Practice what you learned
4. **Take the quiz** - Test your understanding

---

## Table of Contents

- [Module 1: Hello Next.js](#module-1-hello-nextjs---project-setup) ✅
- [Module 2: Components 101](#module-2-components-101---react--tailwind) ✅
- [Module 3: Data Fetching](#module-3-data-fetching---server-components) ✅
- [Module 4: Interactive Components](#module-4-interactive-components---client-state) ✅
- [Module 5: Charts & Visualization](#module-5-charts--visualization) ✅
- [Module 6: AI Chat](#module-6-ai-chat-with-vercel-ai-sdk) ✅
- [Module 7: Generative UI](#module-7-generative-ui---ai-rendered-components) ✅
- [Module 8: Production Polish](#module-8-production-polish) ✅

---

# Module 1: Hello Next.js - Project Setup

## What You'll Learn

- What Next.js is and why we use it
- The App Router architecture
- How `layout.tsx` and `page.tsx` work together
- Running your first Next.js app

## Why It Matters

Next.js is the most popular React framework for building production web applications. It provides:
- **File-based routing** - Create pages by adding files
- **Server-side rendering** - Better SEO and performance
- **API routes** - Backend endpoints in the same project
- **Zero configuration** - Works out of the box

For Quant-Flow, Next.js gives us a modern foundation for building the AI chat interface with streaming support.

---

## Concept: What is Next.js?

**Next.js** is a React framework that adds structure and features on top of React:

```
React alone:          Next.js adds:
-----------          -------------
Components           + File-based routing
JSX                  + Server components
Hooks                + API routes
                     + Image optimization
                     + Built-in CSS support
```

### App Router vs Pages Router

Next.js 13+ introduced the **App Router** (what we use):

```
OLD (Pages Router):     NEW (App Router):
pages/                  app/
├── index.tsx           ├── page.tsx        (home)
├── about.tsx           ├── about/
└── signals/            │   └── page.tsx    (about page)
    └── index.tsx       └── signals/
                            └── page.tsx    (signals page)
```

The App Router uses **React Server Components** by default, meaning components run on the server and send HTML to the client.

---

## Code Walkthrough

### File: `app/layout.tsx`

This is the **root layout** that wraps all pages:

```tsx
// Metadata for SEO - shows in browser tab and search results
export const metadata: Metadata = {
  title: "Quant-Flow | DSE Trading Signals",
  description: "Quantitative trading signal analysis...",
};

// The layout component
export default function RootLayout({
  children,  // <-- This is the page content
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>  {/* Page content goes here */}
    </html>
  );
}
```

**Key Points:**
- `children` is automatically passed by Next.js
- The layout persists across page navigation (good for headers/sidebars)
- `Metadata` export handles SEO automatically

### File: `app/page.tsx`

This is the **home page** (the `/` route):

```tsx
export default function HomePage() {
  return (
    <main>
      <h1>Quant-Flow</h1>
      {/* Rest of the page content */}
    </main>
  );
}
```

**Key Points:**
- File path `app/page.tsx` = URL path `/`
- This is a **Server Component** - runs on the server
- No `"use client"` directive means server-rendered

### File: `next.config.js`

Configuration file for Next.js:

```js
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: "http://localhost:5000/api/v1/:path*",
      },
    ];
  },
};
```

**Key Points:**
- `rewrites()` proxies requests to avoid CORS issues
- `/backend/signals` → `http://localhost:5000/api/v1/signals`

---

## Project Structure Explained

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx          # Root layout (HTML wrapper)
│   ├── page.tsx            # Home page (/)
│   └── globals.css         # Global styles
├── package.json            # Dependencies and scripts
├── next.config.js          # Next.js configuration
├── tsconfig.json           # TypeScript configuration
├── tailwind.config.js      # Tailwind CSS configuration
└── postcss.config.js       # PostCSS (required for Tailwind)
```

---

## Running the App

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) to see your app!

---

## Key Takeaways

1. **Next.js = React + Routing + Server Features**
2. **`app/` directory** uses the new App Router
3. **`layout.tsx`** wraps pages (persists across navigation)
4. **`page.tsx`** defines the actual page content
5. **File path = URL path** (e.g., `app/signals/page.tsx` = `/signals`)

---

## Exercise

Create a new page at `/about`:

1. Create the directory: `app/about/`
2. Create the file: `app/about/page.tsx`
3. Add a simple component that returns some JSX
4. Navigate to `http://localhost:3001/about`

<details>
<summary>Solution</summary>

```tsx
// app/about/page.tsx
export default function AboutPage() {
  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold">About Quant-Flow</h1>
      <p className="mt-4">
        A quantitative trading signal system for DSE.
      </p>
    </main>
  );
}
```

</details>

---

## Quiz

1. **What is the purpose of `layout.tsx`?**
   - A) Define page content
   - B) Wrap pages with shared UI that persists across navigation
   - C) Configure build settings
   - D) Handle API requests

2. **What URL does `app/signals/page.tsx` correspond to?**
   - A) `/app/signals`
   - B) `/signals/page`
   - C) `/signals`
   - D) `/page/signals`

3. **Are components in the App Router server or client rendered by default?**
   - A) Client-rendered
   - B) Server-rendered
   - C) Both equally
   - D) Neither

<details>
<summary>Answers</summary>

1. **B** - Layouts wrap pages and persist across navigation
2. **C** - The file path `app/signals/page.tsx` maps to `/signals`
3. **B** - App Router components are Server Components by default

</details>

---

## What's Next?

In **Module 2**, you'll learn:
- How to create reusable React components
- Tailwind CSS utility classes
- Setting up shadcn/ui component library
- Building a Header and Footer

---

# Module 2: Components 101 - React + Tailwind

## What You'll Learn

- Creating reusable React components
- TypeScript interfaces for component props
- Tailwind CSS utility classes
- The `cn()` utility for class merging
- Compound component pattern

## Why It Matters

Components are the building blocks of React applications. Well-designed components:
- **Reduce code duplication** - Write once, use everywhere
- **Improve consistency** - Same styling across the app
- **Make testing easier** - Isolated, predictable behavior
- **Enable composition** - Build complex UIs from simple parts

---

## Concept: What is a React Component?

A React component is a **JavaScript function that returns JSX** (HTML-like syntax):

```tsx
// Simple component
function Greeting() {
  return <h1>Hello, World!</h1>;
}

// Component with props (parameters)
function Greeting({ name }: { name: string }) {
  return <h1>Hello, {name}!</h1>;
}

// Usage
<Greeting name="Quant-Flow" />
```

### Props (Properties)

Props are how you pass data to components:

```tsx
interface ButtonProps {
  variant: "primary" | "secondary";
  size: "sm" | "md" | "lg";
  children: React.ReactNode;  // The content inside the button
}

function Button({ variant, size, children }: ButtonProps) {
  return <button className={`btn-${variant} btn-${size}`}>{children}</button>;
}
```

---

## Concept: Tailwind CSS

Tailwind is a **utility-first** CSS framework. Instead of writing CSS classes:

```css
/* Traditional CSS */
.card {
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
```

You use utility classes directly in HTML:

```tsx
{/* Tailwind */}
<div className="p-4 bg-white rounded-lg shadow-sm">
  Card content
</div>
```

### Common Tailwind Classes

| Class | CSS Equivalent |
|-------|----------------|
| `p-4` | `padding: 1rem` |
| `m-2` | `margin: 0.5rem` |
| `bg-white` | `background: white` |
| `text-gray-600` | `color: #4b5563` |
| `rounded-lg` | `border-radius: 0.5rem` |
| `shadow-sm` | `box-shadow: 0 1px 2px...` |
| `flex` | `display: flex` |
| `items-center` | `align-items: center` |
| `gap-4` | `gap: 1rem` |

---

## Code Walkthrough

### File: `lib/utils.ts` - The cn() Helper

```tsx
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**Why we need this:**
- `clsx`: Conditionally join class names
- `twMerge`: Resolve Tailwind class conflicts

```tsx
// Example: Later classes override earlier ones
cn("px-2 py-1", "px-4")  // Result: "py-1 px-4" (px-4 wins)

// Conditional classes
cn("base-class", isActive && "bg-blue-500")
```

### File: `components/ui/button.tsx`

```tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "buy" | "sell";
  size?: "sm" | "md" | "lg";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    return (
      <button
        className={cn(
          // Base styles (always applied)
          "inline-flex items-center justify-center rounded-md font-medium",

          // Variant styles (one of these)
          { default: "bg-gray-900 text-white", /*...*/ }[variant],

          // Size styles (one of these)
          { sm: "h-8 px-3 text-sm", /*...*/ }[size],

          // Custom className from props (allows overrides)
          className
        )}
        ref={ref}
        {...props}  // Spread remaining props (onClick, disabled, etc.)
      />
    );
  }
);
```

**Key Patterns:**
1. **`React.forwardRef`** - Allows refs to be passed through
2. **`extends React.ButtonHTMLAttributes`** - Inherits all native button props
3. **`...props`** - Passes through onClick, disabled, type, etc.
4. **`cn()`** - Merges all class strings with conflict resolution

### File: `components/ui/card.tsx` - Compound Components

```tsx
// Multiple related components exported together
const Card = ({ className, ...props }) => (
  <div className={cn("rounded-xl border bg-white shadow-sm", className)} {...props} />
);

const CardHeader = ({ className, ...props }) => (
  <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
);

const CardTitle = ({ className, ...props }) => (
  <h3 className={cn("text-xl font-semibold", className)} {...props} />
);

// Usage - components work together
<Card>
  <CardHeader>
    <CardTitle>GP Stock</CardTitle>
  </CardHeader>
  <CardContent>Price: 450 BDT</CardContent>
</Card>
```

### File: `components/ui/badge.tsx` - SignalBadge

```tsx
function SignalBadge({ type }: { type: "BUY" | "SELL" | "HOLD" }) {
  const variant = type.toLowerCase() as "buy" | "sell" | "hold";
  return <Badge variant={variant}>{type}</Badge>;
}

// Usage - automatically styled based on signal type
<SignalBadge type="BUY" />   // Green
<SignalBadge type="SELL" />  // Red
<SignalBadge type="HOLD" />  // Amber
```

### File: `components/layout/Header.tsx`

```tsx
import Link from "next/link";

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b bg-white/95 backdrop-blur">
      {/* Logo */}
      <Link href="/">Quant-Flow</Link>

      {/* Navigation */}
      <nav className="hidden md:flex gap-6">
        <Link href="/signals">Signals</Link>
        <Link href="/dashboard">Dashboard</Link>
        <Link href="/chat">AI Chat</Link>
      </nav>
    </header>
  );
}
```

**Key Concepts:**
- `Link` from `next/link` - Client-side navigation (no page reload)
- `hidden md:flex` - Hide on mobile, show on medium screens+
- `sticky top-0` - Stick to top when scrolling
- `backdrop-blur` - Frosted glass effect

---

## Files Created in Module 2

| File | Purpose |
|------|---------|
| `lib/utils.ts` | `cn()` helper and formatters |
| `components/ui/button.tsx` | Reusable button with variants |
| `components/ui/card.tsx` | Card compound components |
| `components/ui/badge.tsx` | Badge and SignalBadge |
| `components/ui/input.tsx` | Text input field |
| `components/layout/Header.tsx` | Navigation header |
| `components/layout/Footer.tsx` | Page footer |

---

## Key Takeaways

1. **Components are functions** that return JSX
2. **Props** pass data into components (like function parameters)
3. **Tailwind** uses utility classes instead of custom CSS
4. **`cn()`** merges class names and resolves conflicts
5. **Compound components** (Card, CardHeader, etc.) work together
6. **`forwardRef`** allows passing refs through components
7. **`...props` spread** passes through native HTML attributes

---

## Exercise

Create a `<ConfidenceBar>` component that shows a colored progress bar:

```tsx
// Usage
<ConfidenceBar value={0.75} />  // 75% filled, green
<ConfidenceBar value={0.3} />   // 30% filled, red
```

Requirements:
1. Accept a `value` prop (0 to 1)
2. Show percentage as width
3. Color: green if > 0.5, red if <= 0.5

<details>
<summary>Solution</summary>

```tsx
// components/ui/confidence-bar.tsx
interface ConfidenceBarProps {
  value: number;  // 0 to 1
  className?: string;
}

export function ConfidenceBar({ value, className }: ConfidenceBarProps) {
  const percentage = Math.round(value * 100);
  const isHigh = value > 0.5;

  return (
    <div className={cn("h-2 w-full bg-gray-200 rounded-full overflow-hidden", className)}>
      <div
        className={cn(
          "h-full rounded-full transition-all",
          isHigh ? "bg-buy" : "bg-sell"
        )}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
```

</details>

---

## Quiz

1. **What does `...props` do in a component?**
   - A) Creates a new object
   - B) Spreads remaining props to the underlying element
   - C) Copies the component
   - D) Validates props

2. **What is the purpose of `cn()` utility?**
   - A) Create new components
   - B) Merge class names and resolve Tailwind conflicts
   - C) Navigate between pages
   - D) Fetch data from API

3. **What does `hidden md:flex` mean in Tailwind?**
   - A) Always hidden
   - B) Always flex
   - C) Hidden on mobile, flex on medium screens and up
   - D) Flex on mobile, hidden on medium screens

4. **Why use `React.forwardRef`?**
   - A) To forward props
   - B) To allow refs to be passed through the component
   - C) To forward state
   - D) To forward events

<details>
<summary>Answers</summary>

1. **B** - Spreads remaining props to the underlying element
2. **B** - Merge class names and resolve Tailwind conflicts
3. **C** - Hidden on mobile, flex on medium screens and up
4. **B** - To allow refs to be passed through the component

</details>

---

## What's Next?

In **Module 3**, you'll learn:
- React Server Components vs Client Components
- Fetching data from the FastAPI backend
- TypeScript interfaces matching Python models
- Loading states and error handling

---

# Module 3: Data Fetching - Server Components

## What You'll Learn

- React Server Components vs Client Components
- Fetching data in async Server Components
- TypeScript interfaces matching Python models
- Special files: `loading.tsx` and `error.tsx`
- API client pattern with error handling

## Why It Matters

Server Components let you fetch data directly on the server:
- **No loading spinners needed** - Data arrives with the HTML
- **No client-side JavaScript** - Smaller bundle size
- **Better SEO** - Search engines see actual content
- **Direct data access** - Can query databases directly

---

## Concept: Server vs Client Components

| Feature | Server Component | Client Component |
|---------|-----------------|------------------|
| Runs on | Server only | Browser |
| Can use | async/await, direct DB | useState, useEffect |
| Bundle size | Zero JS | Adds to bundle |
| Interactivity | None | Full |
| Default in App Router | ✅ Yes | Need "use client" |

**Rule of thumb:**
- Start with Server Components (default)
- Add `"use client"` only when you need hooks or event handlers

---

## Concept: Async Server Components

In Next.js App Router, page components can be async:

```tsx
// This is a Server Component (no "use client")
export default async function SignalsPage() {
  // This fetch runs on the SERVER, not in browser!
  const response = await fetch('http://backend/api/signals');
  const signals = await response.json();

  return (
    <div>
      {signals.map(signal => (
        <SignalCard key={signal.id} signal={signal} />
      ))}
    </div>
  );
}
```

**Key insight:** The `await` happens on the server. The browser receives ready-to-display HTML.

---

## Code Walkthrough

### File: `lib/types.ts` - TypeScript Interfaces

These match your Python models from `src/database/models.py`:

```tsx
// Matches SignalHistory model
export interface Signal {
  id: number;
  ticker: string;
  signal_date: string;        // ISO string
  signal_type: "BUY" | "SELL" | "HOLD";
  confidence: number;         // 0.0 to 1.0
  entry_price: number;
  target_price: number | null;
  stop_loss: number | null;
  // ... more fields
}

// Matches API response shape
export interface SignalsResponse {
  signals: Signal[];
  total: number;
  page: number;
  limit: number;
}
```

**Benefits:**
- IDE autocomplete for all fields
- Type errors caught at build time
- Documentation of data shapes

### File: `lib/api.ts` - API Client

```tsx
const API_BASE = "/backend";  // Proxied to localhost:5000

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

export async function getSignals(params = {}): Promise<SignalsResponse> {
  const queryString = buildQueryString(params);
  return fetchAPI<SignalsResponse>(`/signals${queryString}`);
}
```

**Key patterns:**
- Generic `<T>` for type-safe responses
- Error handling with descriptive messages
- Query string builder for filters

### File: `app/signals/loading.tsx` - Loading State

```tsx
// This file is SPECIAL in App Router
// Next.js shows this automatically while page.tsx loads

export default function SignalsLoading() {
  return (
    <div className="animate-pulse">
      {/* Skeleton UI */}
      <div className="h-8 w-48 bg-gray-200 rounded" />
    </div>
  );
}
```

**No useState needed!** Next.js handles the loading state automatically.

### File: `app/signals/error.tsx` - Error Boundary

```tsx
"use client";  // Error boundaries must be Client Components

export default function SignalsError({
  error,
  reset,  // Function to retry
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div>
      <h1>Error: {error.message}</h1>
      <button onClick={reset}>Try Again</button>
    </div>
  );
}
```

**Key points:**
- Must be a Client Component (`"use client"`)
- `reset` function provided by Next.js to retry
- Catches errors from the page and children

### File: `app/signals/page.tsx` - The Page

```tsx
import { getSignals } from "@/lib/api";

// Force dynamic rendering (always fetch fresh)
export const dynamic = "force-dynamic";

export default async function SignalsPage() {
  // SERVER-SIDE FETCH - runs before sending HTML
  const response = await getSignals({ limit: 50 });

  return (
    <div>
      {response.signals.map(signal => (
        <SignalCard key={signal.id} signal={signal} />
      ))}
    </div>
  );
}
```

**Flow:**
1. User navigates to `/signals`
2. Next.js shows `loading.tsx`
3. Server calls `getSignals()` via FastAPI
4. Server renders HTML with data
5. User sees complete page instantly

---

## Files Created in Module 3

| File | Purpose |
|------|---------|
| `lib/types.ts` | TypeScript interfaces for API data |
| `lib/api.ts` | API client with typed methods |
| `app/signals/page.tsx` | Server Component with data fetching |
| `app/signals/loading.tsx` | Automatic loading skeleton |
| `app/signals/error.tsx` | Error boundary with retry |

---

## Key Takeaways

1. **Server Components can be async** - Use `await` directly
2. **Data fetches on the server** - No useEffect needed
3. **`loading.tsx`** - Automatic loading state, no useState
4. **`error.tsx`** - Automatic error boundary, must be "use client"
5. **TypeScript interfaces** - Match your Python models
6. **API proxy** - `/backend/*` avoids CORS issues

---

## Exercise

Create a `/signals/[ticker]` dynamic route that shows signals for a specific stock.

1. Create `app/signals/[ticker]/page.tsx`
2. Use `params.ticker` to get the ticker from the URL
3. Call `getSignalsByTicker(params.ticker)`
4. Display the signals

<details>
<summary>Solution</summary>

```tsx
// app/signals/[ticker]/page.tsx
import { getSignalsByTicker } from "@/lib/api";
import { SignalBadge } from "@/components/ui/badge";

interface PageProps {
  params: { ticker: string };
}

export default async function TickerSignalsPage({ params }: PageProps) {
  const signals = await getSignalsByTicker(params.ticker);

  return (
    <div className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">
        Signals for {params.ticker}
      </h1>

      {signals.length === 0 ? (
        <p>No signals found for {params.ticker}</p>
      ) : (
        <div className="space-y-4">
          {signals.map(signal => (
            <div key={signal.id} className="p-4 border rounded">
              <SignalBadge type={signal.signal_type} />
              <p>Date: {signal.signal_date}</p>
              <p>Confidence: {signal.confidence}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

</details>

---

## Quiz

1. **What directive makes a component render in the browser?**
   - A) "use server"
   - B) "use client"
   - C) "use browser"
   - D) No directive needed

2. **Where does data fetching happen in an async Server Component?**
   - A) In the browser
   - B) On the server
   - C) Both
   - D) Neither

3. **What file shows automatically while a page is loading?**
   - A) loading.tsx
   - B) waiting.tsx
   - C) spinner.tsx
   - D) suspense.tsx

4. **Why must error.tsx be a Client Component?**
   - A) It uses fetch
   - B) It uses useState for error state
   - C) React error boundaries require client-side JavaScript
   - D) It's faster

<details>
<summary>Answers</summary>

1. **B** - "use client" makes it a Client Component
2. **B** - On the server, before HTML is sent
3. **A** - loading.tsx is the special file name
4. **C** - Error boundaries are a React feature that needs JS

</details>

---

## What's Next?

In **Module 4**, you'll learn:
- Adding interactivity with Client Components
- useState and useEffect hooks
- Event handlers (onClick, onChange)
- Building filter and search functionality

---

# Module 4: Interactive Components - Client State

## What You'll Learn

- The difference between Server and Client Components
- React hooks: useState, useMemo, useDebounce
- Controlled inputs and form state
- Client-side filtering and search
- Custom multi-select dropdown components

## Why It Matters

Server Components can't handle user interaction. When users need to:
- Click buttons
- Type in search boxes
- Select filters
- Toggle options

...you need **Client Components** with React hooks to manage state.

---

## Concept: "use client" Directive

The `"use client"` directive at the top of a file marks it as a Client Component:

```tsx
"use client";  // <-- This is required for any component using hooks

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);  // Hook = Client Component

  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

**Without "use client":**
```
Error: useState only works in Client Components.
Add the "use client" directive at the top of the file.
```

---

## Concept: React Hooks

Hooks are special functions that let you "hook into" React features:

| Hook | Purpose | Example |
|------|---------|---------|
| `useState` | Store and update values | Filter selections, search text |
| `useMemo` | Cache computed values | Filtered signal list |
| `useEffect` | Side effects | API calls on mount |
| `useDebounce` | Delay updates | Don't filter on every keystroke |

### useState - Managing State

```tsx
// Syntax: const [value, setValue] = useState(initialValue);

const [search, setSearch] = useState("");           // String
const [selectedType, setSelectedType] = useState<SignalType>("all");  // Union type
const [selectedItems, setSelectedItems] = useState<string[]>([]);     // Array
```

### useMemo - Caching Computed Values

```tsx
// Only recomputes when dependencies change
const filteredSignals = useMemo(() => {
  return signals.filter(s => {
    if (signalType !== "all" && s.signal_type !== signalType) return false;
    if (search && !s.ticker.includes(search)) return false;
    return true;
  });
}, [signals, signalType, search]);  // <-- Dependencies array
```

### useDebounce - Preventing Excessive Updates

```tsx
// Custom hook that delays updates
const debouncedSearch = useDebounce(searchInput, 300);  // Wait 300ms

// Filter runs with debounced value, not every keystroke
const filtered = useMemo(() => {
  return signals.filter(s => s.ticker.includes(debouncedSearch));
}, [signals, debouncedSearch]);
```

---

## Code Walkthrough

### File: `components/signals/SignalFilter.tsx`

This component provides filter controls:

```tsx
"use client";

import { useState } from "react";

interface SignalFilterProps {
  signalType: SignalType;
  onSignalTypeChange: (type: SignalType) => void;
  tickerSearch: string;
  onTickerSearchChange: (search: string) => void;
  // ... more props
}

export function SignalFilter({
  signalType,
  onSignalTypeChange,
  tickerSearch,
  onTickerSearchChange,
}: SignalFilterProps) {
  // Local state for UI (threshold panel open/closed)
  const [showThresholds, setShowThresholds] = useState(false);

  return (
    <div>
      {/* Controlled input - value comes from props */}
      <Input
        value={tickerSearch}
        onChange={(e) => onTickerSearchChange(e.target.value)}
        placeholder="Search by ticker..."
      />

      {/* Filter buttons */}
      {["all", "BUY", "HOLD", "SELL"].map((type) => (
        <Button
          key={type}
          variant={signalType === type ? "default" : "outline"}
          onClick={() => onSignalTypeChange(type as SignalType)}
        >
          {type}
        </Button>
      ))}
    </div>
  );
}
```

**Key Pattern: Lifting State Up**
- The filter component doesn't own the state
- Parent passes current values and callbacks
- This lets parent control filtering logic

### File: `components/signals/SignalsList.tsx`

The parent component that owns the state:

```tsx
"use client";

import { useState, useMemo } from "react";
import { useDebounce } from "@/hooks/useDebounce";

export function SignalsList({ signals }: { signals: Signal[] }) {
  // State owned by this component
  const [signalType, setSignalType] = useState<SignalType>("all");
  const [tickerSearch, setTickerSearch] = useState("");
  const [selectedSectors, setSelectedSectors] = useState<string[]>([]);

  // Debounce search input
  const debouncedSearch = useDebounce(tickerSearch, 300);

  // Computed filtered list
  const filteredSignals = useMemo(() => {
    return signals.filter((signal) => {
      // Type filter
      if (signalType !== "all" && signal.signal_type !== signalType) {
        return false;
      }

      // Search filter
      if (debouncedSearch && !signal.ticker.toLowerCase().includes(debouncedSearch.toLowerCase())) {
        return false;
      }

      // Multi-select sector filter
      if (selectedSectors.length > 0 && !selectedSectors.includes(signal.sector || "")) {
        return false;
      }

      return true;
    });
  }, [signals, signalType, debouncedSearch, selectedSectors]);

  return (
    <div>
      <SignalFilter
        signalType={signalType}
        onSignalTypeChange={setSignalType}
        tickerSearch={tickerSearch}
        onTickerSearchChange={setTickerSearch}
        selectedSectors={selectedSectors}
        onSectorsChange={setSelectedSectors}
        // ... more props
      />

      <div className="grid grid-cols-3 gap-4">
        {filteredSignals.map((signal) => (
          <SignalCard key={signal.id} signal={signal} />
        ))}
      </div>
    </div>
  );
}
```

### File: `hooks/useDebounce.ts`

Custom hook for debouncing:

```tsx
import { useState, useEffect } from "react";

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    // Set up timer
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Cleanup - runs before next effect or unmount
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

**How it works:**
1. User types "G" → timer starts (300ms)
2. User types "P" → previous timer cancelled, new timer starts
3. User stops typing → 300ms passes → debouncedValue updates to "GP"
4. Filter runs once with "GP" instead of twice with "G" then "GP"

### Multi-Select Component Pattern

```tsx
function MultiSelect({
  options,
  selected,
  onChange,
  placeholder,
}: {
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      // Remove if already selected
      onChange(selected.filter((s) => s !== option));
    } else {
      // Add if not selected
      onChange([...selected, option]);
    }
  };

  return (
    <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)}>
        {selected.length === 0
          ? placeholder
          : selected.length === 1
            ? selected[0]
            : `${selected.length} selected`}
      </button>

      {isOpen && (
        <div className="absolute z-20 bg-white border rounded shadow">
          {options.map((option) => (
            <label key={option} className="flex items-center gap-2 p-2">
              <input
                type="checkbox"
                checked={selected.includes(option)}
                onChange={() => toggleOption(option)}
              />
              {option}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Files Created in Module 4

| File | Purpose |
|------|---------|
| `components/signals/SignalFilter.tsx` | Filter controls with multi-select |
| `components/signals/SignalsList.tsx` | Parent component with state |
| `components/signals/SignalCard.tsx` | Individual signal display |
| `hooks/useDebounce.ts` | Custom debounce hook |

---

## Key Takeaways

1. **"use client"** - Required for any component using hooks
2. **useState** - Stores values that change over time
3. **useMemo** - Caches computed values (like filtered lists)
4. **useDebounce** - Prevents filtering on every keystroke
5. **Lifting state up** - Parent owns state, children get callbacks
6. **Controlled inputs** - Value and onChange controlled by React
7. **Multi-select pattern** - Array state with includes/filter/spread

---

## Exercise

Create a `<RangeSlider>` component for the buy/sell thresholds:

```tsx
// Usage
<RangeSlider
  value={buyThreshold}
  onChange={setBuyThreshold}
  min={-1}
  max={1}
  step={0.1}
  label="BUY Threshold"
/>
```

<details>
<summary>Solution</summary>

```tsx
// components/ui/range-slider.tsx
"use client";

interface RangeSliderProps {
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
  label: string;
}

export function RangeSlider({
  value,
  onChange,
  min,
  max,
  step,
  label,
}: RangeSliderProps) {
  return (
    <div>
      <label className="block text-sm text-gray-600 mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="flex-1"
        />
        <span className="w-12 text-right font-medium">{value.toFixed(1)}</span>
      </div>
    </div>
  );
}
```

</details>

---

## Quiz

1. **What does "use client" do?**
   - A) Runs the component on the server
   - B) Marks the component as a Client Component that runs in the browser
   - C) Enables server-side rendering
   - D) Disables JavaScript

2. **When does useMemo recompute its value?**
   - A) On every render
   - B) Never
   - C) When any of its dependencies change
   - D) When the component mounts

3. **Why use useDebounce for search input?**
   - A) To make the input faster
   - B) To prevent filtering on every keystroke
   - C) To validate input
   - D) To format the input

4. **What does "lifting state up" mean?**
   - A) Moving state to a database
   - B) Parent component owns state, children receive callbacks
   - C) Using global state
   - D) Storing state in URL

<details>
<summary>Answers</summary>

1. **B** - Marks the component as a Client Component
2. **C** - When any of its dependencies change
3. **B** - To prevent filtering on every keystroke (performance)
4. **B** - Parent component owns state, children receive callbacks

</details>

---

## What's Next?

In **Module 5**, you'll learn:
- Recharts library for data visualization
- Pie charts, bar charts, and histograms
- ResponsiveContainer for responsive charts
- Data transformation for chart formats

---

# Module 5: Charts & Visualization

## What You'll Learn

- Installing and using Recharts library
- Creating pie charts, bar charts, and histograms
- ResponsiveContainer for responsive sizing
- Data transformation with useMemo
- Chart composition with Recharts components

## Why It Matters

Data visualization helps users:
- **Quickly understand patterns** - A pie chart shows distribution at a glance
- **Compare values** - Bar charts make comparisons easy
- **Identify trends** - See where most signals cluster
- **Make decisions** - Visual data is more actionable

---

## Concept: Recharts Library

Recharts is a **composable** charting library built on React components:

```tsx
// Instead of imperative chart configuration:
const chart = new Chart(canvas, {
  type: 'pie',
  data: {...}
});

// You compose declaratively with JSX:
<PieChart>
  <Pie data={data} dataKey="value" />
  <Tooltip />
  <Legend />
</PieChart>
```

**Benefits:**
- React-native (components, not config objects)
- Declarative (describe what, not how)
- Composable (add/remove features by adding/removing components)
- Great TypeScript support

---

## Concept: Chart Types

| Chart Type | Use Case | Recharts Component |
|------------|----------|-------------------|
| Pie/Donut | Part-to-whole (BUY/SELL/HOLD distribution) | `<PieChart>` |
| Bar | Comparing categories (sector performance) | `<BarChart>` |
| Histogram | Value distribution (score distribution) | `<BarChart>` with binned data |
| Line | Trends over time | `<LineChart>` |
| Area | Cumulative values | `<AreaChart>` |

---

## Code Walkthrough

### File: `components/charts/SignalDistributionChart.tsx`

A donut chart showing BUY/SELL/HOLD distribution:

```tsx
"use client";

import { useMemo } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { Signal } from "@/lib/types";

const COLORS = {
  BUY: "#22c55e",   // green-500
  SELL: "#ef4444",  // red-500
  HOLD: "#f59e0b",  // amber-500
};

export function SignalDistributionChart({ signals }: { signals: Signal[] }) {
  // Transform signals to chart data format
  const chartData = useMemo(() => {
    const counts = { BUY: 0, SELL: 0, HOLD: 0 };

    signals.forEach((signal) => {
      if (signal.signal_type in counts) {
        counts[signal.signal_type as keyof typeof counts]++;
      }
    });

    return [
      { name: "BUY", value: counts.BUY, color: COLORS.BUY },
      { name: "HOLD", value: counts.HOLD, color: COLORS.HOLD },
      { name: "SELL", value: counts.SELL, color: COLORS.SELL },
    ].filter((item) => item.value > 0);
  }, [signals]);

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={40}      // Makes it a donut
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
```

**Key Components:**
- `ResponsiveContainer` - Makes chart resize with parent
- `PieChart` - Container for pie/donut charts
- `Pie` - The actual pie with data
- `Cell` - Individual slice styling
- `Tooltip` - Hover details
- `Legend` - Color key

### File: `components/charts/ScoreHistogramChart.tsx`

A bar chart showing score distribution:

```tsx
"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";

export function ScoreHistogramChart({
  signals,
  buyThreshold = 0.4,
  sellThreshold = -0.4,
}: ScoreHistogramChartProps) {
  // Bin signals into buckets from -1 to 1
  const chartData = useMemo(() => {
    const buckets = [];
    for (let i = -1; i < 1; i += 0.2) {
      buckets.push({
        label: i.toFixed(1),
        min: i,
        max: i + 0.2,
        count: 0,
        color: getColorForBucket(i, buyThreshold, sellThreshold),
      });
    }

    signals.forEach((signal) => {
      const score = signal.total_score;
      if (score === undefined) return;

      const bucketIndex = buckets.findIndex(
        (b) => score >= b.min && score < b.max
      );
      if (bucketIndex >= 0) buckets[bucketIndex].count++;
    });

    return buckets;
  }, [signals, buyThreshold, sellThreshold]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="label" />
        <YAxis />
        <Tooltip />

        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Bar>

        {/* Threshold reference lines */}
        <ReferenceLine x={buyThreshold.toFixed(1)} stroke="#22c55e" label="BUY" />
        <ReferenceLine x={sellThreshold.toFixed(1)} stroke="#ef4444" label="SELL" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

**Key Components:**
- `BarChart` - Container for bar charts
- `CartesianGrid` - Background grid lines
- `XAxis`, `YAxis` - Chart axes
- `Bar` - The bars themselves
- `ReferenceLine` - Threshold indicators

### File: `components/charts/SectorPerformanceChart.tsx`

A horizontal bar chart for sector comparison:

```tsx
<BarChart
  data={chartData}
  layout="vertical"      // Horizontal bars
  margin={{ left: 100 }}  // Room for sector names
>
  <XAxis type="number" domain={[-1, 1]} />
  <YAxis type="category" dataKey="sector" width={90} />
  <ReferenceLine x={0} stroke="#374151" />
  <Bar dataKey="avgScore">
    {chartData.map((entry, index) => (
      <Cell key={`cell-${index}`} fill={entry.color} />
    ))}
  </Bar>
</BarChart>
```

**Note:** `layout="vertical"` swaps axes for horizontal bars.

---

## Files Created in Module 5

| File | Purpose |
|------|---------|
| `components/charts/SignalDistributionChart.tsx` | Donut chart of signal types |
| `components/charts/ScoreHistogramChart.tsx` | Histogram of score distribution |
| `components/charts/SectorPerformanceChart.tsx` | Horizontal bar chart by sector |
| `components/charts/index.ts` | Barrel export file |
| `app/charts/page.tsx` | Charts dashboard page |

---

## Key Takeaways

1. **Recharts uses React components** - Compose charts declaratively
2. **ResponsiveContainer** - Required for responsive charts
3. **useMemo for data transformation** - Efficient chart data computation
4. **Cell for individual styling** - Color each bar/slice differently
5. **ReferenceLine** - Add threshold indicators
6. **layout="vertical"** - For horizontal bar charts

---

## Exercise

Create a `<ConfidenceDistributionChart>` that shows how many signals fall into confidence ranges (0-25%, 25-50%, 50-75%, 75-100%):

<details>
<summary>Solution</summary>

```tsx
"use client";

import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Signal } from "@/lib/types";

export function ConfidenceDistributionChart({ signals }: { signals: Signal[] }) {
  const chartData = useMemo(() => {
    const buckets = [
      { label: "0-25%", min: 0, max: 0.25, count: 0 },
      { label: "25-50%", min: 0.25, max: 0.5, count: 0 },
      { label: "50-75%", min: 0.5, max: 0.75, count: 0 },
      { label: "75-100%", min: 0.75, max: 1, count: 0 },
    ];

    signals.forEach((signal) => {
      const confidence = signal.confidence;
      const bucket = buckets.find(
        (b) => confidence >= b.min && confidence < b.max
      );
      if (bucket) bucket.count++;
    });

    return buckets;
  }, [signals]);

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={chartData}>
        <XAxis dataKey="label" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

</details>

---

## Quiz

1. **Why do charts need "use client"?**
   - A) Charts need database access
   - B) Charts use browser APIs (Canvas, SVG) and React hooks
   - C) Charts are faster on the client
   - D) Server-side rendering doesn't support charts

2. **What does ResponsiveContainer do?**
   - A) Makes the chart animate
   - B) Makes the chart resize with its parent element
   - C) Adds responsive breakpoints
   - D) Enables touch events

3. **Why use useMemo for chart data?**
   - A) Charts require memoized data
   - B) To avoid recalculating data on every render
   - C) To store data in localStorage
   - D) To enable animations

4. **How do you create horizontal bars in Recharts?**
   - A) `orientation="horizontal"`
   - B) `layout="vertical"`
   - C) `direction="horizontal"`
   - D) `rotate={90}`

<details>
<summary>Answers</summary>

1. **B** - Charts use browser APIs and React hooks (useState, useEffect)
2. **B** - Makes the chart resize with its parent element
3. **B** - To avoid recalculating data on every render (performance)
4. **B** - `layout="vertical"` swaps the axes

</details>

---

## What's Next?

In **Module 6**, you'll learn:
- Setting up LangChain.js
- Connecting to Ollama for local LLM
- Creating a simple chat interface
- Prompt templates and chains

---

# Module 6: AI Chat with Vercel AI SDK

## What You'll Learn

- Next.js API Routes for AI endpoints
- Vercel AI SDK for streaming responses
- The useChat hook for chat interfaces
- System prompts for AI context
- Edge Runtime for fast responses

## Why It Matters

AI-powered chat interfaces need:
- **Streaming** - Show responses as they're generated
- **State management** - Track conversation history
- **Error handling** - Handle API failures gracefully
- **Good UX** - Loading states, auto-scroll, etc.

The Vercel AI SDK handles all of this with minimal code!

---

## Concept: Vercel AI SDK

The Vercel AI SDK provides:

```tsx
// Backend: streamText for streaming responses
import { streamText } from "ai";

const result = streamText({
  model: openai("gpt-3.5-turbo"),
  messages: [...],
});

return result.toDataStreamResponse();

// Frontend: useChat hook for state management
import { useChat } from "ai/react";

const { messages, input, handleSubmit } = useChat();
```

**Benefits:**
- Automatic streaming handling
- Built-in state management
- Works with multiple AI providers
- TypeScript support

---

## Concept: API Routes in Next.js

API routes are server-side endpoints:

```
app/
├── api/
│   └── chat/
│       └── route.ts    <- POST /api/chat
```

```tsx
// app/api/chat/route.ts
export async function POST(req: Request) {
  const { messages } = await req.json();
  // Process and return response
}
```

**Key points:**
- Export named functions: GET, POST, PUT, DELETE
- Receive standard Request object
- Return standard Response object
- Can use Edge Runtime for faster responses

---

## Code Walkthrough

### File: `app/api/chat/route.ts`

The API route that handles chat requests:

```tsx
import { streamText, convertToCoreMessages } from "ai";
import { createOpenAI } from "@ai-sdk/openai";

// Use Edge Runtime for streaming
export const runtime = "edge";

// Create OpenAI client
const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// System prompt for AI context
const SYSTEM_PROMPT = `You are a trading signal analyst...`;

export async function POST(req: Request) {
  const { messages } = await req.json();

  // streamText handles streaming automatically
  const result = streamText({
    model: openai("gpt-3.5-turbo"),
    system: SYSTEM_PROMPT,
    messages: convertToCoreMessages(messages),
    maxTokens: 1000,
    temperature: 0.7,
  });

  // Return streaming response
  return result.toDataStreamResponse();
}
```

**Key functions:**
- `streamText` - Generates streaming AI response
- `convertToCoreMessages` - Converts messages to AI SDK format
- `toDataStreamResponse` - Creates streaming Response

### File: `components/chat/Chat.tsx`

The main chat interface:

```tsx
"use client";

import { useChat } from "ai/react";

export function Chat() {
  // useChat handles everything!
  const {
    messages,         // Array of messages
    input,            // Current input text
    handleInputChange, // Handler for input changes
    handleSubmit,     // Handler for form submission
    isLoading,        // Is AI responding?
    error,            // Any error
  } = useChat({
    api: "/api/chat",  // API endpoint
    initialMessages: [
      {
        id: "welcome",
        role: "assistant",
        content: "Hello! How can I help?",
      },
    ],
  });

  return (
    <div>
      {/* Messages list */}
      {messages.map((msg) => (
        <div key={msg.id}>
          <strong>{msg.role}:</strong> {msg.content}
        </div>
      ))}

      {/* Input form */}
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={handleInputChange}
          disabled={isLoading}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

**The useChat hook provides:**
- `messages` - All messages in the conversation
- `input` - Controlled input value
- `handleInputChange` - Updates input on typing
- `handleSubmit` - Sends message and handles streaming
- `isLoading` - True while AI is responding
- `error` - Any error that occurred

### File: `components/chat/ChatMessage.tsx`

Individual message display:

```tsx
import type { Message } from "ai";

export function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={isUser ? "justify-end" : "justify-start"}>
      <div className={isUser ? "bg-blue-600 text-white" : "bg-gray-100"}>
        <div className="text-xs">{isUser ? "You" : "Assistant"}</div>
        <div>{message.content}</div>
      </div>
    </div>
  );
}
```

---

## Environment Variables

Create `.env.local` in the frontend directory:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-api-key

# For local Ollama (optional)
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama2
```

---

## Files Created in Module 6

| File | Purpose |
|------|---------|
| `app/api/chat/route.ts` | API route for chat |
| `components/chat/Chat.tsx` | Main chat interface |
| `components/chat/ChatMessage.tsx` | Message display |
| `components/chat/ChatInput.tsx` | Input form |
| `components/chat/index.ts` | Barrel exports |
| `app/chat/page.tsx` | Chat page |

---

## Key Takeaways

1. **API Routes** - Server endpoints in `app/api/`
2. **Edge Runtime** - Faster cold starts and streaming
3. **streamText** - AI SDK function for streaming
4. **useChat hook** - Handles all chat state and streaming
5. **System prompts** - Give AI context about your domain
6. **Message types** - user, assistant, system

---

## Exercise

Add a "clear chat" button that resets the conversation:

<details>
<summary>Hint</summary>

useChat returns a `setMessages` function you can use to clear messages.

</details>

<details>
<summary>Solution</summary>

```tsx
const { messages, setMessages, ...rest } = useChat();

function clearChat() {
  setMessages([
    {
      id: "welcome",
      role: "assistant",
      content: "Chat cleared. How can I help?",
    },
  ]);
}

<button onClick={clearChat}>Clear Chat</button>
```

</details>

---

## Quiz

1. **What does the Edge Runtime provide?**
   - A) Database access
   - B) Faster cold starts and built-in streaming
   - C) File system access
   - D) WebSocket support

2. **What does useChat return?**
   - A) Just the messages array
   - B) Messages, input state, handlers, and loading state
   - C) Only the API endpoint
   - D) The AI model configuration

3. **What is a system prompt?**
   - A) User's first message
   - B) AI's first response
   - C) Hidden context that shapes AI behavior
   - D) Error message

4. **What does streamText return?**
   - A) A string
   - B) A Promise
   - C) A streaming result that can be converted to Response
   - D) An array of messages

<details>
<summary>Answers</summary>

1. **B** - Faster cold starts and built-in streaming support
2. **B** - Messages, input state, handlers, and loading state
3. **C** - Hidden context that shapes AI behavior
4. **C** - A streaming result that can be converted to Response

</details>

---

## What's Next?

In **Module 7**, you'll learn:
- Generative UI with AI-rendered components
- Tool calling for structured data
- Multi-step AI workflows
- Function calling for backend integration

---

# Module 7: Generative UI - AI-Rendered Components

## What You'll Learn

- What "Generative UI" means and why it's powerful
- Creating reusable components for AI-generated content
- Type-safe props for AI-rendered components
- Building a component library for trading data visualization
- Compound component patterns for complex displays

## Why It Matters

**Generative UI** is a paradigm where AI doesn't just return text—it returns **structured data that renders as rich UI components**. Instead of the AI saying "AAPL has a BUY signal with 75% confidence", it can return data that renders as a beautiful card with colors, icons, and visual indicators.

This creates a much better user experience:

```
Traditional AI Chat:          Generative UI:
-------------------          -------------
"AAPL: BUY signal,           ┌─────────────────────┐
confidence 75%,              │ 🍎 AAPL             │
RSI is 45, price             │ ███████░░░ 75% BUY  │
increased 2.3%"              │ RSI: 45  ▲ +2.3%    │
                             └─────────────────────┘
```

---

## Concept: What is Generative UI?

Traditional AI responses are plain text. With Generative UI:

1. **AI returns structured data** (JSON with specific fields)
2. **React components render the data** as rich UI
3. **Type safety ensures** the data matches what components expect

```tsx
// Instead of:
"GP stock has a BUY signal"

// AI returns:
{ type: "stock-card", ticker: "GP", signal: "BUY", confidence: 0.82 }

// Which renders as a beautiful StockCard component!
```

### The Component Library Pattern

We create a library of components that can be:
- Used standalone in our app
- Rendered by AI responses
- Combined in complex layouts

```
components/generative-ui/
├── StockCard.tsx        # Full stock display card
├── SignalBadge.tsx      # Inline signal indicator
├── IndicatorDisplay.tsx # Visual gauge for indicators
├── SignalsList.tsx      # List of multiple signals
└── index.ts             # Barrel export
```

---

## Code Walkthrough

### File: `components/generative-ui/StockCard.tsx`

A rich, self-contained card for displaying stock information:

```tsx
/**
 * StockCard Props Interface
 *
 * LEARNING NOTE:
 * We define explicit props so the AI knows exactly what
 * data to provide. Each prop is optional with sensible
 * defaults, making the component flexible.
 */
interface StockCardProps {
  ticker: string;              // Required: "GP", "AAPL"
  name?: string;               // Optional: "Grameenphone Ltd."
  price?: number;              // Current price
  change?: number;             // Percentage change (-5.2 to +5.2)
  signal?: "BUY" | "SELL" | "HOLD";
  confidence?: number;         // 0 to 1 (0% to 100%)
  rsi?: number;                // RSI indicator value
  sector?: string;             // "Telecom", "Bank", etc.
}
```

**Key Design Decisions:**

1. **String union for signal**: `"BUY" | "SELL" | "HOLD"` - TypeScript ensures only valid values
2. **Optional props with defaults**: Component works with minimal data
3. **Normalized confidence**: 0-1 range, displayed as percentage

```tsx
export function StockCard({
  ticker,
  name,
  price,
  change,
  signal,
  confidence,
  rsi,
  sector,
}: StockCardProps) {
  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="pb-2">
        {/* Header with ticker and sector */}
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-bold">{ticker}</CardTitle>
          {sector && (
            <span className="text-xs bg-gray-100 px-2 py-1 rounded">
              {sector}
            </span>
          )}
        </div>
        {name && <CardDescription>{name}</CardDescription>}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Price and change - color-coded */}
        {price !== undefined && (
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold">৳{price.toFixed(2)}</span>
            {change !== undefined && (
              <span className={cn(
                "flex items-center text-sm font-medium",
                change >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {change >= 0 ? <TrendingUp /> : <TrendingDown />}
                {Math.abs(change).toFixed(2)}%
              </span>
            )}
          </div>
        )}

        {/* Signal badge and confidence */}
        {signal && (
          <div className="flex items-center justify-between">
            <SignalBadge type={signal} />
            {confidence !== undefined && (
              <span className="text-sm text-gray-500">
                {(confidence * 100).toFixed(0)}% confidence
              </span>
            )}
          </div>
        )}

        {/* RSI indicator with visual bar */}
        {rsi !== undefined && (
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>RSI</span>
              <span className={cn(
                rsi > 70 ? "text-red-600" :
                rsi < 30 ? "text-green-600" : "text-gray-600"
              )}>
                {rsi.toFixed(1)}
              </span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={cn(
                  "h-full transition-all",
                  rsi > 70 ? "bg-red-500" :
                  rsi < 30 ? "bg-green-500" : "bg-blue-500"
                )}
                style={{ width: `${rsi}%` }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

---

### File: `components/generative-ui/SignalBadge.tsx`

A compact, inline badge for signals:

```tsx
interface SignalBadgeProps {
  type: "BUY" | "SELL" | "HOLD";
  score?: number;              // Optional score to display
  size?: "sm" | "md" | "lg";   // Size variants
}

export function SignalBadge({ type, score, size = "md" }: SignalBadgeProps) {
  // Configuration object for each signal type
  const config = {
    BUY: {
      bg: "bg-green-100",
      text: "text-green-800",
      icon: TrendingUp,
    },
    SELL: {
      bg: "bg-red-100",
      text: "text-red-800",
      icon: TrendingDown,
    },
    HOLD: {
      bg: "bg-yellow-100",
      text: "text-yellow-800",
      icon: Minus,
    },
  };

  const { bg, text, icon: Icon } = config[type];

  return (
    <span className={cn(
      "inline-flex items-center gap-1 rounded-full font-medium",
      bg, text,
      size === "sm" && "px-2 py-0.5 text-xs",
      size === "md" && "px-3 py-1 text-sm",
      size === "lg" && "px-4 py-1.5 text-base"
    )}>
      <Icon className={cn(
        size === "sm" && "h-3 w-3",
        size === "md" && "h-4 w-4",
        size === "lg" && "h-5 w-5"
      )} />
      {type}
      {score !== undefined && ` (${(score * 100).toFixed(0)}%)`}
    </span>
  );
}
```

**Learning Points:**

1. **Configuration object pattern**: All variants defined in one place
2. **Size variants**: Same component, different sizes
3. **Conditional rendering**: Score only shown if provided

---

### File: `components/generative-ui/IndicatorDisplay.tsx`

A visual gauge for any indicator value:

```tsx
interface IndicatorDisplayProps {
  name: string;                    // "RSI", "MACD", "ADX"
  value: number;                   // Current value
  min?: number;                    // Minimum of range (default: 0)
  max?: number;                    // Maximum of range (default: 100)
  description?: string;            // Tooltip/helper text
  warningThreshold?: number;       // Yellow zone starts
  dangerThreshold?: number;        // Red zone starts
  higherIsBetter?: boolean;        // Affects color logic
}

export function IndicatorDisplay({
  name,
  value,
  min = 0,
  max = 100,
  description,
  warningThreshold,
  dangerThreshold,
  higherIsBetter = true,
}: IndicatorDisplayProps) {
  // Calculate percentage position
  const percentage = ((value - min) / (max - min)) * 100;
  const clampedPercentage = Math.max(0, Math.min(100, percentage));

  // Determine color based on thresholds
  const getColor = () => {
    if (dangerThreshold !== undefined) {
      const inDanger = higherIsBetter
        ? value <= dangerThreshold
        : value >= dangerThreshold;
      if (inDanger) return "bg-red-500";
    }
    if (warningThreshold !== undefined) {
      const inWarning = higherIsBetter
        ? value <= warningThreshold
        : value >= warningThreshold;
      if (inWarning) return "bg-yellow-500";
    }
    return "bg-green-500";
  };

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="font-medium">{name}</span>
        <span className="text-lg font-bold">{value.toFixed(1)}</span>
      </div>

      {/* Visual progress bar */}
      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={cn("h-full transition-all duration-300", getColor())}
          style={{ width: `${clampedPercentage}%` }}
        />
      </div>

      {/* Min/Max labels */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>{min}</span>
        <span>{max}</span>
      </div>

      {description && (
        <p className="text-sm text-gray-600">{description}</p>
      )}
    </div>
  );
}
```

---

### File: `components/generative-ui/SignalsList.tsx`

Display multiple signals in a compact list:

```tsx
interface SignalItem {
  ticker: string;
  signal: "BUY" | "SELL" | "HOLD";
  score: number;
  sector?: string;
}

interface SignalsListProps {
  signals: SignalItem[];
  title?: string;
  limit?: number;          // Show only first N items
}

export function SignalsList({
  signals,
  title = "Trading Signals",
  limit,
}: SignalsListProps) {
  const displaySignals = limit ? signals.slice(0, limit) : signals;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>
          Showing {displaySignals.length} of {signals.length} signals
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="divide-y">
          {displaySignals.map((item, index) => (
            <div
              key={`${item.ticker}-${index}`}
              className="flex items-center justify-between py-3"
            >
              <div>
                <span className="font-medium">{item.ticker}</span>
                {item.sector && (
                  <span className="ml-2 text-xs text-gray-500">
                    {item.sector}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">
                  {(item.score * 100).toFixed(0)}%
                </span>
                <SignalBadge type={item.signal} size="sm" />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

---

### File: `components/generative-ui/index.ts`

Barrel export for clean imports:

```tsx
/**
 * Barrel Export Pattern
 *
 * LEARNING NOTE:
 * This file re-exports all components from a single location.
 * Instead of:
 *   import { StockCard } from "./generative-ui/StockCard";
 *   import { SignalBadge } from "./generative-ui/SignalBadge";
 *
 * You can do:
 *   import { StockCard, SignalBadge } from "@/components/generative-ui";
 */
export { StockCard } from "./StockCard";
export { SignalBadge } from "./SignalBadge";
export { IndicatorDisplay } from "./IndicatorDisplay";
export { SignalsList } from "./SignalsList";
```

---

## Demo Page: `app/components/page.tsx`

A page showcasing all generative UI components:

```tsx
import {
  StockCard,
  SignalBadge,
  IndicatorDisplay,
  SignalsList,
} from "@/components/generative-ui";

export default function ComponentsPage() {
  // Sample data - in real app, this comes from AI or API
  const sampleSignals = [
    { ticker: "GP", signal: "BUY" as const, score: 0.82, sector: "Telecom" },
    { ticker: "BATBC", signal: "SELL" as const, score: 0.65, sector: "Tobacco" },
    { ticker: "SQURPHARMA", signal: "HOLD" as const, score: 0.45, sector: "Pharma" },
  ];

  return (
    <div className="container mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold">Generative UI Components</h1>

      {/* StockCard examples */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Stock Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StockCard
            ticker="GP"
            name="Grameenphone Ltd."
            price={452.30}
            change={2.45}
            signal="BUY"
            confidence={0.82}
            rsi={45}
            sector="Telecom"
          />
          {/* More cards... */}
        </div>
      </section>

      {/* SignalBadge examples */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Signal Badges</h2>
        <div className="flex gap-4 flex-wrap">
          <SignalBadge type="BUY" />
          <SignalBadge type="SELL" score={0.75} />
          <SignalBadge type="HOLD" size="lg" />
        </div>
      </section>

      {/* IndicatorDisplay examples */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Indicators</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <IndicatorDisplay
            name="RSI"
            value={65}
            warningThreshold={70}
            dangerThreshold={80}
            higherIsBetter={false}
            description="Relative Strength Index"
          />
        </div>
      </section>

      {/* SignalsList example */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Signals List</h2>
        <SignalsList signals={sampleSignals} />
      </section>
    </div>
  );
}
```

---

## Exercise: Create a MarketOverview Component

Build a new component that displays overall market status:

```tsx
// Your task: Create components/generative-ui/MarketOverview.tsx

interface MarketOverviewProps {
  totalStocks: number;
  buySignals: number;
  sellSignals: number;
  holdSignals: number;
  marketSentiment: "bullish" | "bearish" | "neutral";
  topGainer?: { ticker: string; change: number };
  topLoser?: { ticker: string; change: number };
}

// Requirements:
// 1. Display a summary card with signal counts
// 2. Show market sentiment with appropriate colors
// 3. Highlight top gainer and loser if provided
// 4. Use existing SignalBadge component for signal indicators
```

**Hints:**
- Use the Card components from shadcn/ui
- Reference the StockCard pattern for structure
- Consider using a pie chart or progress bars for signal distribution

---

## Quiz: Generative UI Concepts

**Question 1**: Why do we use TypeScript interfaces for component props?

A) To make the code longer
B) To ensure AI provides correctly structured data
C) TypeScript is required by Next.js
D) For better performance

<details>
<summary>Answer</summary>
**B) To ensure AI provides correctly structured data**

TypeScript interfaces act as a contract. When AI generates component data, the types ensure it matches what the component expects. This catches errors at compile time rather than runtime.
</details>

**Question 2**: What is the purpose of a barrel export file (index.ts)?

A) To reduce bundle size
B) To hide implementation details
C) To simplify imports from multiple files
D) To add TypeScript support

<details>
<summary>Answer</summary>
**C) To simplify imports from multiple files**

A barrel export file re-exports everything from a directory, allowing you to import multiple components with a single import statement instead of separate imports for each file.
</details>

**Question 3**: Why do we use `"BUY" | "SELL" | "HOLD"` instead of just `string`?

A) It's faster at runtime
B) It documents the valid values and catches typos at compile time
C) Strings don't work with React
D) It's required by Tailwind CSS

<details>
<summary>Answer</summary>
**B) It documents the valid values and catches typos at compile time**

String literal unions restrict the type to only those specific strings. If the AI or your code tries to use "Buy" (wrong case) or "BUYING" (wrong word), TypeScript will show an error.
</details>

---

## Key Takeaways

1. **Generative UI** = AI returns structured data → React renders rich components
2. **Type-safe props** ensure AI provides valid data
3. **Component library pattern** enables reuse across app and AI responses
4. **Barrel exports** simplify importing from component directories
5. **Configuration objects** keep variant logic clean and centralized
6. **Size variants** (`sm`, `md`, `lg`) provide flexible component sizing

---

## Next Steps

In Module 8, you'll learn:
- Performance optimization techniques
- Error boundaries and fallback UI
- Loading states and skeletons
- Production build configuration
- Testing strategies

---

# Module 8: Production Polish

## What You'll Learn

- Error boundaries and graceful error handling
- Loading states with skeleton components
- Performance optimization techniques
- Responsive design patterns
- Accessibility best practices
- Production build configuration

## Why It Matters

A polished application provides a professional user experience even when things go wrong. Users should never see a blank screen or cryptic error messages. Loading states prevent confusion, and performance optimizations ensure fast interactions.

---

## Concept: Error Boundaries

React error boundaries catch JavaScript errors in their child component tree and display a fallback UI.

```tsx
// File: components/ErrorBoundary.tsx
"use client";

import { Component, ReactNode } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to error reporting service
    console.error("Error caught by boundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="border-red-200 bg-red-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-700">
              <AlertTriangle className="h-5 w-5" />
              Something went wrong
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-red-600 mb-4">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <Button
              variant="outline"
              onClick={() => this.setState({ hasError: false })}
            >
              Try again
            </Button>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}
```

**Usage:**
```tsx
<ErrorBoundary>
  <SignalsTable data={signals} />
</ErrorBoundary>
```

---

## Concept: Loading Skeletons

Skeleton components provide visual feedback while content loads:

```tsx
// File: components/ui/Skeleton.tsx
import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-gray-200",
        className
      )}
    />
  );
}

// File: components/StockCardSkeleton.tsx
export function StockCardSkeleton() {
  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="pb-2">
        <Skeleton className="h-6 w-20" />
        <Skeleton className="h-4 w-32 mt-1" />
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between">
          <Skeleton className="h-8 w-24" />
          <Skeleton className="h-6 w-16" />
        </div>
        <div className="flex justify-between">
          <Skeleton className="h-6 w-16" />
          <Skeleton className="h-4 w-24" />
        </div>
        <Skeleton className="h-2 w-full" />
      </CardContent>
    </Card>
  );
}
```

---

## Concept: Suspense for Data Loading

Next.js supports React Suspense for loading states:

```tsx
// File: app/signals/page.tsx
import { Suspense } from "react";
import { SignalsTable } from "@/components/SignalsTable";
import { SignalsTableSkeleton } from "@/components/SignalsTableSkeleton";

export default function SignalsPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Trading Signals</h1>

      <Suspense fallback={<SignalsTableSkeleton />}>
        <SignalsTable />
      </Suspense>
    </div>
  );
}
```

---

## Concept: Responsive Design

Use Tailwind's responsive prefixes for different screen sizes:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* 1 column on mobile, 2 on tablet, 3 on desktop */}
</div>

<div className="hidden md:block">
  {/* Only visible on tablet and larger */}
</div>

<div className="text-sm md:text-base lg:text-lg">
  {/* Responsive text sizing */}
</div>
```

**Common breakpoints:**
- `sm`: 640px (small tablets)
- `md`: 768px (tablets)
- `lg`: 1024px (laptops)
- `xl`: 1280px (desktops)
- `2xl`: 1536px (large screens)

---

## Concept: Accessibility

Ensure your components are accessible:

```tsx
// Good: Semantic HTML and ARIA attributes
<button
  aria-label="Close dialog"
  aria-pressed={isOpen}
  onClick={handleClose}
>
  <X className="h-4 w-4" />
</button>

// Good: Focus management
<Input
  id="ticker-search"
  aria-describedby="ticker-search-hint"
/>
<p id="ticker-search-hint" className="text-sm text-gray-500">
  Enter a stock ticker symbol like GP or BATBC
</p>

// Good: Color contrast and non-color indicators
<span className={cn(
  "flex items-center gap-1",
  signal === "BUY" && "text-green-700",  // Color
)}>
  {signal === "BUY" && <TrendingUp />}    // Also has icon indicator
  {signal}
</span>
```

---

## Concept: Performance Optimization

### 1. Dynamic Imports for Large Components

```tsx
import dynamic from "next/dynamic";

// Load chart component only when needed
const PriceChart = dynamic(
  () => import("@/components/PriceChart"),
  {
    loading: () => <ChartSkeleton />,
    ssr: false,  // Disable server-side rendering for browser-only libs
  }
);
```

### 2. Memoization

```tsx
import { memo, useMemo, useCallback } from "react";

// Memoize expensive components
const ExpensiveList = memo(function ExpensiveList({ items }) {
  return items.map(item => <Item key={item.id} {...item} />);
});

// Memoize expensive calculations
function SignalAnalysis({ signals }) {
  const statistics = useMemo(() => {
    return calculateStatistics(signals);  // Expensive
  }, [signals]);

  return <StatsDisplay stats={statistics} />;
}

// Memoize callbacks passed to children
function Parent() {
  const handleClick = useCallback((id: string) => {
    // handle click
  }, []);

  return <Child onClick={handleClick} />;
}
```

### 3. Image Optimization

```tsx
import Image from "next/image";

// Next.js Image component automatically optimizes images
<Image
  src="/logo.png"
  alt="Quant-Flow Logo"
  width={120}
  height={40}
  priority  // Load above-the-fold images eagerly
/>
```

---

## Putting It All Together

Here's a production-ready page with all polish applied:

```tsx
// File: app/dashboard/page.tsx
import { Suspense } from "react";
import dynamic from "next/dynamic";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { DashboardSkeleton } from "@/components/DashboardSkeleton";

// Dynamic import for heavy chart component
const SignalChart = dynamic(
  () => import("@/components/SignalChart"),
  { loading: () => <ChartSkeleton /> }
);

async function DashboardContent() {
  const signals = await fetchSignals();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <SignalsList signals={signals} />
      <SignalChart data={signals} />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <div className="container mx-auto p-4 md:p-6">
      <h1 className="text-xl md:text-2xl font-bold mb-4 md:mb-6">
        Trading Dashboard
      </h1>

      <ErrorBoundary>
        <Suspense fallback={<DashboardSkeleton />}>
          <DashboardContent />
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}
```

---

## Exercise: Add Loading and Error States

Take the SignalsTable component and enhance it with:

1. A skeleton loading state
2. Error boundary with retry functionality
3. Empty state when no signals match filters

**Hints:**
- Create SignalsTableSkeleton matching the table structure
- Use Suspense at the page level
- Add an empty state component for zero results

---

## Quiz: Production Patterns

**Question 1**: When should you use dynamic imports?

A) For every component
B) For components that are large and not needed on initial load
C) Only for images
D) Never in production

<details>
<summary>Answer</summary>
**B) For components that are large and not needed on initial load**

Dynamic imports split your bundle and load components only when needed. Use them for heavy components like charts, complex modals, or features behind user interaction.
</details>

**Question 2**: Why use Error Boundaries?

A) To make errors disappear
B) To prevent the entire app from crashing when one component fails
C) To speed up the app
D) They're required by React

<details>
<summary>Answer</summary>
**B) To prevent the entire app from crashing when one component fails**

Error boundaries catch errors in their child tree and display a fallback UI, preventing the entire application from becoming unusable due to one component's error.
</details>

---

## Key Takeaways

1. **Error boundaries** prevent crashes from propagating
2. **Skeleton loading** provides better UX than spinners
3. **Suspense** integrates loading states with React
4. **Dynamic imports** reduce initial bundle size
5. **Responsive design** ensures mobile usability
6. **Accessibility** makes your app usable by everyone
7. **Memoization** optimizes expensive renders

---

## Congratulations!

You've completed the Quant-Flow Frontend Learning Guide! You now understand:

- ✅ Next.js App Router and file-based routing
- ✅ React Server Components vs Client Components
- ✅ Data fetching from APIs
- ✅ Interactive filtering and state management
- ✅ Charts and data visualization
- ✅ AI chat with Vercel AI SDK
- ✅ Generative UI components
- ✅ Production polish and best practices

**Next Steps:**
- Build your own features on top of this foundation
- Explore the Vercel AI SDK documentation for more capabilities
- Consider adding authentication and user preferences
- Deploy to Vercel for production hosting

---

## Glossary

| Term | Definition |
|------|------------|
| **App Router** | Next.js routing system using the `app/` directory |
| **RSC** | React Server Component - runs on the server |
| **Client Component** | React component that runs in the browser |
| **Layout** | Wrapper component that persists across pages |
| **Metadata** | SEO information (title, description) |
| **Rewrite** | URL proxy that hides the destination |

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Vercel AI SDK](https://ai-sdk.dev/docs)
- [LangChain.js](https://js.langchain.com/docs)
