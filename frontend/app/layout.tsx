import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { StoreProvider } from "@/store/StoreProvider";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GMailAgent",
  description:
    "Gmail, AI-suggested reply drafts, review and approve, then send — with you in control.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} min-h-screen`}>
        <StoreProvider>{children}</StoreProvider>
      </body>
    </html>
  );
}
