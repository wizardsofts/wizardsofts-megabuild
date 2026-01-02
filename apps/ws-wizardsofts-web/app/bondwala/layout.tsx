import { Metadata } from "next";

export const metadata: Metadata = {
  title: "BondWala - Bangladesh Prize Bond Tracker App",
  description:
    "Track your Bangladesh Prize Bonds easily. Get instant win notifications with OCR scanning. Free, private, no login required.",
  keywords:
    "prize bonds, bond tracker, Bangladesh, notification, win detection, BondWala",
  openGraph: {
    title: "BondWala - Track Easy, Win Sure",
    description:
      "Bangladesh Prize Bond Tracker. Scan bonds, get win notifications.",
    url: "https://wizardsofts.com/bondwala",
    type: "website",
    images: [
      {
        url: "https://wizardsofts.com/bondwala-og-image.png",
        width: 1200,
        height: 630,
        alt: "BondWala App",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "BondWala - Track Easy, Win Sure",
    description:
      "Bangladesh Prize Bond Tracker app with OCR scanning and instant notifications",
  },
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return children;
}
