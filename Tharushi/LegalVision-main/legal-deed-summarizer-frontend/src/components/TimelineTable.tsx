// src/components/TimelineTable.tsx
import { useMemo, useState } from "react";

type AnyEvent = Record<string, any>;

function pickStr(obj: AnyEvent, keys: string[]) {
  for (const k of keys) {
    const v = obj?.[k];
    if (typeof v === "string" && v.trim()) return v.trim();
  }
  return "";
}

function pickNum(obj: AnyEvent, keys: string[]) {
  for (const k of keys) {
    const v = obj?.[k];
    if (typeof v === "number") return v;
    if (typeof v === "string" && v.trim() && !Number.isNaN(Number(v))) return Number(v);
  }
  return undefined;
}

function normalizeDate(e: AnyEvent) {
  return (
    pickStr(e, ["date", "date_iso", "event_date", "deadline_date", "normalized_date"]) ||
    "Unknown date"
  );
}

function normalizeTitle(e: AnyEvent) {
  return (
    pickStr(e, ["title", "event_title", "event", "name", "label"]) ||
    pickStr(e, ["event_type"]) ||
    "—"
  );
}

function normalizeDesc(e: AnyEvent) {
  return (
    pickStr(e, ["description", "event_description", "details", "text", "note", "snippet"]) ||
    ""
  );
}

function normalizeTags(e: AnyEvent): string[] {
  // Prefer explicit tags/labels arrays
  if (Array.isArray(e?.tags)) {
    const t = e.tags.filter((x: any) => typeof x === "string" && x.trim());
    if (t.length) return t.slice(0, 4);
  }
  if (Array.isArray(e?.labels)) {
    const t = e.labels.filter((x: any) => typeof x === "string" && x.trim());
    if (t.length) return t.slice(0, 4);
  }

  // Build tags from backend fields
  const tags: string[] = [];
  const method = pickStr(e, ["match_method", "method"]);
  const eventType = pickStr(e, ["event_type"]);
  if (method) tags.push(method);
  if (eventType && eventType !== normalizeTitle(e)) tags.push(eventType);
  return tags.slice(0, 4);
}

function normalizeMeta(e: AnyEvent) {
  const lineId = pickStr(e, ["line_id", "lineId", "source_line_id", "clause_id", "id"]);
  const lineNo = pickNum(e, ["line_no", "lineNo", "line_number", "line", "source_line"]);
  return { lineId, lineNo };
}

export default function TimelineTable({ events }: { events: AnyEvent[] }) {
  const grouped = useMemo(() => {
    const map = new Map<string, AnyEvent[]>();
    for (const ev of events || []) {
      const d = normalizeDate(ev);
      if (!map.has(d)) map.set(d, []);
      map.get(d)!.push(ev);
    }

    // sort dates (YYYY-MM-DD) first; unknown last
    const dates = Array.from(map.keys()).sort((a, b) => {
      if (a === "Unknown date") return 1;
      if (b === "Unknown date") return -1;
      return a.localeCompare(b);
    });

    return dates.map((d) => ({ date: d, items: map.get(d)! }));
  }, [events]);

  if (!events || events.length === 0) {
    return (
      <div className="rounded-2xl border bg-white p-5 text-sm text-neutral-600">
        No timeline events found for this document.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="text-lg font-semibold">Timeline Visualization</div>

      <div className="relative">
        {/* vertical line */}
        <div className="absolute left-2 top-0 h-full w-[3px] rounded-full bg-blue-500/30" />

        <div className="space-y-8">
          {grouped.map(({ date, items }) => (
            <div key={date} className="relative pl-10">
              {/* date dot */}
              <div className="absolute left-[6px] top-2 h-3 w-3 rounded-full bg-blue-600" />

              <div className="text-base font-semibold text-neutral-900">{date}</div>

              <div className="mt-3 space-y-3">
                {items.map((e, idx) => (
                  <TimelineCard key={`${date}-${idx}`} event={e} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TimelineCard({ event }: { event: AnyEvent }) {
  const title = normalizeTitle(event);
  const desc = normalizeDesc(event);
  const tags = normalizeTags(event);
  const { lineId, lineNo } = normalizeMeta(event);

  const [open, setOpen] = useState(false);

  const short = desc.length > 180 ? desc.slice(0, 180).trim() + "…" : desc;

  return (
    <div className="rounded-2xl border bg-white p-4">
      {/* tags */}
      {tags.length ? (
        <div className="flex flex-wrap gap-2">
          {tags.map((t) => (
            <span
              key={t}
              className="rounded-lg bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700"
            >
              {t}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-2 text-sm font-semibold text-neutral-900">{title}</div>

      {desc ? (
        <div className="mt-2 text-sm text-neutral-700">
          {open ? desc : short}
        </div>
      ) : (
        <div className="mt-2 text-sm text-neutral-500">No description available.</div>
      )}

      {desc.length > 180 ? (
        <button
          className="mt-2 text-sm font-medium text-blue-700 hover:underline"
          onClick={() => setOpen((v) => !v)}
          type="button"
        >
          {open ? "Show less" : "Show more"}
        </button>
      ) : null}

      {(lineId || typeof lineNo === "number") ? (
        <div className="mt-3 text-xs text-neutral-500">
          {lineId ? (
            <>
              <span className="font-medium">Line ID:</span> {lineId}
            </>
          ) : null}
          {lineId && typeof lineNo === "number" ? <span className="mx-2">•</span> : null}
          {typeof lineNo === "number" ? (
            <>
              <span className="font-medium">Line #:</span> {lineNo}
            </>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}