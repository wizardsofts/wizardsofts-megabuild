# Frontend Developer Skill

Expert in React, Next.js, Node.js, Redux, and modern frontend development with **mobile-first responsive design**.

## Core Principles

### 🎯 Mobile-First Design (MANDATORY)

**CRITICAL**: All designs MUST be mobile-first and fully responsive.

1. **Start with Mobile (320px+)**
   - Design for smallest screen first
   - Add complexity as screen size increases
   - Never assume desktop-only usage

2. **Responsive Breakpoints**
   ```css
   /* Tailwind CSS breakpoints */
   sm: 640px   /* Small tablets */
   md: 768px   /* Tablets */
   lg: 1024px  /* Laptops */
   xl: 1280px  /* Desktops */
   2xl: 1536px /* Large displays */
   ```

3. **Mobile-First Grid Patterns**
   ```tsx
   {/* ✅ CORRECT: Mobile first, then desktop */}
   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">

   {/* ❌ WRONG: Desktop first */}
   <div className="grid grid-cols-3 md:grid-cols-1">
   ```

4. **Touch-Friendly Targets**
   - Minimum tap target: 44×44px (Apple) / 48×48px (Material)
   - Add padding to links/buttons
   - Use proper spacing between interactive elements

5. **Responsive Typography**
   ```tsx
   {/* Scale text for readability */}
   <h1 className="text-2xl md:text-3xl lg:text-4xl">
   ```

## Expertise

- **React & Next.js**: Component architecture, hooks, App Router, server components
- **State Management**: Redux, Context API, Zustand
- **Responsive Design**: Mobile-first, Tailwind CSS, CSS Grid, Flexbox
- **Build Tools**: Webpack, Vite, Turbopack
- **TypeScript**: Advanced types, generics, type inference
- **Testing**: Jest, React Testing Library, Playwright (mobile viewports)
- **Performance**: Code splitting, lazy loading, SSR/SSG optimization, image optimization

## ⛔ CRITICAL: UI Component Governance Rules (2026-01-06)

**ABSOLUTE RULE: NEVER create custom UI components or custom UI rendering logic without explicit user written confirmation.**

This rule is non-negotiable and applies to all frontend work. The three-tier architecture is mandatory.

### Three-Tier Architecture (Mandatory)

```
TIER 1: UI Primitive Libraries
  @wizwebui/core - Button, Input, Card, Table, Tabs, Badge, etc.

TIER 2: Domain-Specific Libraries
  @wizchart/* - ChartRenderer, AddIndicatorPanel, TechnicalIndicators, etc.

TIER 3: Application Layer (Data & Configuration ONLY)
  ✅ API calls, state management, business logic
  ✅ Composing library components with data/callbacks
  ✅ Custom hooks for logic (NOT UI rendering)
  ❌ NO custom JSX/HTML rendering
  ❌ NO custom UI components
  ❌ NO inline styled components without library equivalents
```

### Component Library Integration

**CRITICAL RULE**: ALWAYS use component libraries (`@wizwebui/core` OR `@wizchart/*`). Creating custom UI components is STRICTLY PROHIBITED.

**Before writing ANY UI component:**
1. Check if `@wizwebui/core` has it (Button, Input, Card, Table, etc.)
2. Check if `@wizchart/*` has it (Chart, Indicator, etc.)
3. If NEITHER library has it → **STOP** and ask user for explicit approval
4. ONLY after approval → Extract to appropriate library

### When Library Component Doesn't Match Design

**MANDATORY Process**:

```
STEP 1: Try className override
  <Card className="border-gray-200 shadow-sm rounded" />

STEP 2: Check if existing props/variants support the design
  <Card variant="panel" />
  <Table density="compact" />

STEP 3: If no suitable variant exists, STOP and propose enhancement
  "Current Table doesn't support compact density. I propose adding
   a 'density' prop with 'default' | 'compact' | 'spacious' variants.

   Benefits:
   - Data tables need compact rows
   - Pricing tables need spacious rows
   - Comparison tables need default spacing

   Should I proceed with this enhancement?"

STEP 4: Wait for user approval

STEP 5: Implement enhancement in wizwebui library
  File: wizwebui/packages/core/src/components/Table/Table.tsx

STEP 6: Build and test wizwebui
  cd wizwebui/packages/core
  npm run build

STEP 7: Use enhanced component in project
  <Table density="compact" data={data} />
```

### Enhancement Requirements

All wizwebui enhancements MUST be:
- ✅ **Generic**: Works for multiple design systems (Material, Ant, Tailwind UI, etc.)
- ✅ **Reusable**: Benefits ALL wizwebui users, not just this project
- ✅ **Configurable**: Uses props/variants, NO hard-coded project-specific values
- ✅ **Framework-agnostic**: Works in any React app

❌ **NEVER**:
- Create custom components
- Add project-specific variants
- Hard-code mockup colors/spacing in library

✅ **ALWAYS**:
- Propose generic enhancements
- Get user approval first
- Implement in wizwebui library
- Document the enhancement

#### Installation (Local)
```bash
# Install from local workspace
cd apps/gibd-quant-web
npm install /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core

# OR use npm link for development
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
npm link
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/apps/gibd-quant-web
npm link @wizwebui/core
```

#### Available Components (134 total)

**Navigation:**
- Menu, MenuItem, SubMenu (mega menus)
- Navbar, Header
- Tabs, TabList, Tab, TabPanel
- Breadcrumb, Pagination

**Layout:**
- Grid, GridItem
- Container, Stack
- Card, CardHeader, CardBody, CardFooter
- Divider

**Data Display:**
- Table, TableBuilder
- List, ListItem
- Timeline, Collapse, Accordion
- Badge, Chip, Avatar

**Forms:**
- Input, Textarea, Select
- Checkbox, Radio, RadioGroup, Switch
- DatePicker, TimePicker, DateRange
- AutoComplete, ColorPicker

**Feedback:**
- Alert, Toast, Dialog, Modal
- Progress, Spinner, Skeleton
- Tooltip, Popconfirm

**Advanced:**
- Upload, Slider, Rate, Transfer
- Drawer, Affix, BackTop
- FloatingButton, Statistic

#### Theme Configuration

```tsx
import { ThemeProvider, ConfigProvider, defaultTheme } from '@wizwebui/core';

// Custom theme
const guardianTheme = {
  ...defaultTheme,
  colors: {
    ...defaultTheme.colors,
    primary: '#0056b3',
    success: '#28a745',
    danger: '#dc3545',
  },
};

// In layout.tsx
<ThemeProvider theme={guardianTheme}>
  <ConfigProvider>
    {children}
  </ConfigProvider>
</ThemeProvider>
```

#### Import Patterns

```tsx
// ✅ CORRECT - Use wizwebui
import { Card, CardHeader, CardBody, Button, Badge, Table } from '@wizwebui/core';

// ❌ WRONG - Don't create custom components
import { Card } from '@/components/ui/card';
```

#### Component Usage Examples

**Cards:**
```tsx
<Card>
  <CardHeader>Title</CardHeader>
  <CardBody>
    <p>Content here</p>
  </CardBody>
</Card>
```

**Tables:**
```tsx
<Table
  dataSource={data}
  columns={[
    { title: 'Name', dataIndex: 'name' },
    { title: 'Value', dataIndex: 'value', align: 'right' },
  ]}
  pagination={{ pageSize: 10 }}
/>
```

**Tabs:**
```tsx
<Tabs defaultActiveKey="1">
  <TabList>
    <Tab key="1">Summary</Tab>
    <Tab key="2">Details</Tab>
  </TabList>
  <TabPanel key="1">Summary content</TabPanel>
  <TabPanel key="2">Details content</TabPanel>
</Tabs>
```

**Grid Layout (Mobile-First):**
```tsx
{/* ✅ CORRECT: Responsive grid */}
<Grid cols={[1, 2, 3]} gap={[2, 4, 6]}>
  <GridItem>Column 1</GridItem>
  <GridItem>Column 2</GridItem>
  <GridItem>Column 3</GridItem>
</Grid>

{/* For complex layouts, use native CSS Grid with Tailwind */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[240px_1fr_300px] gap-4">
  <div>Sidebar</div>
  <div>Main Content</div>
  <div>Right Panel</div>
</div>
```

**Responsive Tables:**
```tsx
{/* Mobile: Stack rows vertically */}
{/* Desktop: Show full table */}
<div className="overflow-x-auto">
  <Table
    dataSource={data}
    columns={columns}
    className="min-w-full"
  />
</div>
```

### Mobile-First Layout Patterns

1. **Sidebar Navigation**
   ```tsx
   {/* Mobile: Hidden by default, toggle with hamburger */}
   {/* Desktop: Always visible */}
   <div className="hidden lg:block">Desktop Sidebar</div>
   <div className="lg:hidden">Mobile Menu Button</div>
   ```

2. **Card Grid**
   ```tsx
   <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
     {items.map(item => <Card key={item.id} />)}
   </div>
   ```

3. **Content Width**
   ```tsx
   {/* Mobile: Full width with padding */}
   {/* Desktop: Constrained max-width */}
   <div className="w-full px-4 md:px-6 lg:max-w-7xl lg:mx-auto">
     {content}
   </div>
   ```

### If Component Missing

**Before creating custom component:**

1. **Check wizwebui source:**
   ```bash
   ls /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core/src/components
   ```

2. **Check if it can be composed from existing components:**
   - Example: TrendBar = Progress + custom styling
   - Example: StockPrice = Statistic + Badge

3. **If truly missing, ADD to wizwebui library:**
   ```bash
   cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
   # Create component
   mkdir src/components/YourComponent
   # Add to src/index.ts
   # Build library
   pnpm build
   # Link to project
   npm link
   ```

4. **NEVER create one-off custom components in apps/gibd-quant-web/components/ui/**

### Accessibility Requirements

- All wizwebui components are WCAG compliant
- Always use semantic HTML
- Include ARIA labels for interactive elements
- Test with keyboard navigation
- Verify with screen readers

### Performance Best Practices

- Use Next.js dynamic imports for large components
- Implement code splitting at route level
- Lazy load below-the-fold content
- Optimize images with next/image
- Use React.memo for expensive renders

### Testing Standards

```tsx
// Component test example
import { render, screen } from '@testing-library/react';
import { Card, CardHeader } from '@wizwebui/core';

test('renders card with header', () => {
  render(
    <Card>
      <CardHeader>Test Header</CardHeader>
    </Card>
  );
  expect(screen.getByText('Test Header')).toBeInTheDocument();
});
```

## Next.js App Router Patterns

### File-based Routing
- `app/page.tsx` - Homepage
- `app/holdings/[ticker]/page.tsx` - Dynamic route
- `app/layout.tsx` - Root layout (persistent)

### Server vs Client Components
```tsx
// Server Component (default)
export default async function Page() {
  const data = await fetch('...');
  return <div>{data}</div>;
}

// Client Component (interactive)
'use client';
import { useState } from 'react';
export default function Interactive() {
  const [state, setState] = useState(0);
  return <button onClick={() => setState(s => s + 1)}>{state}</button>;
}
```

### Data Fetching
```tsx
// Server Component
async function getData() {
  const res = await fetch('https://api.example.com/data', {
    next: { revalidate: 60 } // ISR: revalidate every 60 seconds
  });
  return res.json();
}

// Client Component
import useSWR from 'swr';
const { data, error } = useSWR('/api/user', fetcher);
```

## State Management

### Context API (Preferred for Theme/Auth)
```tsx
const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

### Redux (For Complex State)
```tsx
import { configureStore } from '@reduxjs/toolkit';
import signalsReducer from './features/signals/signalsSlice';

export const store = configureStore({
  reducer: {
    signals: signalsReducer,
  },
});
```

## TypeScript Best Practices

```tsx
// Component Props
interface CardProps {
  title: string;
  children: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
  onClick?: () => void;
}

// Generics for reusable components
interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
}
```

## Deployment (GitLab CI/CD)

**CRITICAL**: Never deploy via SSH. Always use GitLab CI/CD.

```yaml
# .gitlab-ci.yml
build:
  script:
    - cd apps/gibd-quant-web
    - npm install
    - npm run build

deploy:
  script:
    - docker build -t gibd-quant-web .
    - docker-compose up -d
  only:
    - master
```

## Security Checklist

- [ ] Run `npm audit --audit-level=high` before every commit
- [ ] Validate all user inputs
- [ ] Sanitize data before rendering (prevent XSS)
- [ ] Use environment variables for secrets (never hardcode)
- [ ] Implement rate limiting on API routes
- [ ] Add CSRF protection for forms
- [ ] Use Content Security Policy headers

## Common Pitfalls to Avoid

**CRITICAL - ZERO TOLERANCE VIOLATIONS:**
1. **❌ ABSOLUTE: Creating custom UI components instead of using library components**
   - This triggers immediate refactoring
   - Includes: custom JSX rendering, inline styled elements, custom form fields
   - Always check wizwebui/wizchart FIRST

2. **❌ Creating custom UI logic without explicit user approval**
   - Custom button handlers, custom form logic, custom input rendering
   - All UI logic MUST be delegated to libraries

3. **❌ Composing custom components from scratch**
   - Example: Building custom card component from `<div>`
   - Solution: Use `<Card>` from `@wizwebui/core`

**OTHER PITFALLS:**
4. **❌ Mixing Client/Server components incorrectly**
5. **❌ Not handling loading/error states**
6. **❌ Forgetting to memoize expensive computations**
7. **❌ Not testing accessibility**
8. **❌ Deploying without running build locally first**

## Git Workflow

**MANDATORY**: Use feature branch workflow (see CLAUDE.md)

```bash
# Create worktree for feature
git worktree add ../wizardsofts-megabuild-worktrees/feature-wizwebui-migration -b feature/wizwebui-migration

# Work in worktree
cd ../wizardsofts-megabuild-worktrees/feature-wizwebui-migration

# Commit and push
git add .
git commit -m "feat: migrate to wizwebui components"
git push gitlab feature/wizwebui-migration
```

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `npm install` |
| Dev server | `npm run dev` (port 3001) |
| Build | `npm run build` |
| Test | `npm test` |
| Lint | `npm run lint` |
| Format | `npm run format` |

## Documentation

- **wizwebui README**: `/Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/README.md`
- **Storybook**: `cd wizwebui && pnpm storybook`
- **Next.js Docs**: https://nextjs.org/docs
- **React Docs**: https://react.dev

---

**When in doubt, prioritize:**
1. Use wizwebui components
2. Follow Next.js best practices
3. Ensure accessibility
4. Deploy via CI/CD only
