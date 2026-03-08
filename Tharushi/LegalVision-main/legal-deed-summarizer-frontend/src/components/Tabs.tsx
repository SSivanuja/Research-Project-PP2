import type { ReactNode } from "react";

export type TabKey = "summaries" | "timeline" | "analytics" | "infographic";

export default function Tabs({
  tab,
  setTab,
  children,
}: {
  tab: TabKey;
  setTab: (t: TabKey) => void;
  children: ReactNode;
}) {
  const items: Array<{ key: TabKey; label: string }> = [
    { key: "summaries", label: "Summaries" },
    { key: "timeline", label: "Timeline" },
    { key: "analytics", label: "Analytics" },
    { key: "infographic", label: "Infographic" },
  ];

  return (
    <div className="rounded-2xl bg-white shadow-soft">
      <div className="flex flex-wrap gap-2 border-b p-3">
        {items.map((it) => (
          <button
            key={it.key}
            onClick={() => setTab(it.key)}
            className={[
              "rounded-xl px-3 py-2 text-sm transition",
              tab === it.key
                ? "bg-neutral-900 text-white"
                : "bg-neutral-100 text-neutral-700 hover:bg-neutral-200",
            ].join(" ")}
          >
            {it.label}
          </button>
        ))}
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}