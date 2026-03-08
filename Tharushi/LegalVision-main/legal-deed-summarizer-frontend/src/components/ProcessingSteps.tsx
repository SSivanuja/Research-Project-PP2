// src/components/ProcessingSteps.tsx
import { useEffect, useMemo, useState } from "react";

export type ProcessingPhase = "summarize" | "timeline" | "details" | "infographic";
type Timings = Record<string, number>;

type SubKey =
  | "01_classify_deed_ms"
  | "05_normalize_jargon_ms"
  | "04_group_by_perspective_ms"
  | "02_results_df_to_rows_ms"
  | "03_build_clauses_list_ms";

const SUB_STEPS: Array<{ key: SubKey; label: string }> = [
  { key: "01_classify_deed_ms", label: "Deed classification" },
  { key: "05_normalize_jargon_ms", label: "Normalize legal jargon" },
  { key: "04_group_by_perspective_ms", label: "Group clauses by perspective" },
  { key: "02_results_df_to_rows_ms", label: "Format results (rows)" },
  { key: "03_build_clauses_list_ms", label: "Build clauses list" },
];

function msToNice(ms?: number) {
  if (typeof ms !== "number") return null;
  return `${Math.round(ms)} ms`;
}

export default function ProcessingSteps({
  phase,
  summarizeTimings,
  hasSummaries,
  hasTimeline,
  hasDetails,
  hasInfographic,
}: {
  phase: ProcessingPhase;
  summarizeTimings: Timings | null;
  hasSummaries: boolean;
  hasTimeline: boolean;
  hasDetails: boolean;
  hasInfographic: boolean;
}) {
  const [startTs] = useState(() => Date.now());
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 200);
    return () => clearInterval(t);
  }, []);

  const liveSeconds = ((now - startTs) / 1000).toFixed(2);

  const [activeSub, setActiveSub] = useState<number>(0);

  useEffect(() => {
    if (phase === "summarize") setActiveSub(0);
  }, [phase]);

  useEffect(() => {
    if (phase !== "summarize") return;

    if (hasSummaries) {
      setActiveSub(SUB_STEPS.length);
      return;
    }

    const t = setInterval(() => {
      setActiveSub((cur) => {
        if (cur >= SUB_STEPS.length - 1) return cur;
        return cur + 1;
      });
    }, 1200);

    return () => clearInterval(t);
  }, [phase, hasSummaries]);

  const timingRows = useMemo(() => {
    if (!summarizeTimings) return null;
    return SUB_STEPS.map((s) => ({ ...s, ms: summarizeTimings[s.key] }));
  }, [summarizeTimings]);

  const stepState = (key: ProcessingPhase): "idle" | "active" | "done" => {
    const doneMap: Record<ProcessingPhase, boolean> = {
      summarize: hasSummaries,
      timeline: hasTimeline,
      details: hasDetails,
      infographic: hasInfographic,
    };

    if (doneMap[key]) return "done";
    if (phase === key) return "active";

    // If we are past this phase, it's done
    const order: ProcessingPhase[] = ["summarize", "timeline", "details", "infographic"];
    const curIdx = order.indexOf(phase);
    const keyIdx = order.indexOf(key);
    if (curIdx > keyIdx) return "done";

    return "idle";
  };

  return (
    <div className="rounded-2xl border bg-white p-6">
      <div className="text-sm font-semibold text-neutral-900">Processing Document…</div>
      <div className="mt-1 text-xs text-neutral-500">Live time: {liveSeconds} s</div>

      <div className="mt-5 space-y-4">
        <StepRow state={stepState("summarize")} title="Summarize into 4 perspectives" />

        <div className="ml-9 space-y-3">
          {SUB_STEPS.map((s, idx) => {
            const state: "idle" | "active" | "done" =
              hasSummaries
                ? "done"
                : idx < activeSub
                ? "done"
                : idx === activeSub
                ? "active"
                : "idle";

            return (
              <div
                key={s.key}
                className="flex items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-neutral-50 px-3 py-2"
              >
                <div className="flex items-center gap-3">
                  <StepIcon state={state} small />
                  <div className="text-xs text-neutral-800">{s.label}</div>
                </div>

                <div className="text-xs text-neutral-500">
                  {timingRows ? msToNice(timingRows[idx].ms) : null}
                </div>
              </div>
            );
          })}
        </div>

        <StepRow state={stepState("timeline")} title="Extract timeline events" />
        <StepRow state={stepState("details")} title="Extract deed details" />
        <StepRow state={stepState("infographic")} title="Build infographic" />

        <div className="pt-2 text-xs text-neutral-500">
          Tip: First run might be slower because models load into memory.
        </div>
      </div>
    </div>
  );
}

function StepRow({
  state,
  title,
}: {
  state: "idle" | "active" | "done";
  title: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <StepIcon state={state} />
      <div className="text-sm font-medium text-neutral-900">{title}</div>
    </div>
  );
}

function StepIcon({
  state,
  small,
}: {
  state: "idle" | "active" | "done";
  small?: boolean;
}) {
  const size = small ? "h-6 w-6" : "h-7 w-7";

  if (state === "done") {
    return (
      <div className={`flex ${size} items-center justify-center rounded-full bg-emerald-600 text-white`}>
        ✓
      </div>
    );
  }
  if (state === "active") {
    return (
      <div className={`flex ${size} items-center justify-center rounded-full bg-neutral-900 text-white`}>
        …
      </div>
    );
  }
  return <div className={`${size} rounded-full border border-neutral-300 bg-white`} />;
}