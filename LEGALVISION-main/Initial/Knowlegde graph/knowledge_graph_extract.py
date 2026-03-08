import os, re, json, uuid
from pathlib import Path
from typing import List, Dict, Optional

RAW_DOCX = Path("./data/raw/30 generated data sets for six types deeds.docx")
RAW_TXT_DIR = Path("./data/raw/txt/")   # optional: when I export deeds to .txt
OUT_DIR = Path("./data/structured/")
OUT_DIR.mkdir(parents=True, exist_ok=True)

USE_DOCX = True  # set False to parse TXT files in RAW_TXT_DIR

def read_docx_paragraphs(docx_path: Path) -> List[str]:
    """Read all paragraphs from a DOCX into a list of strings."""
    try:
        from docx import Document  
    except ImportError:
        raise SystemExit("Please install python-docx or set USE_DOCX = False and use TXT mode.")
    doc = Document(str(docx_path))
    paras = [p.text.strip() for p in doc.paragraphs]
    lines = [ln for ln in paras if ln]
    return lines

def read_txt_files(txt_dir: Path) -> List[str]:
    """Read all .txt files as separate deed blocks (one deed per file)."""
    blocks = []
    for p in sorted(txt_dir.glob("*.txt")):
        blocks.append(p.read_text(encoding="utf-8", errors="ignore"))
    return blocks

def normalize_whitespace(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s.replace("\xa0", " ")).strip()

def collapse_lines(lines: List[str]) -> str:
    txt = "\n".join(lines)
    txt = re.sub(r"\n{2,}", "\n\n", txt)
    return txt

DEED_SPLIT_PATTERNS = [
    r"(?=^\s*(DEED OF TRANSFER|DEED OF GIFT|LAST WILL|LAST WILL & TESTAMENT)\b)",
    r"(?=^\s*Code\s*No\.?|^\s*CODE\s*NO\.?)",
]

def split_into_deeds(full_text: str) -> List[str]:
    """
    Split one big text into per-deed blocks using common headers.
    Heuristic: split on headings ('DEED OF TRANSFER', 'DEED OF GIFT', 'LAST WILL', 'Code No.').
    """
    pattern = re.compile("|".join(DEED_SPLIT_PATTERNS), re.IGNORECASE | re.MULTILINE)
    idxs = [m.start() for m in pattern.finditer(full_text)]
    if not idxs:
        return [full_text.strip()]
    idxs.append(len(full_text))
    blocks = []
    for i in range(len(idxs) - 1):
        block = full_text[idxs[i]:idxs[i+1]].strip()
        if len(block) > 20:
            blocks.append(block)
    return blocks

date_re = re.compile(r"(?i)\b(\d{4}[-./]\d{2}[-./]\d{2}|\d{2}[-./]\d{2}[-./]\d{4})\b")
code_re = re.compile(r"(?i)\bCode\s*No\.?\s*[:\-]?\s*([A-Za-z0-9/\-]+)")
nic_re = re.compile(r"\b\d{12}\b|\b\d{9}[VvXx]\b")
lkr_re = re.compile(r"(?i)\bRs\.?\s*([\d,]+(?:\.\d{1,2})?)")
plan_re = re.compile(r"(?i)\bPlan\s*No\.?\s*([A-Za-z0-9/\-]+)(?:\s*dated\s*([0-9./-]+))?")
lot_re = re.compile(r"(?i)\bLot\s*([A-Za-z0-9]+)\b")
prior_reg_re = re.compile(r"(?i)\bPRIOR\s+REG(?:ISTRATION)?\s*[:\-]?\s*([A-Za-z0-9/\-]+)")
registry_re = re.compile(r"(?i)\bRegistry(?:\s*Office)?\s*[:\-]?\s*([A-Za-z \-]+)")
jurisdiction_re = re.compile(r"(?i)\b(Jurisdiction|District|Division)\s*[:\-]?\s*([A-Za-z \-]+)")
extent_re = re.compile(r"(?i)\bEXTENT\s*[:\-]?\s*([A-Za-z0-9 .:\-]+?)\b(?:P|PERCH|PERCHES)\b")
boundary_line_re = re.compile(r"(?im)^\s*(NORTH|EAST|SOUTH|WEST)\s*[:\-]\s*(.+)$")

def detect_instrument_type(text: str) -> str:
    t = text.lower()
    if "deed of transfer" in t:
        return "sale_transfer"
    if "deed of gift" in t:
        return "gift"
    if "last will" in t or "last will & testament" in t:
        return "will"
    return "unknown"

def first_match(regex: re.Pattern, text: str, group: int = 1) -> Optional[str]:
    m = regex.search(text)
    return m.group(group).strip() if m else None

def find_all_dates(text: str) -> List[str]:
    return [normalize_whitespace(m.group(1)) for m in date_re.finditer(text)]

def extract_boundaries(text: str) -> Dict[str, str]:
    bounds = {}
    for m in boundary_line_re.finditer(text):
        side = m.group(1).upper()
        desc = normalize_whitespace(m.group(2))
        bounds[side[0]] = desc  
    return bounds

def extract_party_line(text: str, label_keywords: List[str]) -> Optional[str]:
    """
    Heuristic: find the line that contains party label like VENDOR/VENDEE/DONOR/DONEE/TESTATOR/EXECUTOR.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        lower = ln.lower()
        if any(k in lower for k in label_keywords):
            return ln
    return None

def parse_names_from_line(line: str) -> List[str]:
    """
    Very simple name parsing: split by 'and', commas, slashes; filter short tokens.
    """
    if not line:
        return []
    cleaned = re.sub(r"(?i)\b(vendor|vendee|donor|donee|testator|executor|executrix|wife|husband|mr\.|mrs\.|ms\.)\b", "", line)
    parts = re.split(r"\s*(?:,| and |/|;)\s*", cleaned)
    names = []
    for p in parts:
        token = normalize_whitespace(p)
        if len(token.split()) >= 2:  
            names.append(token)
    return names

def parse_deed_block(text: str, idx:int) -> Dict:
    block = normalize_whitespace(text)
    instrument = detect_instrument_type(block)

    code = first_match(code_re, block)
    dates = find_all_dates(block)
    date = dates[0] if dates else None

    vendor_line = extract_party_line(block, ["vendor"])
    vendee_line = extract_party_line(block, ["vendee", "purchaser", "buyer"])
    donor_line  = extract_party_line(block, ["donor"])
    donee_line  = extract_party_line(block, ["donee"])
    testator_ln = extract_party_line(block, ["testator"])
    exec_ln     = extract_party_line(block, ["executor", "executrix"])

    vendor_names = parse_names_from_line(vendor_line)
    vendee_names = parse_names_from_line(vendee_line)
    donor_names  = parse_names_from_line(donor_line)
    donee_names  = parse_names_from_line(donee_line)
    testator_names = parse_names_from_line(testator_ln)
    executor_names = parse_names_from_line(exec_ln)

    nics = list(dict.fromkeys(nic_re.findall(block)))  

    plan_no = None
    plan_date = None
    m = plan_re.search(block)
    if m:
        plan_no = m.group(1)
        plan_date = (m.group(2) or "").strip() or None

    lot = first_match(lot_re, block)
    prior_reg = first_match(prior_reg_re, block)
    registry = first_match(registry_re, block)
    jurisdiction = None
    mj = jurisdiction_re.search(block)
    if mj:
        jurisdiction = mj.group(2).strip()

    extent_raw = first_match(extent_re, block)
    extent_perches = None
    if extent_raw:
        mnum = re.search(r"(\d+(?:\.\d+)?)", extent_raw)
        if mnum:
            extent_perches = float(mnum.group(1))

    consideration_lkr = None
    m_lkr = lkr_re.search(block)
    if m_lkr:
        try:
            consideration_lkr = float(m_lkr.group(1).replace(",", ""))
        except:
            pass

    boundaries = extract_boundaries(text)

    base = {
        "id": str(uuid.uuid4()),
        "type": instrument,
        "code_number": code or f"UNKNOWN-{idx+1}",
        "date": date,
        "jurisdiction": jurisdiction,
        "registry_office": registry,
        "plan": {"plan_no": plan_no, "plan_date": plan_date, "surveyor": None},
        "property": {
            "lot": lot,
            "land_name": None,
            "assessment_no": None,
            "address_text": None,
            "extent_perches": extent_perches,
            "boundaries": {
                "N": boundaries.get("N"),
                "E": boundaries.get("E"),
                "S": boundaries.get("S"),
                "W": boundaries.get("W"),
            },
        },
        "prior_registration": prior_reg,
        "consideration_lkr": consideration_lkr,
        "source": {"provenance": "30_deed_samples_v1", "fields_found": []},
    }

    if instrument == "sale_transfer":
        base["vendor"] = {"names": vendor_names}
        base["vendee"] = {"names": vendee_names}
    elif instrument == "gift":
        base["donor"] = {"names": donor_names}
        base["donee"] = {"names": donee_names}
    elif instrument == "will":
        base["testator"] = {"names": testator_names}
        base["executors"] = [{"name": n} for n in executor_names]

    if nics:
        base["ids"] = {"nic_all": nics}

    present = [k for k, v in [
        ("code_number", code),
        ("date", date),
        ("plan_no", plan_no),
        ("lot", lot),
        ("prior_registration", prior_reg),
        ("registry_office", registry),
        ("jurisdiction", jurisdiction),
        ("extent", extent_perches),
        ("consideration_lkr", consideration_lkr),
        ("boundariesN", boundaries.get("N")),
        ("boundariesE", boundaries.get("E")),
        ("boundariesS", boundaries.get("S")),
        ("boundariesW", boundaries.get("W")),
    ] if v]
    base["source"]["fields_found"] = present

    return base

def parse_from_docx(docx_path: Path) -> List[str]:
    """Return deed blocks parsed from a DOCX (paragraphs joined then split)."""
    lines = read_docx_paragraphs(docx_path)
    whole = collapse_lines(lines)
    return split_into_deeds(whole)

def run_pipeline():
    if USE_DOCX:
        if not RAW_DOCX.exists():
            raise SystemExit(f"DOCX not found at: {RAW_DOCX}")
        deed_blocks = parse_from_docx(RAW_DOCX)
    else:
        if not RAW_TXT_DIR.exists():
            raise SystemExit(f"TXT directory not found at: {RAW_TXT_DIR}")
        deed_blocks = read_txt_files(RAW_TXT_DIR)

    if not deed_blocks:
        print("No deeds found.")
        return

    print(f"Found {len(deed_blocks)} deed block(s). Extracting...")
    outputs = []
    for i, block in enumerate(deed_blocks):
        data = parse_deed_block(block, i)
        outputs.append(data)

        out_path = OUT_DIR / f"DEED_{i+1:03d}.json"
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  → {out_path.name} ({data['type']}) fields: {len(data['source']['fields_found'])}")

    # Optional: also write a combined JSONL
    jsonl_path = OUT_DIR / "deeds.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as jf:
        for d in outputs:
            jf.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"Done. Wrote {len(outputs)} JSON files + deeds.jsonl.")

if __name__ == "__main__":
    run_pipeline()
