import re
import torch
from src.config import PERSPECTIVES, PERSPECTIVE_TOKEN_LIMITS, PERSPECTIVE_WORD_LIMITS

PERSPECTIVE_PREFIX = {
    "Ownership & Parties Involved": "ownership_parties:",
    "Financial & Asset Impact": "financial_asset:",
    "Conditions & Procedure": "conditions_procedure:",
    "Rights, Duties & Risks": "rights_duties_risks:",
}


def make_input_text(perspective_type: str, source_text: str) -> str:
    prefix = PERSPECTIVE_PREFIX.get(perspective_type, "summary:")
    return f"{prefix} {source_text}"


def _norm_label(x: str) -> str:
    return re.sub(r"[^a-z]+", "_", str(x).lower()).strip("_")


LABEL_ALIASES = {
    "Ownership & Parties Involved": {
        "ownership_parties", "ownership", "parties", "ownership_parties_involved", "ownership_partiesinvolved"
    },
    "Financial & Asset Impact": {
        "financial_asset", "financial", "asset", "financial_asset_impact"
    },
    "Conditions & Procedure": {
        "conditions_procedure", "conditions", "procedure", "procedural"
    },
    "Rights, Duties & Risks": {
        "rights_duties_risks", "rights", "duties", "risks", "rights_duties"
    },
}


def build_source_for_perspective(
    df,
    perspective_name: str,
    text_col: str = "clause_text",
    pred_col: str = "predicted_perspective",
) -> str:
    """
    Select clauses for a perspective and join with newline.
    Includes fallback contains-based selection and 20k char cap.
    """
    df_local = df[[pred_col, text_col]].copy()
    df_local[pred_col] = df_local[pred_col].astype(str)

    wanted = LABEL_ALIASES[perspective_name]
    keep_mask = df_local[pred_col].apply(lambda s: _norm_label(s) in wanted)

    picked = df_local.loc[keep_mask, text_col].dropna().astype(str).tolist()

    if len(picked) == 0:
        key_hint = list(wanted)[0].split("_")[0]
        keep_mask2 = df_local[pred_col].str.lower().str.contains(key_hint)
        picked = df_local.loc[keep_mask2, text_col].dropna().astype(str).tolist()

    source = "\n".join(picked).strip()
    source = source[:20000]
    return source



def _trim_to_max_words(text: str, max_words: int) -> str:
    if not max_words or max_words <= 0:
        return text

    words = text.split()
    if len(words) <= max_words:
        return text.strip()

    trimmed = " ".join(words[:max_words]).strip()

    # Try to keep only complete sentence(s)
    sentence_end_matches = list(re.finditer(r'[.!?](?=\s|$)', trimmed))
    if sentence_end_matches:
        last_end = sentence_end_matches[-1].end()
        safe_text = trimmed[:last_end].strip()
        if safe_text:
            return safe_text

    # Fallback: trim to last comma/semicolon/colon if available
    fallback_matches = list(re.finditer(r'[,;:](?=\s|$)', trimmed))
    if fallback_matches:
        last_end = fallback_matches[-1].end()
        safe_text = trimmed[:last_end].strip()
        if safe_text:
            return safe_text + " ..."

    # Final fallback: raw trim
    return trimmed.rstrip() + " ..."


@torch.inference_mode()
def generate_summary(
    perspective_type: str,
    source_text: str,
    tok_sum,
    mod_sum,
    device: str,
    max_source_len: int,
):
    torch.manual_seed(0)

    input_text = make_input_text(perspective_type, source_text)

    enc = tok_sum(
        input_text,
        return_tensors="pt",
        truncation=True,
        max_length=max_source_len,
    ).to(device)

    cfg = PERSPECTIVE_TOKEN_LIMITS.get(
        perspective_type,
        {"min_new_tokens": 40, "max_new_tokens": 256}
    )

    out_ids = mod_sum.generate(
        **enc,
        do_sample=False,
        num_beams=4,
        max_new_tokens=cfg["max_new_tokens"],
        min_new_tokens=cfg["min_new_tokens"],
        no_repeat_ngram_size=3,
        repetition_penalty=1.1,
        length_penalty=1.0,
        early_stopping=True,
    )

    summary = tok_sum.decode(out_ids[0], skip_special_tokens=True).strip()

    if perspective_type in PERSPECTIVE_WORD_LIMITS:
        _, max_words = PERSPECTIVE_WORD_LIMITS[perspective_type]
        summary = _trim_to_max_words(summary, max_words)

    return summary


def build_perspective_summaries(
    tok_sum,
    mod_sum,
    device: str,
    max_source_len: int,
    normalized_grouped_text: dict,
) -> dict:
    """
    Build summaries directly from normalized grouped text.
    """
    final = {}
    for p in PERSPECTIVES:
        src = str(normalized_grouped_text.get(p, "") or "").strip()
        if not src:
            final[p] = "(No clauses found for this perspective)"
            continue
        final[p] = generate_summary(p, src, tok_sum, mod_sum, device, max_source_len)
    return final


def print_perspective_summaries(summaries: dict) -> str:
    blocks = []
    for p in PERSPECTIVES:
        blocks.append("\n" + "=" * 90)
        blocks.append(p)
        blocks.append("-" * 90)
        blocks.append(str(summaries.get(p, "")).strip())
    return "\n".join(blocks).strip()