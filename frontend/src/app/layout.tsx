import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { NavBar } from "@/components/layout/NavBar";

export const metadata: Metadata = {
  title: "MMM Platform — Marketing Mix Modeling",
  description:
    "Run Robyn, Meridian & PyMC side-by-side to optimize your marketing spend. Get channel attribution, saturation curves, and budget recommendations.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <NavBar />
          <div id="app-content">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
