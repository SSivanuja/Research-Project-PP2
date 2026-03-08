import os
import json
import re
from google import genai


def _get_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")


def _extract_json_block(text: str) -> str:
    text = (text or "").strip()

    # Remove markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    # If whole text is already JSON-like, return it
    if text.startswith("{") and text.endswith("}"):
        return text
    if text.startswith("[") and text.endswith("]"):
        return text

    # Fallback: extract first outermost {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    return text


def _repair_common_json_issues(text: str) -> str:
    """
    Repair common Gemini JSON mistakes:
    - unquoted object keys
    - trailing commas before } or ]
    - smart quotes
    """
    t = text.strip()

    # normalize smart quotes
    t = t.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

    # remove trailing commas
    t = re.sub(r",\s*([}\]])", r"\1", t)

    # quote unquoted keys: { key: ... } or , key: ...
    t = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*:)', r'\1"\2"\3', t)

    return t


def _parse_json_safely(text: str) -> dict:
    raw = (text or "").strip()
    if not raw:
        raise RuntimeError("Gemini returned empty output.")

    # Try direct parse
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Try extracted JSON block
    block = _extract_json_block(raw)
    try:
        return json.loads(block)
    except Exception:
        pass

    # Try repaired block
    repaired = _repair_common_json_issues(block)
    try:
        return json.loads(repaired)
    except Exception as e:
        preview = repaired[:800]
        raise RuntimeError(f"Gemini returned invalid JSON after repair attempt: {str(e)} | Output preview: {preview}")


def gemini_json(prompt: str, *, temperature: float = 0.1) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment (.env)")

    client = genai.Client(api_key=api_key)
    model_name = _get_model_name()

    resp = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config={
            "temperature": temperature,
            "response_mime_type": "application/json",
        },
    )

    text = (getattr(resp, "text", None) or "").strip()
    return _parse_json_safely(text)