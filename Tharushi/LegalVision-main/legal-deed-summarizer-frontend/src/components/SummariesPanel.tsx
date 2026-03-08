// src/components/SummariesPanel.tsx
import { useMemo, useState } from "react";
import type { SummarizeResponse } from "../lib/types";

type ApiClause = {
  clause_id?: string;
  clause_no?: number;
  clause_text?: string;
  predicted_perspective?: string;
  confidence?: number;
  top2_labels?: string;
};

type PerspectiveKey =
  | "Conditions_Procedure"
  | "Financial_Asset"
  | "Ownership_Parties"
  | "Rights_Duties_Risks"
  | "Other"
  | string;

function prettyPerspective(p?: string) {
  if (!p) return "Other";
  const map: Record<string, string> = {
    Ownership_Parties: "Ownership & Parties Involved",
    Financial_Asset: "Financial & Asset Impact",
    Conditions_Procedure: "Conditions & Procedure",
    Rights_Duties_Risks: "Rights, Duties & Risks",
  };
  return map[p] || p.replaceAll("_", " ");
}

// 4 highlight colors (Turnitin-like)
function toneFor(p: PerspectiveKey) {
  switch (p) {
    case "Conditions_Procedure":
      return {
        name: "Conditions & Procedure",
        pill: "bg-blue-50 text-blue-800 border-blue-200",
        mark: "bg-blue-100",
        dot: "bg-blue-500",
        accent: "bg-blue-500",
      };
    case "Financial_Asset":
      return {
        name: "Financial & Asset",
        pill: "bg-emerald-50 text-emerald-800 border-emerald-200",
        mark: "bg-emerald-100",
        dot: "bg-emerald-500",
        accent: "bg-emerald-500",
      };
    case "Ownership_Parties":
      return {
        name: "Ownership & Parties",
        pill: "bg-purple-50 text-purple-800 border-purple-200",
        mark: "bg-purple-100",
        dot: "bg-purple-500",
        accent: "bg-purple-500",
      };
    case "Rights_Duties_Risks":
      return {
        name: "Rights, Duties & Risks",
        pill: "bg-rose-50 text-rose-800 border-rose-200",
        mark: "bg-rose-100",
        dot: "bg-rose-500",
        accent: "bg-rose-500",
      };
    default:
      return {
        name: "Other",
        pill: "bg-neutral-50 text-neutral-700 border-neutral-200",
        mark: "bg-neutral-100",
        dot: "bg-neutral-400",
        accent: "bg-neutral-400",
      };
  }
}

function Badge({
  children,
  variant = "neutral",
}: {
  children: React.ReactNode;
  variant?: "neutral" | "source" | "ai";
}) {
  const cls =
    variant === "source"
      ? "border border-neutral-200 bg-white text-neutral-800"
      : variant === "ai"
      ? "border border-neutral-900 bg-neutral-900 text-white"
      : "border border-neutral-200 bg-neutral-50 text-neutral-700";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs ${cls}`}
    >
      {children}
    </span>
  );
}

function SectionHeader({
  title,
  subtitle,
  right,
  tone = "neutral",
}: {
  title: string;
  subtitle: string;
  right?: React.ReactNode;
  tone?: "neutral" | "ai";
}) {
  const bg =
    tone === "ai"
      ? "bg-neutral-900 text-white border-neutral-900"
      : "bg-neutral-50 text-neutral-900 border-neutral-200";

  return (
    <div className={`rounded-2xl border p-4 ${bg}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{title}</div>
          <div
            className={`mt-1 text-xs ${
              tone === "ai" ? "text-neutral-200" : "text-neutral-500"
            }`}
          >
            {subtitle}
          </div>
        </div>
        {right ? <div className="shrink-0">{right}</div> : null}
      </div>
    </div>
  );
}

function Legend({
  active,
  setActive,
}: {
  active: PerspectiveKey | "ALL";
  setActive: (v: PerspectiveKey | "ALL") => void;
}) {
  const items: Array<{ key: PerspectiveKey; label: string }> = [
    { key: "Conditions_Procedure", label: "Conditions & Procedure" },
    { key: "Financial_Asset", label: "Financial & Asset" },
    { key: "Ownership_Parties", label: "Ownership & Parties" },
    { key: "Rights_Duties_Risks", label: "Rights, Duties & Risks" },
  ];

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => setActive("ALL")}
        className={[
          "rounded-full border px-3 py-1 text-xs font-medium",
          active === "ALL"
            ? "bg-neutral-900 text-white border-neutral-900"
            : "bg-white text-neutral-800 border-neutral-200 hover:bg-neutral-50",
        ].join(" ")}
      >
        Show all
      </button>

      {items.map((it) => {
        const t = toneFor(it.key);
        const on = active === it.key;
        return (
          <button
            key={it.key}
            type="button"
            onClick={() => setActive(it.key)}
            className={[
              "rounded-full border px-3 py-1 text-xs font-medium",
              on
                ? "bg-neutral-900 text-white border-neutral-900"
                : "bg-white border-neutral-200 hover:bg-neutral-50",
            ].join(" ")}
          >
            <span
              className={`mr-2 inline-block h-2 w-2 rounded-full ${t.dot}`}
            />
            {it.label}
          </button>
        );
      })}
    </div>
  );
}

function buildClauses(data: SummarizeResponse): ApiClause[] {
  const clauses: ApiClause[] = (data as any)?.clauses || [];
  const arr = [...clauses];
  arr.sort((a, b) => (a.clause_no ?? 999999) - (b.clause_no ?? 999999));
  return arr;
}

function normalizePerspectiveKey(p?: string): PerspectiveKey {
  const raw = (p || "").trim();
  if (!raw) return "Other";

  // handle both possible keys (predicted_perspective vs perspective, etc.)
  const map: Record<string, PerspectiveKey> = {
    Conditions_Procedure: "Conditions_Procedure",
    Financial_Asset: "Financial_Asset",
    Ownership_Parties: "Ownership_Parties",
    Rights_Duties_Risks: "Rights_Duties_Risks",

    // common alternate spellings
    Conditions_Procedure_: "Conditions_Procedure",
    Financial_Asset_Impact: "Financial_Asset",
    Ownership_Parties_Involved: "Ownership_Parties",
    Rights_Duties_Risk: "Rights_Duties_Risks",
  };

  return map[raw] || raw;
}

function SummaryCard({
  perspectiveKey,
  title,
  text,
}: {
  perspectiveKey: PerspectiveKey;
  title: string;
  text: string;
}) {
  const t = toneFor(perspectiveKey);
  return (
    <div className="relative overflow-hidden rounded-2xl border bg-white">
      {/* left accent */}
      <div className={`absolute left-0 top-0 h-full w-1.5 ${t.accent}`} />

      <div className="p-4 pl-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className={`inline-block h-2 w-2 rounded-full ${t.dot}`} />
            <div className="text-sm font-semibold text-neutral-900">{title}</div>
          </div>

          <span className="inline-flex items-center rounded-full bg-neutral-900 px-3 py-1 text-xs text-white">
            Summary
          </span>
        </div>

        <div className="mt-2 whitespace-pre-wrap text-sm leading-6 text-neutral-800">
          {text}
        </div>
      </div>
    </div>
  );
}

export default function SummariesPanel({ data }: { data: SummarizeResponse }) {
  const clauses = useMemo(() => buildClauses(data), [data]);

  const [showOriginal, setShowOriginal] = useState(false);
  const [active, setActive] = useState<PerspectiveKey | "ALL">("ALL");

  const summaries =
    (data as any)?.summaries || (data as any)?.multi_perspective_summaries;

  const filteredClauses = useMemo(() => {
    if (active === "ALL") return clauses;
    return clauses.filter((c) => {
      const p = normalizePerspectiveKey(c.predicted_perspective);
      return p === active;
    });
  }, [clauses, active]);

  return (
    <div className="space-y-4">
      {/* ✅ Original Section */}
      <SectionHeader
        title="Text extracted from document"
        subtitle="These highlighted parts are the extracted sentences used to generate each perspective summary."
        right={
          <button
            type="button"
            onClick={() => setShowOriginal((v) => !v)}
            className="rounded-xl border border-neutral-200 bg-white px-3 py-2 text-xs font-medium text-neutral-800 hover:bg-neutral-50"
          >
            {showOriginal ? "Hide original" : "View original"}
          </button>
        }
      />

      {showOriginal ? (
        <div className="rounded-2xl border bg-white p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="source">Source</Badge>
              <span className="text-xs text-neutral-500">
                Turnitin-style highlighting by perspective
              </span>
            </div>
            <Legend active={active} setActive={setActive} />
          </div>

          {/* ✅ Document-like flowing preview */}
          <div className="mt-4 max-h-[520px] overflow-auto rounded-xl border border-neutral-200 bg-neutral-50 p-4">
            {filteredClauses.length ? (
              <p className="text-sm leading-7 text-neutral-900">
                {filteredClauses.map((c, idx) => {
                  const p = normalizePerspectiveKey(c.predicted_perspective);
                  const t = toneFor(p);
                  const txt = (c.clause_text || "").trim();
                  if (!txt) return null;

                  const tip = `${prettyPerspective(p)}${
                    typeof c.confidence === "number"
                      ? ` • conf ${c.confidence.toFixed(3)}`
                      : ""
                  }${c.top2_labels ? ` • top2 ${c.top2_labels}` : ""}`;

                  return (
                    <span key={(c.clause_id || "cl") + "_" + idx} className="mr-2">
                      <mark
                        className={["rounded px-1.5 py-0.5", t.mark].join(" ")}
                        title={tip}
                      >
                        {txt}
                      </mark>
                    </span>
                  );
                })}
              </p>
            ) : (
              <div className="text-sm text-neutral-600">
                No clauses found for the selected perspective.
              </div>
            )}
          </div>

          <div className="mt-3 text-xs text-neutral-500">
            Tip: Hover a highlighted sentence to see its perspective (and
            confidence if available).
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border bg-white p-4 text-sm text-neutral-600">
          Tip: Click <span className="font-medium">“View original”</span> to see
          the document text with 4-color highlights.
        </div>
      )}

      {/* ✅ AI Summary Section */}
      <SectionHeader
        title="Multi-Perspective Summaries"
        subtitle="This section contains model-generated summaries"
        tone="ai"
        right={<Badge variant="ai">AI Summary</Badge>}
      />

      <div className="space-y-3">
        {summaries && typeof summaries === "object" ? (
          Object.entries(summaries).map(([k, v]) => {
            const pk = normalizePerspectiveKey(k);
            return (
              <SummaryCard
                key={k}
                perspectiveKey={pk}
                title={prettyPerspective(k)}
                text={String(v || "")}
              />
            );
          })
        ) : (
          <div className="rounded-2xl border bg-white p-4 text-sm text-neutral-600">
            No summaries found.
          </div>
        )}
      </div>
    </div>
  );
}