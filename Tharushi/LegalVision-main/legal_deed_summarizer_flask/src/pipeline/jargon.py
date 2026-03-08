import re
import pandas as pd


def load_legal_glossary(path):
    """
    Notebook-equivalent glossary loader (Legal Jargan Dictionary.csv).

    Auto-detect:
      - a column for legal term / phrase
      - a column for simple meaning

    Uses typical candidate names and builds {term: simple}.
    """
    glossary = {}
    try:
        df = pd.read_csv(path)

        term_candidates = [
            "term", "Term", "jargon", "Jargon", "Legal Jargon", "legal_jargon",
            "Phrase", "phrase", "Legal Term", "legal_term"
        ]
        simple_candidates = [
            "simple", "Simple", "Plain", "plain", "Meaning", "meaning",
            "Explanation", "explanation", "Definition", "definition"
        ]

        term_col = next((c for c in term_candidates if c in df.columns), None)
        simple_col = next((c for c in simple_candidates if c in df.columns), None)

        if term_col is None or simple_col is None:
            # fallback: pick first two columns if needed
            if len(df.columns) >= 2:
                term_col = term_col or df.columns[0]
                simple_col = simple_col or df.columns[1]
            else:
                return {}

        for _, row in df.iterrows():
            term = str(row.get(term_col, "")).strip()
            simple = str(row.get(simple_col, "")).strip()
            if term and simple and term.lower() != "nan" and simple.lower() != "nan":
                glossary[term] = simple

        return glossary

    except Exception:
        return {}


def normalize_legal_jargon(text, glossary):
    """
    Notebook-equivalent normalization:
    - replace known phrases with simpler equivalents
    - sort by length so longer phrases replaced first
    - keep structure mostly same; only swaps expressions
    """
    if not glossary:
        return text

    new_text = text

    for term, simple in sorted(glossary.items(), key=lambda x: -len(x[0])):
        # whole-word-ish match where possible
        pattern = r"\b" + re.escape(term) + r"\b"
        new_text = re.sub(pattern, simple, new_text, flags=re.IGNORECASE)

    return new_text
