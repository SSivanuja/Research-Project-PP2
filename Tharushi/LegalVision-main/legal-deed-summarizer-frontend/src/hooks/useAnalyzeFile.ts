import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { SummarizeResponse, TimelineResponse } from "../lib/types";

async function postSummarizeFile(file: File, traceability: boolean) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("traceability", traceability ? "true" : "false");

  const res = await api.post<SummarizeResponse>("/api/summarize-file", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

async function postTimelineFile(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("include_relative_deadlines", "true");

  const res = await api.post("/api/extract-timeline-file", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  const data =
    typeof res.data === "string"
      ? JSON.parse(res.data)
      : res.data;

  return data as TimelineResponse;
}

export function useAnalyzeFile() {
  const summarize = useMutation({
    mutationFn: async (args: { file: File; traceability: boolean }) =>
      postSummarizeFile(args.file, args.traceability),
  });

  const timeline = useMutation({
    mutationFn: async (args: { file: File }) => postTimelineFile(args.file),
  });

  return { summarize, timeline };
}