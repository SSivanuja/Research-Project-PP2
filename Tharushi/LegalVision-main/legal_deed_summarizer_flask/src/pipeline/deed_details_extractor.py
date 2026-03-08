import json
from src.llm.gemini_client import gemini_json
from src.pipeline.deed_details_schema import COMMON_DEED_DETAILS_SCHEMA

BASE_RULES = """
You are extracting structured details from a Sri Lankan legal deed.

STRICT RULES:
1) DO NOT invent anything not present in the deed text.
2) If a value is not explicitly present, set it to null.
3) DO NOT normalize or reformat dates. Copy date text exactly as in deed.
4) DO NOT convert written money to numeric, and DO NOT convert numeric to words.
5) Keep capitalization/spelling exactly as in the deed.
6) Output MUST be valid JSON only.
"""

def extract_deed_details_with_gemini(deed_text: str) -> dict:
    prompt = f"""
{BASE_RULES}

Return JSON that follows this schema (keys exactly as shown):
{json.dumps(COMMON_DEED_DETAILS_SCHEMA, ensure_ascii=False, indent=2)}

DEED TEXT:
\"\"\"{deed_text}\"\"\"
""".strip()

    return gemini_json(prompt, temperature=0.1)