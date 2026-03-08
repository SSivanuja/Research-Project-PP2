# validate_and_summarize.py
import json, pathlib, csv
IN_DIR = pathlib.Path("./data/structured")
OUT_CSV = IN_DIR/"summary.csv"

required = ["type","code_number","date"]
rows = []
bad = []

for p in sorted(IN_DIR.glob("DEED_*.json")):
    d = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    miss = [k for k in required if not d.get(k)]
    rows.append({
        "file": p.name,
        "type": d.get("type"),
        "code": d.get("code_number"),
        "date": d.get("date"),
        "jurisdiction": d.get("jurisdiction"),
        "registry": d.get("registry_office"),
        "plan_no": d.get("plan",{}).get("plan_no"),
        "lot": d.get("property",{}).get("lot"),
        "extent_perches": d.get("property",{}).get("extent_perches"),
        "prior_reg": d.get("prior_registration"),
        "fields_found": ",".join(d.get("source",{}).get("fields_found",[]))
    })
    if miss: bad.append((p.name, miss))

with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)

print(f"Summary → {OUT_CSV}")
if bad:
    print("Missing required fields in:")
    for name, miss in bad:
        print("  ", name, "->", miss)
