import re
from typing import List


LEGAL_BOUNDARY_PATTERNS = [
    r"\bWHEREAS\b",
    r"\bNOW\s+KNOW\s+YE\b",
    r"\bKNOW\s+ALL\s+MEN\s+BY\s+THESE\s+PRESENTS\b",
    r"\bWITNESSETH\b",
    r"\bIN\s+WITNESS\s+WHEREOF\b",
    r"\bSCHEDULE\b",
    r"\bFIRST\s+SCHEDULE\b",
    r"\bSECOND\s+SCHEDULE\b",
    r"\bTHIRD\s+SCHEDULE\b",
    r"\bDESCRIPTION\s+OF\s+THE\s+PROPERTY\b",
    r"\bTO\s+ALL\s+TO\s+WHOM\s+THESE\s+PRESENTS\s+SHALL\s+COME\b",
    r"\bAND\s+WHEREAS\b",
    r"\bI\s+DO\s+HEREBY\b",
    r"\bHEREBY\s+AGREE\b",
    r"\bTHE\s+VENDOR\b",
    r"\bTHE\s+VENDEE\b",
    r"\bTHE\s+DONOR\b",
    r"\bTHE\s+DONEE\b",
    r"\bTHE\s+LESSOR\b",
    r"\bTHE\s+LESSEE\b",
    r"\bTHE\s+MORTGAGOR\b",
    r"\bTHE\s+MORTGAGEE\b",
]


HEADING_LINE_RE = re.compile(
    r"^(?:"
    r"PRIOR\s+REGISTRATION.*|"
    r"DEED\s+OF\s+TRANSFER.*|"
    r"DEED\s+OF\s+GIFT.*|"
    r"DEED\s+OF\s+LEASE.*|"
    r"LAST\s+WILL\s*(?:&|AND)?\s*TESTAMENT.*|"
    r"MORTGAGE\s+OF\s+IMMOVABLE\s+PROPERTY.*|"
    r"THIS\s+INDENTURE.*|"
    r"NO\.?\s*[:\-]?.*|"
    r"-:\s*S\s*E\s*N\s*D.*G\s*R\s*E\s*E\s*T\s*I\s*N\s*G\s*S\s*:-"
    r")$",
    flags=re.IGNORECASE,
)


ROLE_TRIGGER_RE = re.compile(
    r"\b(?:VENDOR|VENDEE|PURCHASER|DONOR|DONEE|LESSOR|LESSEE|MORTGAGOR|MORTGAGEE|EXECUTOR|TESTATOR)\b",
    flags=re.IGNORECASE,
)


NUMBERED_LINE_RE = re.compile(r"^\s*(?:\(?\d+[\)\.]|[IVXLCDM]+\.|[A-Z]\.)\s+")
SENTENCE_SPLIT_RE = re.compile(r'(?<=[.;:])\s+(?=(?:[A-Z"“]|\(?\d+\)|\d+\.))')
ALL_CAPS_SPACED_RE = re.compile(r"^(?:[A-Z]\s+){3,}[A-Z]\s*$")
MARKER_FMT = "\n§BOUNDARY§ {}\n"


# Avoid splitting on legal / document abbreviations.
ABBREVIATION_RE = re.compile(
    r"(?:\bNo|\bNos|\bNIC|\bN\.I\.C|\bRs|\bDr|\bMr|\bMrs|\bMs|\bLtd|\bCo|\bInc|\bAve|\bRd|\bSt)\.$",
    flags=re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _insert_structure_boundaries(text: str) -> str:
    # Add boundaries around strong inline legal markers.
    for pat in LEGAL_BOUNDARY_PATTERNS:
        text = re.sub(
            rf"(?<!§BOUNDARY§\s)({pat})",
            lambda m: MARKER_FMT.format(m.group(1).strip()),
            text,
            flags=re.IGNORECASE,
        )

    # Add boundaries for numbered clauses after a newline.
    text = re.sub(r"\n(?=\s*(?:\(?\d+[\)\.]|[IVXLCDM]+\.|[A-Z]\.)\s+)", "\n§BOUNDARY§ ", text)
    return text


def _split_line_structured(text: str) -> List[str]:
    pieces: List[str] = []
    current: List[str] = []

    def flush():
        nonlocal current
        joined = " ".join(part.strip() for part in current if part.strip()).strip()
        if joined:
            pieces.append(joined)
        current = []

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            flush()
            continue

        is_heading = bool(HEADING_LINE_RE.match(line) or ALL_CAPS_SPACED_RE.match(line))
        is_numbered = bool(NUMBERED_LINE_RE.match(line))
        is_marker = line.startswith("§BOUNDARY§")
        is_role_heavy = bool(ROLE_TRIGGER_RE.search(line)) and len(line.split()) <= 20

        if is_marker or is_heading or is_numbered or is_role_heavy:
            flush()
            cleaned = line.replace("§BOUNDARY§", "").strip(" :-")
            if cleaned:
                current.append(cleaned)
                flush()
            continue

        current.append(line)

    flush()
    return pieces


def _split_sentences(piece: str) -> List[str]:
    if not piece:
        return []

    piece = re.sub(r"\s+", " ", piece).strip()
    if not piece:
        return []

    parts = []
    buf = []
    tokens = re.split(r"(\s+)", piece)
    for i, tok in enumerate(tokens):
        buf.append(tok)
        token_str = "".join(buf).strip()
        if tok and tok[-1:] in ".;:":
            last_word = re.sub(r"\s+", "", token_str).split(" ")[-1] if token_str else ""
            if ABBREVIATION_RE.search(last_word):
                continue
        joined = "".join(buf)
        if SENTENCE_SPLIT_RE.search(joined):
            split_parts = SENTENCE_SPLIT_RE.split(joined)
            if split_parts:
                for sub in split_parts[:-1]:
                    sub = sub.strip()
                    if sub:
                        parts.append(sub)
                buf = [split_parts[-1]]

    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _merge_short_clauses(chunks: List[str], min_length: int) -> List[str]:
    merged: List[str] = []
    buffer = ""

    for chunk in chunks:
        chunk = re.sub(r"\s+", " ", chunk).strip(" -:\n\t")
        if not chunk:
            continue

        if len(chunk) < min_length:
            buffer = f"{buffer} {chunk}".strip()
            continue

        if buffer:
            candidate = f"{buffer} {chunk}".strip()
            merged.append(candidate)
            buffer = ""
        else:
            merged.append(chunk)

    if buffer:
        if merged:
            merged[-1] = f"{merged[-1]} {buffer}".strip()
        else:
            merged.append(buffer)

    return [m for m in merged if len(m) >= min_length]


# Improved clause segmentation for legal deeds.
def split_into_clauses(text, min_length=30):
    text = _normalize_text(text or "")
    if not text:
        return []

    text = _insert_structure_boundaries(text)
    line_pieces = _split_line_structured(text)

    sentence_level: List[str] = []
    for piece in line_pieces:
        subs = _split_sentences(piece)
        if subs:
            sentence_level.extend(subs)
        else:
            sentence_level.append(piece)

    return _merge_short_clauses(sentence_level, min_length=min_length)
