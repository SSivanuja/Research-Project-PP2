import os, json, pathlib
from neo4j import GraphDatabase

OUT = pathlib.Path("./reasoning/contexts"); OUT.mkdir(parents=True, exist_ok=True)

URI  = os.getenv("NEO4J_URI",  "neo4j+s://0c4fa62b.databases.neo4j.io")
USER = os.getenv("NEO4J_USER", "neo4j")
PASS = os.getenv("NEO4J_PASS", "hWoQt_bXs83DqDLnV3kAPVa1eyeic7FcBLvvWcMtFZk")

Q = """
MATCH (i:Instrument {code_number:$code})
OPTIONAL MATCH (i)-[:REGISTERED_AT]->(r:RegistryOffice)
OPTIONAL MATCH (i)-[:UNDER_JURISDICTION]->(j:Jurisdiction)
OPTIONAL MATCH (i)-[:CONVEYS]->(pp:PropertyParcel)-[:DEFINED_BY]->(pl:Plan)
OPTIONAL MATCH (p:Person)-[hr:HAS_ROLE]->(i)
OPTIONAL MATCH (i)-[:REFERS_TO]->(pr:PriorInstrument)
WITH i, r, j, pp, pl, pr,
     collect({name:p.name, role:hr.role}) AS parties
RETURN {
  code_number: i.code_number,
  type: i.type,
  date: i.date,
  registry: r.name,
  jurisdiction: j.name,
  parties: parties,
  plan: {plan_no: pl.plan_no, plan_date: pl.plan_date},
  parcel: {
    lot: pp.lot,
    extent_perches: pp.extent_perches,
    boundaryN: pp.boundaryN, boundaryE: pp.boundaryE,
    boundaryS: pp.boundaryS, boundaryW: pp.boundaryW
  },
  prior_registration: pr.ref
} AS ctx
"""

def save_context(sess, code):
    rec = sess.run(Q, code=code).single()
    if not rec:
        print("No record for", code); return
    ctx = rec["ctx"]
    path = OUT / f"{code}.json"
    path.write_text(json.dumps(ctx, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Saved", path)

def main():
    # I have choosen a few codes to start; but I can also fetch all:
    # codes = [r["code"] for r in sess.run("MATCH (i:Instrument) RETURN i.code_number AS code")]
    codes = ["UNKNOWN-1","UNKNOWN-2","UNKNOWN-5","UNKNOWN-15"]  # only chosen few for demo
    driver = GraphDatabase.driver(URI, auth=(USER, PASS))
    with driver.session() as sess:
        for c in codes: save_context(sess, c)

if __name__ == "__main__":
    main()
