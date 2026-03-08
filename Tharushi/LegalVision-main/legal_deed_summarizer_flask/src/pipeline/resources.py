import os
import torch
import pandas as pd
#import evaluate

# ✅ Timeline: spaCy resource (added, does not remove existing)
import logging
from typing import Optional
import spacy
import pytesseract

# Configure Tesseract OCR path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
)

from src.config import (
    PERSPECTIVES,
    CLAUSE_CLASSIFIER_DIR,
    GLOSSARY_CSV_PATH,
    DEFAULT_SUMMARIZER_MODEL_NAME,
    SAVED_SUMMARIZER_DIR,
    infer_max_source_len,
)
from src.pipeline.jargon import load_legal_glossary


logger = logging.getLogger(__name__)

_RESOURCES = None

_SPACY_MODEL_NAME = "en_core_web_sm"  # timeline extraction


def get_resources():
    """
    Loads all heavy resources once and caches them.
    """
    global _RESOURCES
    if _RESOURCES is not None:
        return _RESOURCES

    device = "cpu"  # notebook used CPU

    # ---------- classifier ----------
    model_dir = CLAUSE_CLASSIFIER_DIR
    if not os.path.isdir(model_dir):
        raise RuntimeError(
            f"Clause classifier folder not found: {model_dir}. "
            f"Place your fine-tuned model at ./legalbert_clause_perspective_model"
        )

    clf_tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
    clf_model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    clf_model.eval()

    # ---------- summarizer ----------
    # Notebook inference cell loads from save_dir "./saved_summarizer_model".
    # If that folder exists -> load it. Else fall back to MODEL_NAME from notebook.
    if os.path.isdir(SAVED_SUMMARIZER_DIR):
        sum_loaded_from = SAVED_SUMMARIZER_DIR
        sum_model_name = DEFAULT_SUMMARIZER_MODEL_NAME  # keep for metadata
        sum_tokenizer = AutoTokenizer.from_pretrained(SAVED_SUMMARIZER_DIR, use_fast=False)
        sum_model = AutoModelForSeq2SeqLM.from_pretrained(SAVED_SUMMARIZER_DIR)
    else:
        sum_loaded_from = DEFAULT_SUMMARIZER_MODEL_NAME
        sum_model_name = DEFAULT_SUMMARIZER_MODEL_NAME
        sum_tokenizer = AutoTokenizer.from_pretrained(DEFAULT_SUMMARIZER_MODEL_NAME, use_fast=False)
        sum_model = AutoModelForSeq2SeqLM.from_pretrained(DEFAULT_SUMMARIZER_MODEL_NAME)

    sum_model.to(torch.device(device))
    sum_model.eval()

    # notebook safety: ensure pad token exists
    if sum_tokenizer.pad_token_id is None and getattr(sum_model.config, "pad_token_id", None) is None:
        # usually tokenizers have pad_token_id; if not, set it to eos_token_id
        if sum_tokenizer.eos_token_id is not None:
            sum_tokenizer.pad_token_id = sum_tokenizer.eos_token_id
            sum_model.config.pad_token_id = sum_tokenizer.pad_token_id

    if getattr(sum_model.config, "pad_token_id", None) is None and sum_tokenizer.pad_token_id is not None:
        sum_model.config.pad_token_id = sum_tokenizer.pad_token_id

    # ---------- glossary ----------
    glossary = {}
    if os.path.isfile(GLOSSARY_CSV_PATH):
        try:
            glossary = load_legal_glossary(GLOSSARY_CSV_PATH)
        except Exception:
            glossary = {}

    # ---------- rouge ----------
   #rouge = evaluate.load("rouge")

    # ✅ Timeline: load spaCy once (cached). App still runs if model missing.
    spacy_nlp: Optional["spacy.language.Language"] = None
    spacy_ok = False
    spacy_err = None
    try:
        spacy_nlp = spacy.load(_SPACY_MODEL_NAME)
        spacy_ok = True
        logger.info("spaCy model loaded: %s", _SPACY_MODEL_NAME)
    except Exception as e:
        spacy_nlp = None
        spacy_ok = False
        spacy_err = str(e)
        logger.exception("Failed to load spaCy model: %s", _SPACY_MODEL_NAME)

    _RESOURCES = {
        "device": device,
        "perspectives": PERSPECTIVES,
        "classifier": {
            "model_dir": model_dir,
            "tokenizer": clf_tokenizer,
            "model": clf_model,
        },
        "summarizer": {
            "loaded_from": sum_loaded_from,
            "model_name": sum_model_name,
            "tokenizer": sum_tokenizer,
            "model": sum_model,
            "max_source_len": infer_max_source_len(sum_model_name),
        },
        "glossary": glossary,
        #"rouge": rouge,
        # ✅ Timeline
        "spacy": {
            "loaded": spacy_ok,
            "model": _SPACY_MODEL_NAME,
            "error": spacy_err,
            "nlp": spacy_nlp,
        },
    }
    return _RESOURCES


# ==========================
# Timeline helpers (additions)
# ==========================

def get_nlp():
    """Return cached spaCy nlp or None."""
    res = get_resources()
    return res.get("spacy", {}).get("nlp")


def spacy_status() -> dict:
    res = get_resources()
    sp = res.get("spacy", {})
    return {
        "loaded": bool(sp.get("loaded")),
        "model": sp.get("model"),
        "error": sp.get("error"),
    }
