# WizWebUI Integration Issues - Next.js 16 + Turbopack

**Date**: 2026-01-04
**Status**: Blocked - Needs Resolution
**Component Library**: wizwebui v0.2.0
**Framework**: Next.js 16.1.1 (Turbopack)

---

## Summary

Created Holdings page using wizwebui components, but encountered build/runtime integration issues with Next.js 16's Turbopack bundler. The Holdings page code is complete and follows best practices, but cannot be tested until build system issues are resolved.

---

## What Was Accomplished

### ✅ Holdings Page Created
- **Location**: `app/dashboard/dse/[ticker]/holding/page.tsx`
- **URL Pattern**: `/dashboard/dse/BATBC/holding`
- **Components Used** (from wizwebui):
  - Card, CardHeader, CardBody
  - Table (with columns configuration)
  - Tabs, TabList, Tab, TabPanel
  - Grid, GridItem
  - Badge
  - Statistic

### ✅ Features Implemented
1. **Stock Price Header**: Company info, price display with Statistic component
2. **Tab Navigation**: 9 tabs (Holdings, Summary, Profile, Financials, etc.)
3. **3-Column Dashboard Layout**: Using Grid with responsive cols
4. **Holdings Summary Panel**:
   - CSS conic-gradient pie chart (from mockup)
   - Legend with percentages
5. **Shareholding Composition Table**:
   - Category, Holders, % Holding, Shares, Trend columns
   - Custom TrendBar component (not in wizwebui)
   - Badge chips for "Locked", "Smart Money" labels
6. **Market Statistics**: Right sidebar with basic stats
7. **Insider Actions**: Buy/Sell transaction display

### ✅ Configuration Updates
- **next.config.js**: Added Turbopack empty config, transpilePackages, webpack symlink support
- **Analytics**: Created placeholder `lib/analytics.ts` (was missing)

---

## Issues Encountered

### Issue 1: Next.js 16 Turbopack + npm link Incompatibility

**Problem**: Turbopack doesn't fully support npm linked packages with complex builds.

**Error Messages**:
```
Module not found: Can't resolve '@wizwebui/core'
```

**Root Cause**:
- Next.js 16 uses Turbopack by default (not Webpack)
- Turbopack has different module resolution for symlinked packages
- wizwebui exports CJS (`index.js`) and ESM (`index.mjs`) but Turbopack may be looking for `.cjs.js`
- `transpilePackages: ['@wizwebui/core']` should work but may have Turbopack bugs

**Attempted Solutions**:
1. ✅ Added `turbopack: {}` to silence webpack warning
2. ✅ Added `transpilePackages: ['@wizwebui/core']`
3. ✅ Added webpack config with `resolve.symlinks = true` (fallback)
4. ❌ Tried `turbopack.resolveAlias` but caused `require.resolve()` error
5. ❌ Server starts but returns 500 errors on all routes

**Status**: **Unresolved** - Needs deeper investigation or alternative approach

---

### Issue 2: wizwebui TypeScript Declaration Build Failures

**Problem**: Full `pnpm build` fails due to ~12 export errors in `index.ts`.

**Errors Fixed** (committed to wizwebui):
- ✅ `StepProps` → `StepItem` (Steps component)
- ✅ Removed `TourStep` export (not available)

**Remaining Errors** (documented but not fixed):
- `CascaderOption`, `FloatingButtonAction` not properly exported
- `useConfig`, `useComponentDefaults`, `WizConfig`, `ConfigContextValue`, `ComponentDefaults` from ConfigProvider
- `SegmentedOption`, `DescriptionsItem`, `DescriptionsItemProps`, `Step` from various components

**Workaround**: Use `pnpm build:no-dts` (builds JS without TypeScript declarations)

**Impact**:
- Library works for development (JS builds successfully)
- TypeScript autocomplete may be limited in IDE
- Not a blocker for functionality, but reduces DX

---

## Recommendations

### Option 1: Use File-based Installation (NOT npm link)

**Approach**:
```bash
cd apps/gibd-quant-web
npm install /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
```

**Pros**:
- Avoids npm link symlink issues
- May work better with Turbopack

**Cons**:
- Need to reinstall wizwebui after every change
- Slower development cycle

### Option 2: Use Webpack Instead of Turbopack

**Approach**:
```bash
npm run dev -- --webpack  # Force webpack mode
```

**Pros**:
- Webpack has mature symlink support
- `transpilePackages` works reliably

**Cons**:
- Slower build times than Turbopack
- Not the Next.js 16 default

### Option 3: Publish wizwebui to NPM Registry

**Approach**:
```bash
# In wizwebui
cd packages/core
pnpm build:no-dts
npm publish --registry=http://10.0.0.84:8090/api/v4/projects/PROJECT_ID/packages/npm/

# In gibd-quant-web
npm install @wizwebui/core@0.2.0 --registry=...
```

**Pros**:
- Production-ready approach
- No syml human help me do this faster . skip retrospective. fix the issue and give me summary + any info to update in wizwebui project + commit + migrate