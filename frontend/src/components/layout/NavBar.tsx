"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavBar() {
  const pathname = usePathname();
  const isLanding = pathname === "/";

  return (
    <header className={`border-b border-gray-200 ${isLanding ? "bg-white/80 backdrop-blur-sm sticky top-0 z-50" : "bg-white"}`}>
      <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <span className="text-lg font-bold text-brand">MMM Platform</span>
          {!isLanding && (
            <>
              <span className="text-gray-300">|</span>
              <span className="text-sm text-gray-500">Robyn · Meridian · PyMC</span>
            </>
          )}
        </Link>

        <nav className="flex items-center gap-4">
          {isLanding ? (
            <>
              <a href="#how-it-works" className="text-sm text-gray-600 hover:text-gray-900 transition">
                How it works
              </a>
              <Link
                href="/dashboard"
                className="rounded-lg bg-brand px-5 py-2 text-sm font-semibold text-white hover:bg-brand-dark transition"
              >
                Get started
              </Link>
            </>
          ) : (
            <Link
              href="/dashboard"
              className="text-sm text-gray-600 hover:text-gray-900 transition"
            >
              Dashboard
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
