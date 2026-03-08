import argparse
import csv
import hashlib
import os
import queue
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from slugify import slugify
import tldextract
from urllib import robotparser

# Default property-law keywords
PROPERTY_KEYWORDS = [
    # general
    "property", "immovable", "movable", "land", "lands", "estate", "title", "ownership",
    "boundary", "parcel", "allotment", "plan", "lot", "survey", "resurvey", "deed", "deeds",
    "mortgage", "lease", "encumbrance", "transfer", "sale", "gift", "will", "succession",
    "prescription", "adverse", "easement", "servitude", "trust", "notary", "notaries",
    "registration", "registrar", "partition", "condominium",
    # Sri Lanka specific acts/ordinances (common ones—extend as needed)
    "registration of documents ordinance",
    "notaries ordinance",
    "state lands ordinance",
    "land development ordinance",
    "prescription ordinance",
    "partition law",
    "trusts ordinance",
    "condominium property act",
    "title registration act",
    "lands (special provisions)",
]

DOC_EXT_RE = re.compile(r"\.(pdf|docx?|rtf)$", re.I)


def sha256_of_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def normalize_url(base: str, link: str) -> str:
    if not link:
        return ""
    link = urldefrag(link)[0]  
    return urljoin(base, link)

def same_registered_domain(a: str, b: str) -> bool:
    ea = tldextract.extract(a)
    eb = tldextract.extract(b)
    return (ea.registered_domain and eb.registered_domain and
            ea.registered_domain == eb.registered_domain)

def is_allowed_by_robots(robots_parsers, url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    rp = robots_parsers.get(root)
    if not rp:
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(urljoin(root, "/robots.txt"))
            rp.read()
        except Exception:
            pass
        robots_parsers[root] = rp
    try:
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

def text_matches_keywords(text: str, keywords) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)

def filename_from_url(url: str) -> str:
    name = os.path.basename(urlparse(url).path) or "index"
    return slugify(name, lowercase=False)

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def crawl(seeds, allow_domains, out_dir: Path, max_pages: int, delay: float, timeout: int, keywords):
    out_dir_files = out_dir / "files"
    ensure_dir(out_dir_files)
    meta_path = out_dir / "metadata.csv"
    visited = set()
    q = queue.Queue()

    allow_domains = set(d.strip().lower() for d in allow_domains if d.strip())
    for s in seeds:
        q.put(s)

    meta_file_exists = meta_path.exists()
    meta_fp = meta_path.open("a", newline="", encoding="utf-8")
    meta_writer = csv.writer(meta_fp)
    if not meta_file_exists:
        meta_writer.writerow([
            "fetched_at","url","final_url","status","content_type","saved_to",
            "sha256","bytes","title","source_text_snippet"
        ])

    session = requests.Session()
    session.headers.update({
        "User-Agent": "SriLanka-PropertyLaw-Crawler/1.0 (+research use; contact: your-email@example.com)"
    })

    robots_cache = {}
    pages_crawled = 0

    try:
        while not q.empty() and pages_crawled < max_pages:
            url = q.get()
            if url in visited:
                continue
            visited.add(url)

            host = urlparse(url).netloc.lower()
            if not any(host.endswith(ad) or same_registered_domain(url, "https://" + ad) for ad in allow_domains):
                continue

            if not is_allowed_by_robots(robots_cache, url, session.headers["User-Agent"]):
                continue

            try:
                r = session.get(url, timeout=timeout, allow_redirects=True)
            except Exception:
                continue

            pages_crawled += 1
            time.sleep(delay)

            ctype = r.headers.get("Content-Type","").lower()
            final_url = r.url

            if DOC_EXT_RE.search(final_url) or any(ft in ctype for ft in ["application/pdf","msword","officedocument"]):
                content = r.content
                sha = sha256_of_bytes(content)
                fn_guess = filename_from_url(final_url)
                if not DOC_EXT_RE.search(fn_guess):
                    if "pdf" in ctype:
                        fn_guess += ".pdf"
                    elif "word" in ctype or "officedocument" in ctype:
                        if "officedocument.wordprocessingml" in ctype:
                            fn_guess += ".docx"
                        else:
                            fn_guess += ".doc"
                    else:
                        fn_guess += ".bin"
                dest = out_dir_files / fn_guess
                if dest.exists():
                    dest = out_dir_files / f"{sha[:10]}_{fn_guess}"
                dest.write_bytes(content)

                meta_writer.writerow([
                    datetime.utcnow().isoformat()+"Z", url, final_url, r.status_code,
                    ctype, str(dest), sha, len(content), "", ""
                ])
                meta_fp.flush()
                continue

            is_html = "text/html" in ctype or r.text.strip().lower().startswith("<!doctype html")
            title_text = ""
            snippet = ""
            if is_html:
                soup = BeautifulSoup(r.text, "html.parser")
                title = soup.find("title")
                title_text = (title.get_text(strip=True) if title else "")[:200]
                body_text = soup.get_text(" ", strip=True)[:1000]
                snippet = body_text[:300]

                if text_matches_keywords(final_url, keywords) or text_matches_keywords(body_text, keywords):
                    meta_writer.writerow([
                        datetime.utcnow().isoformat()+"Z", url, final_url, r.status_code,
                        ctype, "", "", len(r.content), title_text, snippet
                    ])
                    meta_fp.flush()

                for a in soup.find_all("a", href=True):
                    nxt = normalize_url(final_url, a["href"])
                    if not nxt or nxt in visited:
                        continue
                    nxt_host = urlparse(nxt).netloc.lower()
                    if not any(nxt_host.endswith(ad) or same_registered_domain(nxt, "https://" + ad) for ad in allow_domains):
                        continue
                    anchor_text = a.get_text(" ", strip=True)
                    if (DOC_EXT_RE.search(nxt) or
                        text_matches_keywords(nxt, keywords) or
                        text_matches_keywords(anchor_text, keywords)):
                        q.put(nxt)
            else:
                # Non-HTML non-doc content: skip
                pass

        print(f"[DONE] Crawled {pages_crawled} pages. Metadata → {meta_path}")
    finally:
        meta_fp.close()


def parse_args():
    ap = argparse.ArgumentParser(description="Sri Lanka property-law document crawler")
    ap.add_argument("--seeds", type=str, required=False, default="",
                    help="Comma-separated seed URLs to start from.")
    ap.add_argument("--allow", type=str, required=False, default="",
                    help="Comma-separated allowed domains (e.g., parliament.lk,documents.gov.lk).")
    ap.add_argument("--out", type=str, default="./data/raw_laws", help="Output directory.")
    ap.add_argument("--max-pages", type=int, default=600, help="Max pages to fetch (HTML or files).")
    ap.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds).")
    ap.add_argument("--timeout", type=int, default=40, help="HTTP timeout seconds.")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    seeds = [s.strip() for s in args.seeds.split(",") if s.strip()]
    allow = [d.strip() for d in args.allow.split(",") if d.strip()]
    if not seeds or not allow:
        print("Tip: provide --seeds and --allow.\n"
              "Example:\n"
              "  --seeds \"https://www.parliament.lk/,https://www.documents.gov.lk/\" "
              "--allow \"parliament.lk,documents.gov.lk\"\n",
              file=sys.stderr)
    out_dir = Path(args.out)
    ensure_dir(out_dir)
    crawl(seeds, allow, out_dir, args.max_pages, args.delay, args.timeout, PROPERTY_KEYWORDS)


# to run
# python .\sri_lanka_property_law_crawler.py --seeds "https://www.parliament.lk/,https://www.documents.gov.lk/" --allow "parliament.lk,documents.gov.lk" --out .\data\raw_laws --max-pages 800 --delay 1.5

