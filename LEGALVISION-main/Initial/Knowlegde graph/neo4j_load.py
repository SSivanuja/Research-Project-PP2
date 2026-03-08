import os, json, pathlib
from dotenv import load_dotenv
load_dotenv()
from neo4j import GraphDatabase

JSON_DIR = pathlib.Path("./data/structured")
NEO4J_URI = os.getenv("NEO4J_URI","neo4j+s://0c4fa62b.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER","neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS","hWoQt_bXs83DqDLnV3kAPVa1eyeic7FcBLvvWcMtFZk")

def merge_instrument(tx, d):
    q = """
    WITH $code AS code, $type AS type, $date AS date,
         $registry AS registry, $jurisdiction AS jurisdiction,
         $plan_no AS plan_no, $plan_date AS plan_date,
         $lot AS lot, $extent AS extent

    MERGE (i:Instrument {code_number:code})
      ON CREATE SET i.type=type, i.date=date
      ON MATCH  SET i.type=type, i.date=date

    FOREACH (_ IN CASE WHEN registry IS NULL THEN [] ELSE [1] END |
      MERGE (r:RegistryOffice {name:registry})
      MERGE (i)-[:REGISTERED_AT]->(r))

    FOREACH (_ IN CASE WHEN jurisdiction IS NULL THEN [] ELSE [1] END |
      MERGE (j:Jurisdiction {name:jurisdiction})
      MERGE (i)-[:UNDER_JURISDICTION]->(j))

    // Create Plan if present
    FOREACH (_ IN CASE WHEN plan_no IS NULL THEN [] ELSE [1] END |
      MERGE (pl:Plan {plan_no:plan_no})
      SET pl.plan_date = plan_date
      MERGE (i)-[:REFERENCES_PLAN]->(pl)

      // Create Parcel only if BOTH plan_no and lot exist
      FOREACH (__ IN CASE WHEN lot IS NULL THEN [] ELSE [1] END |
        MERGE (pp:PropertyParcel {lot:lot, plan_no:plan_no})
        SET pp.extent_perches = extent
        MERGE (pp)-[:DEFINED_BY]->(pl)
        MERGE (i)-[:CONVEYS]->(pp)
      )
    )

    RETURN i.code_number AS code
    """
    tx.run(
        q,
        code=d["code_number"],
        type=d["type"],
        date=d.get("date"),
        registry=d.get("registry_office"),
        jurisdiction=d.get("jurisdiction"),
        plan_no=d.get("plan", {}).get("plan_no"),
        plan_date=d.get("plan", {}).get("plan_date"),
        lot=d.get("property", {}).get("lot"),
        extent=d.get("property", {}).get("extent_perches"),
    )


def merge_boundaries(tx, d):
    b = d.get("property",{}).get("boundaries",{}) or {}
    if not b: return
    q = """
    MATCH (i:Instrument {code_number:$code})-[:CONVEYS]->(pp:PropertyParcel)
    SET pp.boundaryN=$N, pp.boundaryE=$E, pp.boundaryS=$S, pp.boundaryW=$W
    """
    tx.run(q, code=d["code_number"], N=b.get("N"), E=b.get("E"), S=b.get("S"), W=b.get("W"))

def merge_parties(tx, d):
    parties = []
    if d["type"] == "sale_transfer":
        for role, names in [("VENDOR", d.get("vendor",{}).get("names",[])),
                            ("VENDEE", d.get("vendee",{}).get("names",[]))]:
            for nm in names:
                parties.append((role, nm))
    elif d["type"] == "gift":
        for role, names in [("DONOR", d.get("donor",{}).get("names",[])),
                            ("DONEE", d.get("donee",{}).get("names",[]))]:
            for nm in names:
                parties.append((role, nm))
    elif d["type"] == "will":
        for nm in d.get("testator",{}).get("names",[]):
            parties.append(("TESTATOR", nm))
        for ex in d.get("executors",[]):
            nm = ex.get("name")
            if nm: parties.append(("EXECUTOR", nm))

    if not parties: return
    q = """
    MATCH (i:Instrument {code_number:$code})
    UNWIND $rows AS row
    MERGE (p:Person {name:row.name})
    MERGE (p)-[:HAS_ROLE {role:row.role}]->(i)
    """
    tx.run(q, code=d["code_number"], rows=[{"role":r, "name":n} for r,n in parties])

def merge_prior_reg(tx, d):
    pr = d.get("prior_registration")
    if not pr: return
    q = """
    MATCH (i:Instrument {code_number:$code})
    MERGE (p:PriorInstrument {ref:$ref})
    MERGE (i)-[:REFERS_TO]->(p)
    """
    tx.run(q, code=d["code_number"], ref=pr)


def load_all():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    files = sorted(JSON_DIR.glob("DEED_*.json"))
    if not files:
        raise SystemExit(f"No files found in {JSON_DIR}")

    print(f"Found {len(files)} JSON files in {JSON_DIR}")
    with driver, driver.session() as sess:
        for fp in files:
            try:
                raw = fp.read_text(encoding="utf-8", errors="strict")
                d = json.loads(raw)
            except UnicodeDecodeError as e:
                print(f"[ENCODING] {fp.name}: {e}. Retrying with errors='replace'…")
                raw = fp.read_text(encoding="utf-8", errors="replace")
                d = json.loads(raw)
            except json.JSONDecodeError as e:
                print(f"[JSON] {fp.name}: {e}. Skipping this file.")
                continue

            sess.execute_write(merge_instrument, d)
            sess.execute_write(merge_boundaries, d)
            sess.execute_write(merge_parties, d)
            sess.execute_write(merge_prior_reg, d)
            print(f"Loaded {fp.name}  {d.get('type')}  {d.get('code_number')}")

    print("Done.")

if __name__ == "__main__":
    load_all()
