// src/components/Layout.tsx
import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      {/* Top Header */}
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
          {/* Left: icon + title */}
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-neutral-200 bg-white">
  {/* Document icon: black lines, white space */}
  <svg
    viewBox="0 0 24 24"
    className="h-5 w-5 text-neutral-900"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <path
      d="M7 3h7l3 3v15a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinejoin="round"
    />
    <path
      d="M14 3v4a1 1 0 0 0 1 1h4"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinejoin="round"
    />
    <path
      d="M8 12h8M8 16h8"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
</div>
            <div>
              <div className="text-lg font-semibold leading-6">
                Legal Document Analyzer &amp; Summariser
              </div>
              <div className="text-sm text-neutral-500">
                Upload a deed → multi-perspective summaries, infographics
              </div>
            </div>
          </div>

          {/* Right: small meta */}
          <div className="hidden items-center gap-2 text-sm text-neutral-500 md:flex">
            <span>Fast</span>
            <span>•</span>
            <span>Clean</span>
            <span>•</span>
            <span>Traceable</span>
          </div>
        </div>
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-6xl px-6 py-6">{children}</main>
    </div>
  );
}