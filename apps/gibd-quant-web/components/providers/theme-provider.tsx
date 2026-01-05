'use client';

// TODO: Replace with @wizwebui/core ThemeProvider once library is fixed (missing export in dist)
// For now, just pass through children without theme provider
// import { ThemeProvider as WizWebUIThemeProvider } from '@wizwebui/core';
// import { guardianTheme } from '@/lib/theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // TODO: Wrap with WizWebUIThemeProvider once wizwebui exports are fixed
  return children;
}
