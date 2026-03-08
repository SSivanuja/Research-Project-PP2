import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { DeedDetailsResponse, CommonInfographicResponse } from "../lib/types";

async function postExtractDeedDetailsFile(file: File) {
  const fd = new FormData();
  fd.append("file", file);

  const res = await api.post<DeedDetailsResponse>(
    "/api/extract-deed-details-file",
    fd,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
  return res.data;
}

async function postGenerateCommonInfographic(deed_details: any) {
  const res = await api.post<CommonInfographicResponse>(
    "/api/generate-common-infographic",
    { deed_details }
  );
  return res.data;
}

export function useDeedInfographic() {
  const extractDetails = useMutation({
    mutationFn: async (args: { file: File }) => postExtractDeedDetailsFile(args.file),
  });

  const generateInfographic = useMutation({
    mutationFn: async (args: { deed_details: any }) =>
      postGenerateCommonInfographic(args.deed_details),
  });

  return { extractDetails, generateInfographic };
}