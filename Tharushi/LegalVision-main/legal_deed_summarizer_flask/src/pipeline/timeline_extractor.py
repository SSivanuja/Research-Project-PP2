import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

import pandas as pd
import dateparser

from src.pipeline.resources import get_nlp

# ===========================
# A) build_lines_df(text)
# ===========================
def build_lines_df(text: str) -> pd.DataFrame:
    """
    Split input into lines and produce:
    line_id (L0001...), line_no, char_start, char_end, line_text
    Offsets are kept for UI highlighting.
    """
    lines = text.splitlines()
    recs = []
    cursor = 0

    for i, line in enumerate(lines, start=1):
        line_txt = line.rstrip("\n")
        start = cursor
        end = start + len(line_txt)

        recs.append({
            "line_id": f"L{i:04d}",
            "line_no": i,
            "char_start": start,
            "char_end": end,
            "line_text": line_txt
        })

        # account for newline removed by splitlines()
        cursor = end + 1

    return pd.DataFrame(recs)


# ===========================
# B) Explicit Date Extraction
# ===========================
MONTHS = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
MONTHS_RE = re.compile(MONTHS, re.IGNORECASE)

BAD_DATE_LIKE = re.compile(r"^\s*(no\.?|no|lot|colombo)\s*\d+\s*$", re.IGNORECASE)

DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b"),                         # 09.3.2002 / 10.02.2017
    re.compile(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b"),                           # 2001.12.21 / 2008.10.15
    re.compile(rf"\b\d{{1,2}}(st|nd|rd|th)?\s+{MONTHS}\s+\d{{4}}\b", re.I),     # 29th July 2017
    re.compile(rf"\b{MONTHS}\s+\d{{1,2}}(st|nd|rd|th)?,\s+\d{{4}}\b", re.I),    # July 29, 2017
    re.compile(rf"\b{MONTHS}\s+\d{{1,2}}(st|nd|rd|th)?\s+\d{{4}}\b", re.I),     # July 29 2017
    re.compile(rf"\b\d{{1,2}}(st|nd|rd|th)?\s+day\s+of\s+{MONTHS}\s+\d{{4}}\b", re.I),  # 29th day of July 2017
    re.compile(rf"\b{MONTHS}\s+\d{{4}}\b", re.I),  # April 2015
]

LEGAL_DAY_OF_MONTH = re.compile(
    rf"\b(?:[A-Za-z\-]+\s+)?\(\s*(\d{{1,2}})(st|nd|rd|th)?\s*\)\s*day\s+of\s+{MONTHS}.*?\(\s*(\d{{4}})\s*\)",
    re.IGNORECASE
)


def _has_4digit_year(s: str) -> bool:
    return bool(re.search(r"\b(18|19|20)\d{2}\b", s or ""))


def _is_full_numeric_date(s: str) -> bool:
    s = (s or "").strip()
    return bool(re.match(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$", s)) or bool(
        re.match(r"^\d{4}[./-]\d{1,2}[./-]\d{1,2}$", s)
    )


def _is_year_only(s: str) -> bool:
    s = (s or "").strip()
    return bool(re.fullmatch(r"\(?\s*(18|19|20)\d{2}\s*\)?", s))


_WORD_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}


def _words_to_number(tokens):
    total = 0
    for t in tokens:
        t = t.lower().strip("-")
        if t in _WORD_NUM:
            total += _WORD_NUM[t]
    return total


def normalize_written_year(text: str) -> str:
    """
    Converts e.g. 'Two Thousand and Twenty One' -> '2021'
    Applied only when month names appear in the surrounding text.
    """
    if not text:
        return text

    def repl(m):
        tail = m.group(1) or ""
        tokens = re.findall(r"[A-Za-z\-]+", tail)
        n = _words_to_number(tokens)
        if 0 <= n <= 99:
            return str(2000 + n)
        return m.group(0)

    return re.sub(
        r"\bTwo\s+Thousand(?:\s+and)?\s+([A-Za-z\-\s]+)\b",
        repl,
        text,
        flags=re.IGNORECASE,
    )


def strict_parse_date(ds: str):
    ds = (ds or "").strip()
    if not ds:
        return None
    if BAD_DATE_LIKE.match(ds):
        return None
    if _is_year_only(ds):
        return None
    if (not _has_4digit_year(ds)) and (not _is_full_numeric_date(ds)):
        return None

    # month-year like "April 2015" -> 2015-04-01
    if re.fullmatch(rf"{MONTHS}\s+\d{{4}}", ds, flags=re.IGNORECASE):
        return dateparser.parse(
            ds,
            settings={"STRICT_PARSING": False, "PREFER_DAY_OF_MONTH": "first", "PREFER_DATES_FROM": "past"},
        )

    if re.match(r"^\d{4}[./-]\d{1,2}[./-]\d{1,2}$", ds):
        return dateparser.parse(ds, settings={"STRICT_PARSING": True, "DATE_ORDER": "YMD"})
    if re.match(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$", ds):
        return dateparser.parse(ds, settings={"STRICT_PARSING": True, "DATE_ORDER": "DMY"})

    return dateparser.parse(ds, settings={"STRICT_PARSING": True})


def extract_date_matches(text: str):
    """
    Returns list of dicts:
      {date_text, date_iso, start, end, method}
    Includes REGEX + LEGAL_DAY_OF_MONTH + spaCy DATE entities.
    """
    text = text or ""
    if MONTHS_RE.search(text):
        text = normalize_written_year(text)

    found = []

    for m in LEGAL_DAY_OF_MONTH.finditer(text):
        day = int(m.group(1))
        month = m.group(3)
        year = int(m.group(4))
        dt = dateparser.parse(f"{day} {month} {year}", settings={"STRICT_PARSING": True})
        if dt:
            found.append({
                "date_text": m.group(0),
                "date_iso": dt.date().isoformat(),
                "start": m.start(),
                "end": m.end(),
                "method": "LEGAL_DAY_OF_MONTH",
            })

    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            ds = m.group(0)
            dt = strict_parse_date(ds)
            if dt:
                found.append({
                    "date_text": ds,
                    "date_iso": dt.date().isoformat(),
                    "start": m.start(),
                    "end": m.end(),
                    "method": "REGEX",
                })

    nlp = get_nlp()
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ != "DATE":
                continue
            ds = ent.text.strip()
            dt = strict_parse_date(ds)
            if dt:
                found.append({
                    "date_text": ds,
                    "date_iso": dt.date().isoformat(),
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "method": "SPACY",
                })

    uniq = []
    seen = set()
    for x in found:
        key = (x["date_iso"], x["start"], x["end"], x["method"])
        if key not in seen:
            seen.add(key)
            uniq.append(x)
    return uniq


# ===========================
# C) Context extraction
# ===========================
def extract_ref_key(context_text: str):
    s = (context_text or "").lower()

    m = re.search(r"\bplan\s*no\.?\s*(\d+)\b", s, re.I)
    if m:
        return f"PLAN_{m.group(1)}"

    m = re.search(r"\bdeed\s*no\.?\s*(\d+)\b", s, re.I)
    if m:
        return f"DEED_{m.group(1)}"

    m = re.search(r"\bcertificate\s*no\.?\s*(\d+)\b", s, re.I)
    if m:
        return f"CERT_{m.group(1)}"

    return None


def classify_event_type_from_context(context_text: str) -> str:
    s = (context_text or "").lower()

    if any(k in s for k in ["bank certificate", "certificate of payment", "peoples bank", "provincial council"]):
        return "Bank Certificate/Stamp"

    if any(k in s for k in ["in witness whereof", "date of attestation", "notary public", "attest", "read over", "signed", "set his hand"]):
        return "Execution/Attestation"

    if any(k in s for k in ["deed no", "under and by virtue", "prior registration", "registered under title"]):
        return "Prior Title/Deed"

    if any(k in s for k in ["plan no", "licensed surveyor", "depicted in plan", "plan"]):
        return "Survey/Plan"

    if any(k in s for k in ["consideration", "rupees", "paid", "payment", "receipt whereof", "loan obtained", "sum of"]):
        return "Payment/Consideration"

    if any(k in s for k in ["register", "registration", "land registry", "folio", "day book"]):
        return "Registration"

    return "Other Date"


# ===========================
# D) Build raw timeline events list
# ===========================
def _iter_sentences_from_text(text: str):
    text = (text or "").strip()
    if not text:
        return []

    nlp = get_nlp()
    if nlp is not None:
        doc = nlp(text)
        sents = [s.text.strip() for s in doc.sents if s.text.strip()]
        if sents:
            return sents

    return [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", text) if x.strip()]


def build_timeline_events_raw(lines_df: pd.DataFrame, raw_text: str = None):
    timeline_events_raw = []
    event_counter = 1
    WINDOW = 80

    # pass 1: line-by-line extraction
    for _, r in lines_df.iterrows():
        line = (r["line_text"] or "").strip()
        if not line:
            continue

        for sent_text in _iter_sentences_from_text(line):
            matches = extract_date_matches(sent_text)

            for m in matches:
                a = max(0, m["start"] - WINDOW)
                b = min(len(sent_text), m["end"] + WINDOW)
                context_text = sent_text[a:b]

                event_type = classify_event_type_from_context(context_text)
                ref_key = extract_ref_key(context_text)

                timeline_events_raw.append({
                    "event_id": f"E{event_counter}",
                    "event_type": event_type,
                    "date_iso": m["date_iso"],
                    "time_phrase": m["date_text"],
                    "event_title": (sent_text[:70] + "...") if len(sent_text) > 70 else sent_text,
                    "event_description": sent_text,
                    "ref_key": ref_key or "",
                    "match_method": "REGEX" if m["method"] in ("REGEX", "LEGAL_DAY_OF_MONTH") else "SPACY",
                    "source_line_id": r["line_id"],
                    "source_line_no": int(r["line_no"]),
                    "char_start": int(r["char_start"]),
                    "char_end": int(r["char_end"]),
                    "source_text": line,
                })
                event_counter += 1

    raw_df = pd.DataFrame(timeline_events_raw)

    # pass 2: if line-based pass finds nothing, retry on full text
    if (raw_df is None or raw_df.empty) and raw_text:
        fallback_events = []

        for sent_text in _iter_sentences_from_text(raw_text):
            matches = extract_date_matches(sent_text)

            for m in matches:
                a = max(0, m["start"] - WINDOW)
                b = min(len(sent_text), m["end"] + WINDOW)
                context_text = sent_text[a:b]

                event_type = classify_event_type_from_context(context_text)
                ref_key = extract_ref_key(context_text)

                fallback_events.append({
                    "event_id": f"E{event_counter}",
                    "event_type": event_type,
                    "date_iso": m["date_iso"],
                    "time_phrase": m["date_text"],
                    "event_title": (sent_text[:70] + "...") if len(sent_text) > 70 else sent_text,
                    "event_description": sent_text,
                    "ref_key": ref_key or "",
                    "match_method": "REGEX" if m["method"] in ("REGEX", "LEGAL_DAY_OF_MONTH") else "SPACY",
                    "source_line_id": "FULLTEXT",
                    "source_line_no": 0,
                    "char_start": 0,
                    "char_end": len(sent_text),
                    "source_text": sent_text,
                })
                event_counter += 1

        raw_df = pd.DataFrame(fallback_events)
        return fallback_events, raw_df

    return timeline_events_raw, raw_df


# ===========================
# E) Dedupe logic
# ===========================
def dedupe_timeline(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    def key_row(r):
        rk = r.get("ref_key")
        if rk:
            return f"{r['date_iso']}|{r['event_type']}|{rk}"
        return f"{r['date_iso']}|{r['event_type']}|{r['time_phrase']}"

    df = df.copy()
    df["dedupe_key"] = df.apply(key_row, axis=1)

    groups = []
    for _, g in df.groupby("dedupe_key", sort=False):
        g = g.copy()
        g["len_desc"] = g["event_description"].astype(str).str.len()
        rep = g.sort_values(by=["len_desc"], ascending=False).iloc[0].to_dict()

        rep["mentions_count"] = int(len(g))
        rep["evidence_lines"] = ", ".join(g["source_line_id"].astype(str).tolist())
        rep["evidence_line_nos"] = ", ".join(g["source_line_no"].astype(str).tolist())

        groups.append(rep)

    out = pd.DataFrame(groups).drop(columns=["len_desc", "dedupe_key"], errors="ignore")
    # Ensure string columns never contain NaN
    for col in ["ref_key", "dedupe_key", "evidence_lines", "evidence_line_nos", "time_phrase", "event_title", "event_description", "match_method", "source_line_id", "source_text"]:
        if col in out.columns:
            out[col] = out[col].fillna("").astype(str)

    out["date_sort"] = pd.to_datetime(out["date_iso"], errors="coerce")
    out = out.sort_values(by=["date_sort", "event_type"]).drop(columns=["date_sort"]).reset_index(drop=True)
    return out


# ===========================
# F) Relative deadline extraction (computed)
# ===========================
NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def parse_int_token(tok: str):
    tok = (tok or "").strip().lower()
    if tok.isdigit():
        return int(tok)
    return NUM_WORDS.get(tok)


REL_PATTERNS = [
    re.compile(r"\bwithin\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+days?\b", re.I),
    re.compile(r"\bwithin\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+months?\b", re.I),
    re.compile(r"\bwithin\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+years?\b", re.I),
]


def find_anchor_date(timeline_events):
    if not timeline_events:
        return None

    preferred = []
    for e in timeline_events:
        et = (e.get("event_type") or "").lower()
        if ("execution" in et) or ("agreement" in et) or ("attestation" in et) or ("sign" in et):
            preferred.append(e)

    pool = preferred if preferred else timeline_events
    pool_sorted = sorted(pool, key=lambda x: x.get("date_iso", "9999-12-31"))
    return datetime.fromisoformat(pool_sorted[0]["date_iso"]).date()


def add_relative_deadlines(raw_text: str, timeline_events: list):
    anchor = find_anchor_date(timeline_events)
    if not anchor:
        return timeline_events

    chunks = re.split(r"(?<=[.!?])\s+|\n+", raw_text)

    existing_nums = []
    for e in timeline_events:
        m = re.match(r"^E(\d+)$", str(e.get("event_id", "")))
        if m:
            existing_nums.append(int(m.group(1)))
    next_id = (max(existing_nums) + 1) if existing_nums else (len(timeline_events) + 1)

    for ch in chunks:
        ch_clean = ch.strip()
        if not ch_clean:
            continue

        low = ch_clean.lower()
        if ("date hereof" not in low) and ("from the date" not in low):
            continue

        for pat in REL_PATTERNS:
            m = pat.search(ch_clean)
            if not m:
                continue

            n = parse_int_token(m.group(1))
            if not n:
                continue

            if "days" in pat.pattern.lower():
                due = anchor + relativedelta(days=+n)
                offset_days = n
            elif "months" in pat.pattern.lower():
                due = anchor + relativedelta(months=+n)
                offset_days = (due - anchor).days
            else:
                due = anchor + relativedelta(years=+n)
                offset_days = (due - anchor).days

            timeline_events.append({
                "event_id": f"E{next_id}",
                "event_type": "Relative Deadline (computed)",
                "date_iso": due.isoformat(),
                "relative_offset_days": offset_days,
                "time_phrase": m.group(0),
                "event_title": "Computed deadline from date hereof",
                "event_description": ch_clean,
                "computed_from": anchor.isoformat(),
            })
            next_id += 1

    return timeline_events