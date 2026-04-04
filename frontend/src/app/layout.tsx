import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "MMM Platform",
  description: "Marketing Mix Modeling — compare Robyn, Meridian & PyMC",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <header className="border-b border-gray-200 bg-white">
            <div className="mx-auto max-w-7xl px-6 py-4 flex items-center gap-3">
              <span className="text-lg font-bold text-brand">MMM Platform</span>
              <span className="text-gray-300">|</span>
              <span className="text-sm text-gray-500">Robyn · Meridian · PyMC-Marketing</span>
            </div>
          </header>
          <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
