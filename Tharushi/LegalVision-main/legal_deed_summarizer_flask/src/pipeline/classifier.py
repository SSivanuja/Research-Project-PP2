import numpy as np
import torch
import pandas as pd

from src.config import CLASSIFIER_MAX_LEN
from src.pipeline.deed_processor import split_into_clauses


def _get_label_name(id2label, i: int) -> str:
    """
    Notebook-equivalent robust label mapping:
    - id2label can be dict with keys 0 or "0"
    - or list/tuple
    """
    if isinstance(id2label, dict):
        if i in id2label:
            return id2label[i]
        if str(i) in id2label:
            return id2label[str(i)]
        key = sorted(id2label.keys())[i]
        return id2label[key]
    elif isinstance(id2label, (list, tuple)):
        return id2label[i]
    else:
        return str(id2label)


def classify_clause(clause_text: str, tokenizer, model) -> dict:
    """
    Notebook-style single clause classification:
    tokenizer -> model -> logits -> softmax probs
    """
    id2label = model.config.id2label
    num_labels = model.config.num_labels

    inputs = tokenizer(
        clause_text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=CLASSIFIER_MAX_LEN,
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

    pred_id = int(np.argmax(probs))
    pred_label = _get_label_name(id2label, pred_id)
    confidence = float(probs[pred_id])

    # also expose full probability vector per label
    prob_by_label = {}
    for i in range(num_labels):
        lbl = _get_label_name(id2label, i)
        prob_by_label[f"prob_{lbl}"] = float(probs[i])

    # top-2
    top2_idx = np.argsort(probs)[::-1][:2]
    top2 = [(_get_label_name(id2label, int(i)), float(probs[i])) for i in top2_idx]
    top2_str = ", ".join([f"{lbl} ({p:.2f})" for lbl, p in top2])

    return {
        "predicted_perspective": pred_label,
        "confidence": confidence,
        "top2_labels": top2_str,
        "prob_by_label": prob_by_label,
    }


def classify_deed(raw_deed_text: str, tokenizer, model, min_clause_length=30) -> pd.DataFrame:
    """
    Notebook-equivalent deed classification:
    - split_into_clauses
    - run inference per clause
    - return a dataframe with the SAME style columns:
        clause_no, predicted_perspective, top2_labels, clause_text, prob_<label>...
    """
    clauses = split_into_clauses(raw_deed_text, min_length=min_clause_length)

    rows = []
    id2label = model.config.id2label
    num_labels = model.config.num_labels

    for idx, cl_text in enumerate(clauses, start=1):
        out = classify_clause(cl_text, tokenizer, model)

        row = {
            "clause_no": idx,
            "predicted_perspective": out["predicted_perspective"],
            "top2_labels": out["top2_labels"],
            "clause_text": cl_text,
        }
        # add probabilities per label, exactly like notebook "prob_<label>"
        for i in range(num_labels):
            lbl = _get_label_name(id2label, i)
            row[f"prob_{lbl}"] = float(out["prob_by_label"][f"prob_{lbl}"])
        rows.append(row)

    df = pd.DataFrame(rows)
    return df
