import pandas as pd

from src.config import (
    CONFIDENCE_THRESHOLD,
    CONFIDENCE_MARGIN_THRESHOLD,
    ENABLE_CONFIDENCE_FILTER,
)
from src.pipeline.classifier import classify_deed
from src.pipeline.jargon import normalize_legal_jargon
from src.pipeline.summarizer import (
    build_perspective_summaries,
    print_perspective_summaries,
    build_source_for_perspective,
)
from src.utils.timers import timed_section


def _extract_prob_columns(row: dict):
    return {k: float(v) for k, v in row.items() if str(k).startswith("prob_")}


def _get_top2_from_probs(prob_map: dict):
    if not prob_map:
        return (None, 0.0), (None, 0.0)

    ranked = sorted(prob_map.items(), key=lambda x: x[1], reverse=True)
    top1 = ranked[0] if len(ranked) >= 1 else (None, 0.0)
    top2 = ranked[1] if len(ranked) >= 2 else (None, 0.0)
    return top1, top2


def _is_uncertain_clause(row: dict) -> tuple[bool, str, float, float]:
    prob_map = _extract_prob_columns(row)
    top1, top2 = _get_top2_from_probs(prob_map)

    top1_prob = float(top1[1]) if top1[0] is not None else 0.0
    top2_prob = float(top2[1]) if top2[0] is not None else 0.0
    margin = top1_prob - top2_prob

    if not ENABLE_CONFIDENCE_FILTER:
        return False, "", top1_prob, margin

    if top1_prob < CONFIDENCE_THRESHOLD:
        return True, f"low_confidence<{CONFIDENCE_THRESHOLD}", top1_prob, margin

    if margin < CONFIDENCE_MARGIN_THRESHOLD:
        return True, f"low_margin<{CONFIDENCE_MARGIN_THRESHOLD}", top1_prob, margin

    return False, "", top1_prob, margin


def run_full_pipeline(document_id: str, raw_text: str, traceability: bool, resources: dict) -> dict:
    timings = {}

    clf_tok = resources["classifier"]["tokenizer"]
    clf_mod = resources["classifier"]["model"]

    sum_tok = resources["summarizer"]["tokenizer"]
    sum_mod = resources["summarizer"]["model"]
    device = resources["device"]
    max_source_len = resources["summarizer"]["max_source_len"]

    glossary = resources["glossary"]
    perspectives = resources["perspectives"]

    # ---------- Clause classification ----------
    with timed_section(timings, "01_classify_deed_ms"):
        results_df = classify_deed(raw_text, clf_tok, clf_mod, min_clause_length=30)

    # ---------- results rows ----------
    with timed_section(timings, "02_results_df_to_rows_ms"):
        results_rows = results_df.to_dict(orient="records")

    # ---------- clause list + uncertainty tagging ----------
    with timed_section(timings, "03_build_clauses_list_ms"):
        clauses = []
        for r in results_rows:
            clause_no = int(r.get("clause_no", 0))
            clause_id = f"C{clause_no:03d}"

            is_uncertain, uncertain_reason, confidence, margin = _is_uncertain_clause(r)

            item = {
                "clause_id": clause_id,
                "clause_no": clause_no,
                "clause_text": r.get("clause_text", ""),
                "predicted_perspective": r.get("predicted_perspective", ""),
                "top2_labels": r.get("top2_labels", ""),
                "confidence": confidence,
                "confidence_margin": margin,
                "is_uncertain": is_uncertain,
                "uncertain_reason": uncertain_reason,
            }
            clauses.append(item)

    # ---------- split certain vs uncertain ----------
    with timed_section(timings, "04_split_certain_uncertain_ms"):
        certain_clause_nos = {c["clause_no"] for c in clauses if not c["is_uncertain"]}
        uncertain_clauses = [c for c in clauses if c["is_uncertain"]]

        filtered_results_df = results_df[results_df["clause_no"].isin(certain_clause_nos)].copy()

    # ---------- Group by perspective using only certain clauses ----------
    with timed_section(timings, "05_group_by_perspective_ms"):
        grouped_by_perspective = {}
        for p in perspectives:
            src = build_source_for_perspective(filtered_results_df, p)

            grouped_clauses = [
                c for c in clauses
                if (not c["is_uncertain"]) and str(c["predicted_perspective"]) == str(p)
            ]

            grouped_by_perspective[p] = {
                "source_text_joined": src,
                "clauses": grouped_clauses if traceability else [],
            }

    # ---------- Jargon normalization ----------
    with timed_section(timings, "06_normalize_jargon_ms"):
        normalized_grouped_text = {}
        for p in perspectives:
            src = grouped_by_perspective[p]["source_text_joined"]
            normalized_grouped_text[p] = normalize_legal_jargon(src, glossary) if src else ""

    # ---------- Summarization ----------
    with timed_section(timings, "07_generate_summaries_ms"):
        summaries = build_perspective_summaries(
            sum_tok,
            sum_mod,
            device,
            max_source_len,
            normalized_grouped_text,
        )

    # ---------- Printable output ----------
    with timed_section(timings, "08_printable_summary_ms"):
        printable_summary = print_perspective_summaries(summaries)

    meta = {
        "timings_ms": timings,
        "models": {
            "classifier_dir": resources["classifier"]["model_dir"],
            "summarizer_loaded_from": resources["summarizer"]["loaded_from"],
            "summarizer_model_name": resources["summarizer"]["model_name"],
            "summarizer_max_source_len": resources["summarizer"]["max_source_len"],
        },
        "counts": {
            "num_clauses": len(clauses),
            "num_results_rows": len(results_rows),
            "certain_clauses": len([c for c in clauses if not c["is_uncertain"]]),
            "uncertain_clauses": len(uncertain_clauses),
        },
        "confidence_filter": {
            "enabled": ENABLE_CONFIDENCE_FILTER,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "margin_threshold": CONFIDENCE_MARGIN_THRESHOLD,
        }
    }

    return {
        "document_id": document_id,
        "clauses": clauses,
        "uncertain_clauses": uncertain_clauses,
        "results_df_equivalent": results_rows,
        "grouped_by_perspective": grouped_by_perspective,
        "normalized_grouped_text": normalized_grouped_text,
        "summaries": summaries,
        "printable_summary": printable_summary,
        "meta": meta,
    }


# ============================================================
# Timeline Extraction Orchestrator
# ============================================================
from src.pipeline.timeline_extractor import (
    build_lines_df as tl_build_lines_df,
    build_timeline_events_raw as tl_build_timeline_events_raw,
    dedupe_timeline as tl_dedupe_timeline,
    add_relative_deadlines as tl_add_relative_deadlines,
)


def extract_timeline_pipeline(
    document_id: str,
    text: str,
    include_relative_deadlines: bool = True,
) -> dict:
    timings = {}

    def _clean_for_json(value):
        if isinstance(value, dict):
            return {k: _clean_for_json(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_clean_for_json(v) for v in value]
        # Guard: only call isna on scalar types - calling it on str can raise in some pandas versions
        if isinstance(value, float):
            import math
            if math.isnan(value):
                return None
        else:
            try:
                if pd.isna(value):
                    return None
            except (TypeError, ValueError):
                pass
        return value

    with timed_section(timings, "A_build_lines_df_ms"):
        lines_df = tl_build_lines_df(text)

    with timed_section(timings, "D_build_timeline_events_raw_ms"):
        timeline_events_raw, raw_df = tl_build_timeline_events_raw(lines_df, text)

    with timed_section(timings, "G_sort_timeline_df_ms"):
        if raw_df is None or raw_df.empty:
            timeline_df = pd.DataFrame([])
        else:
            timeline_df = raw_df.sort_values("date_iso").reset_index(drop=True)

    with timed_section(timings, "E_dedupe_timeline_ms"):
        timeline_df_deduped = tl_dedupe_timeline(timeline_df) if not timeline_df.empty else timeline_df

    with timed_section(timings, "F_relative_deadlines_ms"):
        timeline_events_final = timeline_df_deduped.to_dict(orient="records") if not timeline_df_deduped.empty else []
        if include_relative_deadlines:
            timeline_events_final = tl_add_relative_deadlines(text, timeline_events_final)
        # ✅ Clean NaN from newly appended relative deadline events too
        timeline_events_final = _clean_for_json(timeline_events_final)

    with timed_section(timings, "G_final_sort_ms"):
        final_df = pd.DataFrame(timeline_events_final) if timeline_events_final else pd.DataFrame([])
        if not final_df.empty and "date_iso" in final_df.columns:
            final_df = final_df.sort_values("date_iso").reset_index(drop=True)

    with timed_section(timings, "G_export_json_ms"):
        export_json = final_df.to_dict(orient="records") if not final_df.empty else []

    # ✅ clean NaN -> None before jsonify
    lines_df_records = _clean_for_json(lines_df.to_dict(orient="records"))
    timeline_events_raw_clean = _clean_for_json(timeline_events_raw)
    timeline_df_records = _clean_for_json(timeline_df.to_dict(orient="records") if not timeline_df.empty else [])
    timeline_df_deduped_records = _clean_for_json(
        timeline_df_deduped.to_dict(orient="records") if not timeline_df_deduped.empty else []
    )
    timeline_events_final_records = _clean_for_json(
        final_df.to_dict(orient="records") if not final_df.empty else []
    )
    export_json_clean = _clean_for_json(export_json)

    return {
        "document_id": document_id,
        "lines_df": lines_df_records,
        "timeline_events_raw": timeline_events_raw_clean,
        "timeline_df": timeline_df_records,
        "timeline_df_deduped": timeline_df_deduped_records,
        "timeline_events_final": timeline_events_final_records,
        "export_json": export_json_clean,
        "meta": {
            "timings": timings,
            "counts": {
                "lines": int(len(lines_df)),
                "raw_events": int(len(timeline_events_raw)),
                "timeline_rows": int(len(timeline_df)) if hasattr(timeline_df, "__len__") else 0,
                "deduped_rows": int(len(timeline_df_deduped)) if hasattr(timeline_df_deduped, "__len__") else 0,
                "final_rows": int(len(final_df)) if hasattr(final_df, "__len__") else 0,
            },
        },
    }