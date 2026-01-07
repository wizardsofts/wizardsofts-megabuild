# Policy Updates Summary - No Custom Components

**Date**: 2026-01-04
**Context**: Holdings page design mismatch identified
**Action**: Updated policies to strictly enforce wizwebui component usage

---

## 🚫 NEW STRICT POLICY

**CRITICAL RULE**: Creating custom UI components is now **PROHIBITED**.

### What This Means

❌ **NEVER**:
- Create custom tables, cards, tabs, buttons, badges, etc.
- Build one-off components for specific designs
- Duplicate functionality that exists in wizwebui

✅ **ALWAYS**:
- Use wizwebui components for ALL UI elements
- Propose GENERIC enhancements if component doesn't match design
- Get user approval before implementing enhancements
- Make enhancements reusable for all wizwebui users

---

## 📋 Files Updated

### 1. CLAUDE.md (Root Instructions)
**File**: `/CLAUDE.md`
**Section Added**: "Component Library Policy - MANDATORY ⚠️"

**Key Points**:
- Strict component usage rules (never create custom)
- Step-by-step process when component doesn't match
- Enhancement approval process
- Examples of good vs bad enhancements

### 2. Frontend Developer Skill
**File**: `.claude/skills/frontend-developer.md`
**Section Updated**: "Component Library Integration"

**Key Points**:
- Mandatory wizwebui usage
- Enhancement proposal process
- Generic vs project-specific guidelines
- Build and test procedure for enhancements

### 3. Enhancement Plan
**New File**: `WIZWEBUI_ENHANCEMENT_PLAN.md`

**Contents**:
- Proposed enhancements (Card variants, Table density, Tab styles, etc.)
- Generic enhancement guidelines
- DO NOT / DO lists
- Implementation approach

### 4. Retrospective
**File**: `RETROSPECTIVE_HOLDINGS_PAGE.md`

**Lessons Learned**:
- Why design mismatch happened
- Process improvements needed
- Metrics on time wasted

### 5. Background Fix
**File**: `apps/gibd-quant-web/app/layout.tsx`
**Change**: `bg-gray-50` → `bg-white`

---

## 🔄 New Development Process

### When Component Doesn't Match Design

```
STEP 1: Try className override
  <Table className="text-sm border-gray-100" />

STEP 2: Check existing props/variants
  <Table density="compact" />

STEP 3: No variant? STOP and propose enhancement
  "Current Table doesn't support compact density.
   I propose adding 'density' prop with 3 variants.
   Benefits: data tables, pricing tables, etc.
   Should I proceed?"

STEP 4: Wait for user approval

STEP 5: Implement in wizwebui library
  File: wizwebui/packages/core/src/components/Table/Table.tsx

STEP 6: Build wizwebui
  cd wizwebui/packages/core && npm run build

STEP 7: Use enhanced component
  <Table density="compact" />
```

---

## 📊 Proposed wizwebui Enhancements

### Enhancement 1: Card Variants
```tsx
interface CardProps {
  variant?: 'default' | 'panel' | 'minimal'
}

// 'default': Current rounded card with shadow
// 'panel': Flat panel for dashboards
// 'minimal': No styling, just structure
```

**Generic Value**: Supports dashboard panels, product cards, landing page cards

### Enhancement 2: Table Density
```tsx
interface TableProps {
  density?: 'default' | 'compact' | 'spacious'
  borderStyle?: 'default' | 'minimal' | 'none'
}

// Density controls row padding
// Border style controls border colors/thickness
```

**Generic Value**: Supports data tables, pricing tables, comparison tables

### Enhancement 3: Tab Variants
```tsx
interface TabsProps {
  variant?: 'default' | 'underline' | 'pills' | 'minimal'
}

// 'underline': Clean underline only (mockup style)
// 'pills': Pill-shaped tabs
// etc.
```

**Generic Value**: Supports navigation tabs, settings tabs, filter tabs

### Enhancement 4: Badge Sizes
```tsx
interface BadgeProps {
  size?: 'xs' | 'sm' | 'md' | 'lg'
  variant?: 'default' | 'pill' | 'minimal'
}

// Size controls text/padding
// Variant controls shape/styling
```

**Generic Value**: Supports status indicators, category tags, counts

### Enhancement 5: CardHeader Variants
```tsx
interface CardHeaderProps {
  variant?: 'default' | 'compact' | 'minimal'
  uppercase?: boolean
}

// 'compact': Minimal padding (py-2 px-4)
// uppercase: Text transformation
```

**Generic Value**: Supports compact dashboards, spacious landing pages

---

## ✅ What's Been Completed

1. ✅ Background color fix (`bg-gray-50` → `bg-white`)
2. ✅ CLAUDE.md updated with strict policy
3. ✅ Frontend-developer skill updated
4. ✅ Enhancement plan documented
5. ✅ Retrospective created
6. ✅ Process improvements defined

---

## ⏳ Next Steps (Awaiting User Approval)

### Immediate Actions Needed

**User Decision Required**: Should we proceed with wizwebui enhancements?

**If YES**:
1. Implement Card variant prop
2. Implement Table density prop
3. Implement Tabs variant prop
4. Implement Badge size prop
5. Implement CardHeader variant prop
6. Build wizwebui library
7. Update Holdings page to use enhanced components
8. Test responsive design
9. Document enhancements

**If NO / Need Guidance**:
- User will provide alternative approach
- May need to adjust enhancement proposals
- May need different strategy entirely

---

## 📝 Key Takeaways

### For Future Development

1. **Never create custom components** - Always enhance wizwebui
2. **Make enhancements generic** - Not project-specific
3. **Get approval first** - Don't implement without user OK
4. **Document everything** - Policies, enhancements, decisions
5. **Test across design systems** - Ensure generic value

### Why This Matters

- **Consistency**: All projects use same component library
- **Maintainability**: One library to update, not scattered custom components
- **Quality**: Generic enhancements benefit all users
- **Efficiency**: Reusable components save future time

---

## 📚 Documentation References

- **Enhancement Plan**: `WIZWEBUI_ENHANCEMENT_PLAN.md`
- **Retrospective**: `RETROSPECTIVE_HOLDINGS_PAGE.md`
- **Design Fix Plan**: `DESIGN_MISMATCH_FIX_PLAN.md`
- **Root Policy**: `/CLAUDE.md` - Component Library Policy section
- **Skill Policy**: `.claude/skills/frontend-developer.md` - Component Library Integration section

---

## Summary

We've established a **strict no-custom-components policy** and defined a clear process for enhancing wizwebui when components don't match designs. All documentation has been updated to enforce this approach.

**Awaiting user approval** to proceed with implementing the proposed wizwebui enhancements.
