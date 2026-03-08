import os, json
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a Sri Lankan property law reasoning assistant.
Given structured deed facts, perform stepwise legal reasoning (3-5 steps)
and end with a clear conclusion. Cite data fields in [brackets]."""

def run_reasoning(context_path):
    ctx = json.loads(open(context_path, encoding="utf-8").read())

    user_prompt = f"""
FACTS:
{json.dumps(ctx, indent=2)}

TASK:
Assess the title validity, prior registration, and plan-lot consistency.
Return valid JSON with:
{{
  "steps": [...],
  "conclusion": "...",
  "citations": [...]
}}
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4,
    )

    result = completion.choices[0].message.content
    print("\n--- LLaMA 3.1 Reasoning Output ---\n")
    print(result)

if __name__ == "__main__":
    run_reasoning("./reasoning/contexts/UNKNOWN-5.json")
