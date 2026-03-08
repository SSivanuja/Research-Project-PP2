import json, pathlib, random

CTX_DIR = pathlib.Path("./reasoning/contexts")
OUT_TRAIN = pathlib.Path("./reasoning/dataset/train.jsonl")
OUT_EVAL  = pathlib.Path("./reasoning/dataset/eval.jsonl")
OUT_TRAIN.parent.mkdir(parents=True, exist_ok=True)

def mk_example(ctx):
    # Minimal Q/A pair using the context facts
    q = f"Is the transfer in instrument {ctx['code_number']} valid and properly described?"
    # For init demo, create a templated target you can refine later:
    cited = []
    if ctx.get("prior_registration"): cited.append("[prior_registration]")
    if ctx.get("plan",{}).get("plan_no"): cited.append("[plan_no]")
    if ctx.get("parcel",{}).get("lot"): cited.append("[lot]")
    cited = " ".join(cited) if cited else "[no_citations_found]"

    a = (
      "1) Parties and roles identified from provided facts.\n"
      "2) Prior registration traced where available.\n"
      "3) Plan number and lot matched to parcel; boundaries/extent noted.\n"
      "4) Registry and jurisdiction reviewed for consistency.\n"
      f"Conclusion: Preliminary title appears {'plausible' if cited!='[no_citations_found]' else 'incomplete'} based on the cited facts. Cites: {cited}"
    )
    return {
        "instrument_code": ctx["code_number"],
        "question": q,
        "facts": ctx,             # full context goes here
        "answer_ref": a,          # reference answer (for now templated)
        "citations": cited.split(),
        "type": ctx["type"]
    }

def main():
    ctx_files = sorted(CTX_DIR.glob("*.json"))
    data = []
    for fp in ctx_files:
        ctx = json.loads(fp.read_text(encoding="utf-8"))
        # 2 examples per context to start
        data.append(mk_example(ctx))
        data.append(mk_example(ctx))
    random.shuffle(data)
    cut = max(1, int(0.8*len(data)))
    with OUT_TRAIN.open("w", encoding="utf-8") as f:
        for row in data[:cut]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with OUT_EVAL.open("w", encoding="utf-8") as f:
        for row in data[cut:]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(data[:cut])} train and {len(data[cut:])} eval examples.")

if __name__ == "__main__":
    main()
