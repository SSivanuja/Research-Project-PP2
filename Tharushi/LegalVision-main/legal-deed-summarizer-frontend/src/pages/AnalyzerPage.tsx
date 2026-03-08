// src/pages/AnalyzerPage.tsx
import { useMemo, useState } from "react";
import DropzoneCard from "../components/DropzoneCard";
import ProcessingSteps, { type ProcessingPhase } from "../components/ProcessingSteps";
import Tabs, { type TabKey } from "../components/Tabs";
import SummariesPanel from "../components/SummariesPanel";
import TimelineTable from "../components/TimelineTable";
import AnalyticsPanel from "../components/AnalyticsPanel";
import CommonInfographicPanel from "../components/CommonInfographicPanel";
import { useAnalyzeFile } from "../hooks/useAnalyzeFile";
import { useDeedInfographic } from "../hooks/useDeedInfographic";
import type {
  SummarizeResponse,
  TimelineResponse,
  DeedDetailsResponse,
  CommonInfographicResponse,
} from "../lib/types";

type UiState = "idle" | "processing" | "done" | "error";

export default function AnalyzerPage() {
  const { summarize, timeline } = useAnalyzeFile();
  const { extractDetails, generateInfographic } = useDeedInfographic();

  const [ui, setUi] = useState<UiState>("idle");
  const [phase, setPhase] = useState<ProcessingPhase>("summarize");

  const [traceability, setTraceability] = useState(true);

  const [pickedFile, setPickedFile] = useState<File | null>(null);
  const [sumData, setSumData] = useState<SummarizeResponse | null>(null);
  const [tlData, setTlData] = useState<TimelineResponse | null>(null);

  const [detailsData, setDetailsData] = useState<DeedDetailsResponse | null>(null);
  const [infoData, setInfoData] = useState<CommonInfographicResponse | null>(null);

  const [tab, setTab] = useState<TabKey>("summaries");
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const canPick = ui !== "processing";

  const timingsText = useMemo(() => {
    const ms = sumData?.meta?.timings_ms;
    if (!ms) return null;
    const top = Object.entries(ms)
      .sort((a, b) => (b[1] ?? 0) - (a[1] ?? 0))
      .slice(0, 6);
    return top.map(([k, v]) => `${k}: ${Math.round(v)} ms`).join(" • ");
  }, [sumData]);

  async function start(file: File) {
    setPickedFile(file);

    setUi("processing");
    setPhase("summarize");

    setErrMsg(null);
    setSumData(null);
    setTlData(null);
    setDetailsData(null);
    setInfoData(null);
    setTab("summaries");

    try {
      // 1) Summaries
      const s = await summarize.mutateAsync({ file, traceability });
      setSumData(s);

      // 2) Timeline
      // 2) Timeline
      setPhase("timeline");
      const t = await timeline.mutateAsync({ file });
      setTlData(t);

      // 3) Gemini: deed details
      setPhase("details");
      const d = await extractDetails.mutateAsync({ file });
      setDetailsData(d);

      // 4) Build common infographic from extracted details
      setPhase("infographic");
      const inf = await generateInfographic.mutateAsync({ deed_details: d.deed_details });
      setInfoData(inf);

      setUi("done");
      setTab("summaries");
    } catch (e: any) {
      setUi("error");
      setErrMsg(e?.response?.data?.error || e?.message || "Something went wrong");
    }
  }

  return (
    <div className="space-y-5">
      {/* top controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-neutral-700">
          {pickedFile ? (
            <>
              File: <span className="font-medium">{pickedFile.name}</span>
            </>
          ) : (
            "Upload a deed document to analyze."
          )}
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={traceability}
            onChange={(e) => setTraceability(e.target.checked)}
          />
          Traceability (group clauses per perspective)
        </label>
      </div>

      {/* main state */}
      {ui === "idle" ? (
        <DropzoneCard
          disabled={!canPick}
          onPick={(f) => {
            start(f);
          }}
        />
      ) : null}

      {ui === "processing" ? (
        <ProcessingSteps
          phase={phase}
          summarizeTimings={sumData?.meta?.timings_ms || null}
          hasSummaries={!!sumData}
          hasTimeline={!!tlData}
          hasDetails={!!detailsData}
          hasInfographic={!!infoData}
        />
      ) : null}

      {ui === "error" ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
          <div className="text-sm font-semibold text-red-800">Error</div>
          <div className="mt-1 text-sm text-red-700">{errMsg}</div>
          <button
            className="mt-3 rounded-xl bg-neutral-900 px-4 py-2 text-sm text-white"
            onClick={() => {
              setUi("idle");
              setPickedFile(null);
              setErrMsg(null);
              setSumData(null);
              setTlData(null);
              setDetailsData(null);
              setInfoData(null);
              setPhase("summarize");
              setTab("summaries");
            }}
          >
            Try again
          </button>
        </div>
      ) : null}

      {ui === "done" && sumData ? (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-xs text-neutral-500">
              document_id:{" "}
              <span className="font-mono text-neutral-700">
                {sumData.document_id}
              </span>
            </div>
            {timingsText ? (
              <div className="text-xs text-neutral-500">{timingsText}</div>
            ) : null}
          </div>

          <Tabs tab={tab} setTab={setTab}>
            {tab === "summaries" ? <SummariesPanel data={sumData} /> : null}

            {tab === "timeline" ? (
              <div className="space-y-3">
                {tlData?.meta?.counts ? (
                  <div className="flex gap-3 text-xs text-neutral-500">
                    <span>Raw events: <strong>{tlData.meta.counts.raw_events ?? 0}</strong></span>
                    <span>•</span>
                    <span>After dedup: <strong>{tlData.meta.counts.deduped_rows ?? 0}</strong></span>
                    <span>•</span>
                    <span>Final: <strong>{tlData.meta.counts.final_rows ?? 0}</strong></span>
                  </div>
                ) : null}
                <TimelineTable
                  events={
                    tlData?.timeline_events_final ||
                    tlData?.export_json ||
                    []
                  }
                />
              </div>
            ) : null}

            {tab === "analytics" ? (
              <AnalyticsPanel clauses={sumData.clauses || []} />
            ) : null}

            {tab === "infographic" ? (
              infoData?.infographic ? (
                <CommonInfographicPanel infographic={infoData.infographic} />
              ) : (
                <div className="text-sm text-neutral-500">
                  No infographic generated.
                </div>
              )
            ) : null}
          </Tabs>

          <div className="flex gap-2">
            <button
              className="rounded-xl bg-neutral-900 px-4 py-2 text-sm text-white"
              onClick={() => {
                setUi("idle");
                setPickedFile(null);
                setErrMsg(null);
                setSumData(null);
                setTlData(null);
                setDetailsData(null);
                setInfoData(null);
                setPhase("summarize");
                setTab("summaries");
              }}
            >
              Analyze another file
            </button>

            <button
              className="rounded-xl border px-4 py-2 text-sm"
              onClick={() => {
                const blob = new Blob(
                  [JSON.stringify({ sumData, tlData, detailsData, infoData }, null, 2)],
                  { type: "application/json" }
                );
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `analysis_${sumData.document_id}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            >
              Export JSON
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}