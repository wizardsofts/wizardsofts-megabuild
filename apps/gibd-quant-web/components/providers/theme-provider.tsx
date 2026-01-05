'use client';

import { ThemeProvider as WizWebUIThemeProvider } from '@wizwebui/core';
import { guardianTheme } from '@/lib/theme';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <WizWebUIThemeProvider theme={guardianTheme}>
      {children}
    </WizWebUIThemeProvider>
  );
}
