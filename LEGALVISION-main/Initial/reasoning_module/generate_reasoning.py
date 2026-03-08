import os, json, pathlib, time, openai, random
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")  
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CTX_DIR = pathlib.Path("./reasoning/contexts")
OUT_DIR = pathlib.Path("./reasoning/synthetic"); OUT_DIR.mkdir(parents=True, exist_ok=True)

reasoning_types = [
    "Title validation and legality",
    "Boundary or extent consistency",
    "Registry and jurisdiction compliance",
    "Prior registration linkage",
    "Plan and lot relationship verification",
    "Consideration and transaction value reasoning"
]

SYSTEM_PROMPT = """You are a Sri Lankan property-law reasoning generator.
For each deed context, produce one detailed JSON object.

Format:
{
  "question": "...",
  "answer_ref": {
    "steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "conclusion": "...",
    "confidence": 0.85
  },
  "reasoning_type": "...",
  "citations": ["[plan_no]", "[lot]", "[prior_registration]"]
}

Guidelines:
- Write 2-4 reasoning steps leading to a clear conclusion.
- Include confidence 0-1 based on data completeness.
- Keep language formal but concise.
- Always output valid JSON, no markdown fences.
"""


def generate_reasoning(context, reasoning_type):
    prompt = (
        f"Context:\n{json.dumps(context, indent=2)}\n\n"
        f"Generate ONE reasoning sample of type: {reasoning_type}."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    txt = resp.choices[0].message.content.strip()
    try:
        data = json.loads(txt)
    except Exception:
        data = {"raw_output": txt, "reasoning_type": reasoning_type}
    return data

def main():
    ctx_files = sorted(CTX_DIR.glob("*.json"))
    for fp in ctx_files:
        ctx = json.loads(fp.read_text(encoding="utf-8"))
        results = []

        styles = ["legal_analytical", "plain_explanatory"]
        for rtype in random.sample(reasoning_types, k=3):
            for style in styles:
                data = generate_reasoning(ctx, rtype)
                data["instrument_code"] = ctx["code_number"]
                data["style"] = style
                results.append(data)
                time.sleep(2)

        out_path = OUT_DIR / f"{ctx['code_number']}_synthetic.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("Generated", len(results), "for", ctx["code_number"])

if __name__ == "__main__":
    main()
