import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { GoogleAnalytics } from "@/components/analytics/GoogleAnalytics";
import { AdMobScript } from "@/components/analytics/AdMob";
import { ClickTracker } from "@/components/analytics/ClickTracker";
import { AuthProvider } from "@/components/providers/auth-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";

/**
 * Root Layout - Wraps all pages in the application
 *
 * LEARNING MODULE 1 & 2:
 * ----------------------
 * In Next.js App Router, layout.tsx defines a wrapper that persists across
 * page navigations. Think of it as a template that surrounds your page content.
 *
 * Key concepts:
 * 1. `children` - This is the page content that will be rendered inside the layout
 * 2. `Metadata` - SEO information like title and description
 * 3. This layout applies to ALL routes in the app/ directory
 *
 * MODULE 2 UPDATE:
 * We've added Header and Footer components that will appear on every page.
 * The `flex flex-col min-h-screen` pattern ensures the footer stays at bottom.
 *
 * AUTHENTICATION:
 * AuthProvider wraps the app with NextAuth.js session context for
 * Keycloak OIDC authentication.
 *
 * File path: frontend/app/layout.tsx
 * See: frontend/LEARNING.md#module-1-layouts
 */

export const metadata: Metadata = {
  title: "Guardian Investment BD | DSE Trading Signals",
  description:
    "Quantitative trading signal analysis for Dhaka Stock Exchange (DSE)",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white antialiased">
        <ThemeProvider>
          <AuthProvider>
            {/* Analytics Scripts */}
            <GoogleAnalytics />
            <AdMobScript />
            <ClickTracker />

            {/* Header - fixed at top */}
            <Header />

            {/* Main content - with padding for fixed header/footer */}
            <main className="pt-12 pb-12 min-h-screen bg-white">{children}</main>

            {/* Footer - fixed at bottom */}
            <Footer />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
