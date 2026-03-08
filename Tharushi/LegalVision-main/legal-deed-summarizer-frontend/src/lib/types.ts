export type Clause = {
  clause_id: string;
  clause_no: number;
  clause_text: string;
  predicted_perspective: string;
  top2_labels?: string;
  confidence?: number;
};

export type SummarizeResponse = {
  document_id: string;
  summaries: Record<string, string>;
  printable_summary?: string;
  clauses: Clause[];
  results_df_equivalent?: Array<Record<string, unknown>>;
  grouped_by_perspective?: Record<
    string,
    { source_text_joined: string; clauses: Clause[] }
  >;
  normalized_grouped_text?: Record<string, string>;
  meta?: {
    timings_ms?: Record<string, number>;
    counts?: { num_clauses?: number; num_results_rows?: number };
    models?: Record<string, unknown>;
  };
};

export type TimelineEvent = {
  date_iso?: string;
  date_text?: string;
  title?: string;
  description?: string;
  source_line?: string;
  confidence?: number;
  [k: string]: unknown;
};

export type TimelineResponse = {
  document_id: string;
  timeline_events_final: TimelineEvent[];
  export_json: TimelineEvent[];
  meta?: {
    timings?: Record<string, number>;
    counts?: Record<string, number>;
  };
};

export type DeedDetailsResponse = {
  document_id: string;
  deed_details: Record<string, any>;
};

export type CommonInfographicResponse = {
  infographic: Record<string, any>;
};



