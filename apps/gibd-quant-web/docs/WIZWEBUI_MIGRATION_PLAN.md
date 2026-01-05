# Guardian Investment BD - WizWebUI Migration Plan

**Date**: 2026-01-04
**Status**: Ready for Implementation
**Component Library**: wizwebui v0.2.0 (134 components)
**Installation Method**: Local package installation (Nexus registry disabled)

---

## Executive Summary

Migrate Guardian Investment BD website from custom HTML/CSS mockup to use the **wizwebui** component library for:
- ✅ Consistent design system across all pages
- ✅ Reduced maintenance burden (134 reusable components)
- ✅ Improved accessibility (WCAG compliant)
- ✅ Faster feature development
- ✅ Better theme support (light/dark mode)

**Estimated Timeline**: 5-7 days

---

## Current State Analysis

### Mockup Analysis
- **File**: [apps/gibd-quant-web/resources/mockup.html](../resources/mockup.html)
- **Lines of CSS**: ~293 lines
- **Key Features**:
  - Global header with mega menu
  - Stock price header
  - Tab navigation
  - 3-column dashboard grid (240px-1fr-300px)
  - Data tables, panels, badges
  - Pie chart (CSS conic-gradient)
  - Trend bars

### Current Implementation
- **Framework**: Next.js 16.1.1, React 19, TypeScript
- **Styling**: Tailwind CSS
- **Custom Components**: 5 in `components/ui/` (Button, Card, Badge, Input)
- **Issue**: No design system, inconsistent styling

---

## Installation Strategy (Nexus Registry Disabled)

### Option 1: npm link (Development - RECOMMENDED)

**Advantages:**
- ✅ Changes in wizwebui reflect immediately
- ✅ Easy to fix issues in wizwebui while developing
- ✅ No version management needed

**Setup:**
```bash
# 1. Build wizwebui
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
pnpm build

# 2. Create global link
npm link

# 3. Link in gibd-quant-web
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/apps/gibd-quant-web
npm link @wizwebui/core
```

**Unlink when done:**
```bash
npm unlink @wizwebui/core
npm install
```

### Option 2: Local File Installation (CI/CD)

**Advantages:**
- ✅ Works in Docker builds
- ✅ No global state

**Setup:**
```bash
cd apps/gibd-quant-web
npm install /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
```

**Update package.json:**
```json
{
  "dependencies": {
    "@wizwebui/core": "file:../../../../wizardsofts/wizwebui/packages/core"
  }
}
```

### Option 3: GitLab Package Registry (Production - FUTURE)

**When Nexus is restored or GitLab registry is configured:**
```bash
# Publish to GitLab
cd wizwebui/packages/core
npm publish --registry=http://10.0.0.84:8090/api/v4/projects/<PROJECT_ID>/packages/npm/

# Install from GitLab
npm install @wizwebui/core --registry=http://10.0.0.84:8090/api/v4/projects/<PROJECT_ID>/packages/npm/
```

---

## Component Mapping

| Mockup Section | HTML/CSS | WizWebUI Component | Priority |
|----------------|----------|-------------------|----------|
| Global Header | Custom | `Menu`, `SubMenu`, `MenuItem`, `Input` | High |
| Stock Header | Grid + CSS | `Card`, `Statistic`, `Badge`, `Grid` | High |
| Tabs | Custom CSS | `Tabs`, `TabList`, `Tab`, `TabPanel` | High |
| Dashboard Grid | CSS Grid | `Grid`, `GridItem` | Medium |
| Data Tables | HTML Table | `Table` | High |
| Panels/Cards | Custom CSS | `Card`, `CardHeader`, `CardBody` | High |
| Badges/Chips | Inline CSS | `Badge`, `Chip` | Medium |
| Price Display | Custom CSS | `Statistic` | Medium |
| Pie Chart | CSS Conic | **Keep as-is** (custom CSS) | Low |
| Trend Bars | DIVs | `Progress` or custom | Low |

---

## Implementation Phases

### Phase 0: Setup (Day 1 - Morning)

**Tasks:**
1. Create feature branch using worktree workflow
2. Install wizwebui via npm link
3. Add ThemeProvider to root layout
4. Save implementation plan to docs/

**Commands:**
```bash
# Create worktree
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git fetch gitlab
git checkout master
git pull gitlab master
git worktree add ../wizardsofts-megabuild-worktrees/feature-wizwebui-migration -b feature/wizwebui-migration

# Work in worktree
cd ../wizardsofts-megabuild-worktrees/feature-wizwebui-migration

# Build and link wizwebui
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
pnpm build
npm link

# Link in project
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-wizwebui-migration/apps/gibd-quant-web
npm link @wizwebui/core
```

**Update [apps/gibd-quant-web/app/layout.tsx](../app/layout.tsx):**
```tsx
import { ThemeProvider, ConfigProvider } from '@wizwebui/core';
import '@wizwebui/core/dist/styles.css'; // Import wizwebui styles

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <ThemeProvider>
          <ConfigProvider>
            <AuthProvider>
              {/* existing content */}
              <Header />
              <main>{children}</main>
              <Footer />
            </AuthProvider>
          </ConfigProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

### Phase 1: Header Migration (Day 1 - Afternoon)

**Goal**: Replace custom header with wizwebui Menu component

**File**: [apps/gibd-quant-web/components/layout/Header.tsx](../components/layout/Header.tsx)

**Changes:**
- Replace custom navigation with `Menu`, `MenuItem`, `SubMenu`
- Add mega menu dropdowns using nested `SubMenu`
- Replace search input with wizwebui `Input`
- Replace badge with wizwebui `Badge`

**Testing:**
```bash
npm run dev
# Visit http://localhost:3001
# Verify navigation works, mega menus display correctly
```

### Phase 2: Holdings Page (Day 2-3)

**Goal**: Create new Holdings page using only wizwebui components

**New File**: `apps/gibd-quant-web/app/holdings/[ticker]/page.tsx`

**Components Used:**
- `Card`, `CardHeader`, `CardBody`
- `Tabs`, `TabList`, `Tab`, `TabPanel`
- `Grid`, `GridItem`
- `Table`
- `Badge`, `Chip`
- `Statistic`

**Data Structure:**
```tsx
const shareholdingData = [
  {
    category: 'Sponsor / Director',
    chip: 'Locked',
    holders: 5,
    percentage: '72.91%',
    shares: '393,714,000',
    trend: [50, 50, 50, 50], // neutral trend
  },
  // ... more rows
];
```

**Testing:**
```bash
npm run dev
# Visit http://localhost:3001/holdings/BATBC
# Verify all sections render correctly
```

### Phase 3: Homepage Migration (Day 4)

**Goal**: Replace custom components with wizwebui

**File**: [apps/gibd-quant-web/app/page.tsx](../app/page.tsx)

**Changes:**
- Replace `@/components/ui/card` with `@wizwebui/core` imports
- Replace `@/components/ui/button` with wizwebui `Button`
- Replace `@/components/ui/badge` with wizwebui `Badge`

**Before:**
```tsx
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
```

**After:**
```tsx
import { Card, CardHeader, CardBody, Button, Badge } from '@wizwebui/core';
```

### Phase 4: Signals Page Migration (Day 5)

**Goal**: Migrate signals page to wizwebui

**File**: [apps/gibd-quant-web/app/signals/page.tsx](../app/signals/page.tsx)

**Changes:**
- Replace `SignalCard` custom component with wizwebui `Card`
- Use wizwebui `Table` for signal list
- Use wizwebui `Badge` for BUY/SELL/HOLD indicators

### Phase 5: Charts & Other Pages (Day 6)

**Goal**: Complete migration of remaining pages

**Files:**
- [apps/gibd-quant-web/app/charts/page.tsx](../app/charts/page.tsx)
- [apps/gibd-quant-web/app/multi-criteria/page.tsx](../app/multi-criteria/page.tsx)
- [apps/gibd-quant-web/app/chat/page.tsx](../app/chat/page.tsx)

**Note**: Keep Recharts for data visualization (wizwebui has charts but Recharts is already integrated)

### Phase 6: Cleanup & Testing (Day 7)

**Tasks:**
1. **Remove or deprecate old custom components:**
   ```bash
   # Option A: Delete
   rm apps/gibd-quant-web/components/ui/card.tsx
   rm apps/gibd-quant-web/components/ui/badge.tsx
   rm apps/gibd-quant-web/components/ui/button.tsx

   # Option B: Make them wrappers (gradual migration)
   # Update components/ui/card.tsx:
   export { Card, CardHeader, CardBody, CardFooter } from '@wizwebui/core';
   ```

2. **Run tests:**
   ```bash
   npm test
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

4. **Check bundle size:**
   ```bash
   npm run build
   # Review .next/build-manifest.json
   ```

5. **Manual QA:**
   - [ ] All pages load without errors
   - [ ] Navigation works (header, tabs)
   - [ ] Tables render correctly
   - [ ] Forms submit properly
   - [ ] Responsive design on mobile
   - [ ] Dark mode works (if implemented)
   - [ ] Accessibility (keyboard navigation, screen readers)

6. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: migrate to wizwebui component library

   - Replaced custom UI components with wizwebui
   - Added ThemeProvider and ConfigProvider
   - Created Holdings page with wizwebui components
   - Migrated Header, Homepage, Signals, Charts pages
   - Removed old custom components

   BREAKING CHANGE: All UI components now from @wizwebui/core

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

   git push gitlab feature/wizwebui-migration
   ```

7. **Create Merge Request in GitLab:**
   ```bash
   # Visit http://10.0.0.84:8090/wizardsofts/wizardsofts-megabuild/-/merge_requests/new
   # Title: "feat: Migrate to wizwebui component library"
   # Description: See WIZWEBUI_MIGRATION_PLAN.md for details
   # Assign reviewers
   ```

---

## Handling wizwebui Issues

**If you encounter issues with wizwebui components:**

### 1. Check Component Exists
```bash
ls /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core/src/components
```

### 2. Check Component Export
```bash
grep "export.*YourComponent" /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core/src/index.ts
```

### 3. Fix Issue in wizwebui

**Create feature branch in wizwebui:**
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui
git checkout -b fix/component-issue
# Make fixes
pnpm build
git add .
git commit -m "fix: resolve component issue"
git push origin fix/component-issue
```

**Rebuild and test in gibd-quant-web:**
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core
pnpm build

# If using npm link, changes reflect immediately
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-wizwebui-migration/apps/gibd-quant-web
npm run dev
```

### 4. Add Missing Component

**If component doesn't exist in wizwebui:**

```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core

# Create component
mkdir -p src/components/NewComponent
cat > src/components/NewComponent/NewComponent.tsx << 'EOF'
import React from 'react';

export interface NewComponentProps {
  children?: React.ReactNode;
  className?: string;
}

export const NewComponent: React.FC<NewComponentProps> = ({ children, className }) => {
  return <div className={className}>{children}</div>;
};
EOF

# Add tests
cat > src/components/NewComponent/NewComponent.test.tsx << 'EOF'
import { render } from '@testing-library/react';
import { NewComponent } from './NewComponent';

test('renders component', () => {
  const { container } = render(<NewComponent>Test</NewComponent>);
  expect(container.textContent).toBe('Test');
});
EOF

# Export from index.ts
echo "export { NewComponent } from './components/NewComponent/NewComponent';" >> src/index.ts
echo "export type { NewComponentProps } from './components/NewComponent/NewComponent';" >> src/index.ts

# Build
pnpm build

# Test
pnpm test
```

---

## Docker Configuration for CI/CD

**Issue**: npm link doesn't work in Docker builds

**Solution**: Use file path installation in Dockerfile

**Update [apps/gibd-quant-web/Dockerfile](../Dockerfile):**

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app

# Copy wizwebui package (CRITICAL for file: installation)
COPY ../../../../wizardsofts/wizwebui/packages/core /tmp/wizwebui-core

# Copy package files
COPY apps/gibd-quant-web/package*.json ./

# Install dependencies (will use /tmp/wizwebui-core for file: path)
RUN npm ci

# Build stage
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY apps/gibd-quant-web .

RUN npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]
```

**Update docker-compose.yml:**
```yaml
services:
  gibd-quant-web:
    build:
      context: .
      dockerfile: apps/gibd-quant-web/Dockerfile
    volumes:
      - /Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/packages/core:/tmp/wizwebui-core:ro
```

---

## Rollback Plan

**If migration fails or causes issues:**

### Option 1: Revert Commits
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild-worktrees/feature-wizwebui-migration
git log --oneline # Find commit before migration
git revert <commit-hash>
git push gitlab feature/wizwebui-migration
```

### Option 2: Abandon Feature Branch
```bash
cd /Users/mashfiqurrahman/Workspace/wizardsofts-megabuild
git worktree remove ../wizardsofts-megabuild-worktrees/feature-wizwebui-migration
git branch -D feature/wizwebui-migration
# Close MR in GitLab
```

### Option 3: Keep Old Components as Fallback
**Don't delete old components until migration is fully validated in production.**

---

## Success Metrics

**Before Migration:**
- Custom CSS: ~293 lines
- Custom Components: 5 components
- Theme Support: None
- Accessibility: Basic
- Maintenance: High (custom code)

**After Migration:**
- wizwebui Components: 134 available (using ~20)
- Theme Support: Light/dark mode ready
- Accessibility: WCAG 2.1 AA compliant
- Maintenance: Low (library maintained separately)
- Bundle Size: TBD (measure after Phase 6)

**KPIs:**
- [ ] All pages load without console errors
- [ ] Lighthouse Accessibility score ≥ 90
- [ ] Bundle size increase < 100KB
- [ ] Build time < 2 minutes
- [ ] Zero TypeScript errors
- [ ] 100% test coverage for new components

---

## References

- **wizwebui README**: `/Users/mashfiqurrahman/Workspace/wizardsofts/wizwebui/README.md`
- **Component Storybook**: Run `pnpm storybook` in wizwebui directory
- **Frontend Developer Skill**: `.claude/skills/frontend-developer.md`
- **Git Workflow**: [CLAUDE.md](../../CLAUDE.md) - Git Worktree section
- **Deployment Guidelines**: [apps/gibd-quant-web/CLAUDE.md](../CLAUDE.md)

---

## Next Steps

1. **Review this plan with team**
2. **Start Phase 0: Setup**
3. **Execute phases 1-6 sequentially**
4. **Create merge request when complete**
5. **Deploy to staging first, then production**

**Questions? Issues?**
- Check `.claude/skills/frontend-developer.md` for wizwebui usage
- Review wizwebui Storybook for component examples
- Test changes in wizwebui first, then in gibd-quant-web
