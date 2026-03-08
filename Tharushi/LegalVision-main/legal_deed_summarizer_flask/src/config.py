import os
from pathlib import Path

# Flask project root: .../MULTI PERSPECTIVE SUMMARIZATION/legal_deed_summarizer_flask
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Workspace root: .../MULTI PERSPECTIVE SUMMARIZATION
WORKSPACE_ROOT = PROJECT_ROOT.parent

PERSPECTIVES = [
    "Ownership & Parties Involved",
    "Financial & Asset Impact",
    "Conditions & Procedure",
    "Rights, Duties & Risks",
]

# ✅ model folder is at workspace level (NOT inside flask folder)
CLAUSE_CLASSIFIER_DIR = os.getenv(
    "CLAUSE_CLASSIFIER_DIR",
    str(WORKSPACE_ROOT / "model" / "legalbert_clause_perspective_model")
)

GLOSSARY_CSV_PATH = os.getenv(
    "GLOSSARY_CSV_PATH",
    str(WORKSPACE_ROOT / "data" / "raw" / "Legal Jargan Dictonary.csv")
)

DEFAULT_SUMMARIZER_MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "nsi319/legal-led-base-16384"
)

SAVED_SUMMARIZER_DIR = os.getenv(
    "SAVED_SUMMARIZER_DIR",
    str(WORKSPACE_ROOT / "model" / "saved_summarizer_model")
)

def infer_max_source_len(model_name: str) -> int:
    return 4096 if "led" in model_name.lower() else 1024


# -----------------------------
# ✅ Global fallback generation limits
# -----------------------------
MAX_TARGET_LEN = int(os.getenv("MAX_TARGET_LEN", "256"))
MIN_TARGET_LEN = int(os.getenv("MIN_TARGET_LEN", "40"))

CLASSIFIER_MAX_LEN = int(os.getenv("CLASSIFIER_MAX_LEN", "256"))


# -----------------------------
# ✅ Classifier quality control
# -----------------------------
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.55"))
CONFIDENCE_MARGIN_THRESHOLD = float(os.getenv("CONFIDENCE_MARGIN_THRESHOLD", "0.12"))
ENABLE_CONFIDENCE_FILTER = os.getenv(
    "ENABLE_CONFIDENCE_FILTER",
    "true"
).lower() in ("1", "true", "yes", "y")


# -----------------------------
# ✅ Per-perspective summary length policy (WORDS)
# -----------------------------
PERSPECTIVE_WORD_LIMITS = {
    "Ownership & Parties Involved": (60, 100),
    "Financial & Asset Impact": (50, 90),
    "Conditions & Procedure": (70, 120),
    "Rights, Duties & Risks": (80, 130),
}


# -----------------------------
# ✅ Per-perspective generation caps (TOKENS)
# tokens != words, but this aligns well in practice
# -----------------------------
PERSPECTIVE_TOKEN_LIMITS = {
    "Ownership & Parties Involved": {"min_new_tokens": 60, "max_new_tokens": 140},
    "Financial & Asset Impact": {"min_new_tokens": 50, "max_new_tokens": 130},
    "Conditions & Procedure": {"min_new_tokens": 70, "max_new_tokens": 170},
    "Rights, Duties & Risks": {"min_new_tokens": 80, "max_new_tokens": 190},
}


# -----------------------------
# ✅ Utility: get generation config for a perspective
# -----------------------------
def get_generation_limits(perspective: str) -> dict:
    """
    Returns {"min_new_tokens": int, "max_new_tokens": int} for the given perspective.
    Falls back to global MIN_TARGET_LEN / MAX_TARGET_LEN if not configured.
    """
    return PERSPECTIVE_TOKEN_LIMITS.get(
        perspective,
        {"min_new_tokens": MIN_TARGET_LEN, "max_new_tokens": MAX_TARGET_LEN},
    )