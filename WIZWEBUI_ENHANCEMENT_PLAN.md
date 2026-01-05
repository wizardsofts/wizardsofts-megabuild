# wizwebui Component Library Enhancement Plan

## Objective
Make wizwebui components flexible enough to support mockup-style designs **without creating custom components**.

## Constraint
**CRITICAL**: Do NOT create custom components. Enhance the generic wizwebui library to be configurable.

## Enhancement Strategy

### Phase 1: Card Component Enhancements

#### Current Limitation
wizwebui Card has default styling that can't be fully overridden via className.

#### Solution: Add Style Variants
**File**: `wizwebui/packages/core/src/components/Card/Card.tsx`

Add `variant` prop to support different card styles:

```tsx
interface CardProps {
  variant?: 'default' | 'panel' | 'minimal'
  // ... existing props
}

// Variants:
// 'default' - Current rounded card with shadow
// 'panel' - Flat panel with gray header (mockup style)
// 'minimal' - No styling, just structure
```

**Why Generic**: Different apps need different card styles (dashboard panels, product cards, etc.)

### Phase 2: CardHeader Component Enhancements

#### Current Limitation
CardHeader has default padding/background that doesn't match mockup's compact style.

#### Solution: Add Header Variants
**File**: `wizwebui/packages/core/src/components/Card/Card.tsx`

```tsx
interface CardHeaderProps {
  variant?: 'default' | 'compact' | 'minimal'
  uppercase?: boolean
  // ... existing props
}

// Variants:
// 'default' - Current padding/style
// 'compact' - Minimal padding (py-2 px-4)
// 'minimal' - No default styling
```

**Why Generic**: Headers need different densities (compact dashboards, spacious landing pages, etc.)

### Phase 3: Table Component Enhancements

#### Current Limitation
wizwebui Table has fixed padding, borders, font sizes.

#### Solution: Add Density Variants
**File**: `wizwebui/packages/core/src/components/Table/Table.tsx`

```tsx
interface TableProps {
  density?: 'default' | 'compact' | 'spacious'
  borderStyle?: 'default' | 'minimal' | 'none'
  // ... existing props
}

// Density:
// 'default' - Current padding (py-3)
// 'compact' - Minimal padding (py-2)
// 'spacious' - Extra padding (py-4)

// Border Style:
// 'default' - Current borders
// 'minimal' - Light borders (#f0f0f0)
// 'none' - No borders
```

**Why Generic**: Tables need different densities (data tables, pricing tables, etc.)

### Phase 4: Tabs Component Enhancements

#### Current Limitation
wizwebui Tabs may have default styling that differs from mockup's clean underline.

#### Solution: Add Tab Variants
**File**: `wizwebui/packages/core/src/components/Tabs/Tabs.tsx`

```tsx
interface TabsProps {
  variant?: 'default' | 'underline' | 'pills' | 'minimal'
  // ... existing props
}

// Variants:
// 'default' - Current style
// 'underline' - Clean underline only (mockup style)
// 'pills' - Pill-shaped tabs
// 'minimal' - No styling
```

**Why Generic**: Different tab styles for different UIs (navigation, settings, dashboards, etc.)

### Phase 5: Badge Component Enhancements

#### Current Limitation
Badge may have default sizing/padding that doesn't match mockup's chips.

#### Solution: Add Size/Style Variants
**File**: `wizwebui/packages/core/src/components/Badge/Badge.tsx`

```tsx
interface BadgeProps {
  size?: 'xs' | 'sm' | 'md' | 'lg'
  variant?: 'default' | 'pill' | 'minimal'
  // ... existing props
}

// Size:
// 'xs' - 0.75rem text, 2px 8px padding
// 'sm' - 0.875rem text
// 'md' - 1rem text
// 'lg' - 1.125rem text

// Variant:
// 'default' - Current style
// 'pill' - Rounded pill (10px border-radius)
// 'minimal' - No background
```

**Why Generic**: Badges used in many contexts (status indicators, categories, counts, etc.)

## Implementation Approach

### DO NOT:
❌ Create custom components for this project
❌ Add project-specific styling to wizwebui
❌ Hard-code mockup colors/spacing in library

### DO:
✅ Add **generic** variants that support multiple design systems
✅ Make components **configurable** via props
✅ Allow **className override** for edge cases
✅ Keep library **framework-agnostic** and **reusable**

## Testing Strategy

### 1. Test with Multiple Design Systems
Before merging wizwebui enhancements, test variants with:
- Mockup design (Holdings page)
- Material Design
- Ant Design
- Tailwind UI

If variants work for multiple design systems → Good generic solution

### 2. Component Library Philosophy
```
GOOD Generic Enhancement:
- Adds 'compact' density option
- Works for data tables, pricing tables, comparison tables
- Configurable via prop

BAD Project-Specific Enhancement:
- Adds 'mockup-style' variant
- Only works for this one design
- Hard-codes specific colors/spacing
```

## Updated CLAUDE.md Instructions

### Component Usage Policy

**CRITICAL RULE**: NEVER create custom components. Always enhance wizwebui library instead.

#### When You Need Different Styling:

```
STEP 1: Try className override
STEP 2: If that fails, check if variant prop exists
STEP 3: If no variant, propose GENERIC enhancement to wizwebui
STEP 4: Get user approval for enhancement approach
STEP 5: Implement enhancement in wizwebui library
STEP 6: Use enhanced component in project
```

#### Example:

```
❌ WRONG:
"I'll create a custom CompactTable component"

✅ CORRECT:
"The current Table doesn't support compact density. I propose adding a
'density' prop to wizwebui Table with 'default' | 'compact' | 'spacious'
variants. This would benefit all users needing different table densities."
```

## Proposed Enhancements for wizwebui

### Enhancement 1: Card Variants
**Generic Value**: Support panels, product cards, minimal wrappers
**Implementation**: Add `variant` prop with configurable styles

### Enhancement 2: Table Density
**Generic Value**: Support data tables, pricing tables, comparison tables
**Implementation**: Add `density` and `borderStyle` props

### Enhancement 3: Tab Styles
**Generic Value**: Support navigation tabs, setting tabs, filter tabs
**Implementation**: Add `variant` prop for different tab styles

### Enhancement 4: Badge Sizes
**Generic Value**: Support status indicators, category tags, counts
**Implementation**: Add `size` and `variant` props

### Enhancement 5: Typography System
**Generic Value**: Consistent font sizes across design systems
**Implementation**: Add theme-able typography scale

## Next Steps

1. Get user approval on enhancement approach
2. Implement enhancements in wizwebui library
3. Update wizwebui documentation with new variants
4. Use enhanced components in Holdings page
5. Test enhancements with other design systems
6. Publish updated wizwebui version

## Success Criteria

- [ ] Holdings page matches mockup using wizwebui components
- [ ] No custom components created
- [ ] wizwebui enhancements are **generic** and **reusable**
- [ ] Other design systems can use same enhancements
- [ ] Component library remains framework-agnostic
