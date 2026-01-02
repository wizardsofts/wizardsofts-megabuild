import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Padma Foods | Coming Soon",
  description:
    "Quality Assured • Authentic Taste. Fresh, authentic Bangladeshi food products coming soon to your door. Visit us today!",
  keywords: [
    "Padma Foods",
    "Bangladeshi food",
    "food delivery Bangladesh",
    "authentic cuisine",
    "quality food",
    "Bengali food",
    "halal food",
  ],
  authors: [{ name: "Padma Foods" }],
  openGraph: {
    title: "Padma Foods | Quality Assured • Authentic Taste",
    description:
      "Fresh, authentic Bangladeshi food products delivered to your door. Coming Soon!",
    url: "https://mypadmafoods.com",
    siteName: "Padma Foods",
    type: "website",
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "Padma Foods | Quality Assured • Authentic Taste",
    description:
      "Fresh, authentic Bangladeshi food products delivered to your door.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
