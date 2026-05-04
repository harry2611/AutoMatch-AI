import type { Metadata } from "next";

import { Navbar } from "@/components/navbar";

import "./globals.css";

export const metadata: Metadata = {
  title: "AutoMatch AI — Bayesian Marketplace Optimizer",
  description:
    "AutoMatch AI turns noisy buyer browsing signals into ranked vehicle matches that convert. Powered by Bayesian posteriors, real-time re-ranking, dealer intelligence, and A/B experiment governance.",
  keywords: [
    "automotive marketplace",
    "Bayesian recommendation engine",
    "car matching AI",
    "dealer intelligence",
    "vehicle ranking",
    "A/B experimentation",
  ],
  openGraph: {
    title: "AutoMatch AI — Bayesian Marketplace Optimizer",
    description:
      "Real-time Bayesian ranking engine for automotive marketplaces. Buyer app, dealer IQ, and experiment governance in one platform.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col">
        <Navbar />
        <div className="flex-1">{children}</div>
      </body>
    </html>
  );
}
