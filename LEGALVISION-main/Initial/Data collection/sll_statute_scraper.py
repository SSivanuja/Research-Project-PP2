import argparse
import csv
import os
import re
import time
import json
import hashlib
import tldextract
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as html2md
from slugify import slugify
from urllib import robotparser


USER_AGENT = "SriLankaLaw-Statute-Scraper/1.0 (+research use)"
PDF_HINT = re.compile(r"\.pdf($|\?)", re.I)
SLUG_HINT = "registration-of-documents-ordinance"

MAIN_SELECTORS = [
    "div.item-page",             # common on Joomla sites
    "div#content",               # generic fallback
    "article",                   # semantic fallback
    "div[itemprop='articleBody']",
    "div[itemprop='articleBody'] div",
]

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def same_registered_domain(a: str, b: str) -> bool:
    ea = tldextract.extract(a)
    eb = tldextract.extract(b)
    return (ea.registered_domain and eb.registered_domain and
            ea.registered_domain == eb.registered_domain)

def normalize_url(base: str, link: str) -> str:
    if not link:
        return ""
    u = urljoin(base, link)
    u = urldefrag(u)[0]
    return u

def is_allowed_by_robots(url: str, session: requests.Session) -> bool:
    parsed = urlparse(url)
    root = f"{parsed.scheme}://{parsed.netloc}"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(urljoin(root, "/robots.txt"))
        rp.read()
        return rp.can_fetch(session.headers.get("User-Agent", "*"), url)
    except Exception:
        return True

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def clean_text(html: str) -> str:
    md = html2md(html, heading_style="ATX", strip=["script","style"])
    lines = [ln.rstrip() for ln in md.splitlines()]
    return "\n".join(lines).strip()

def extract_main(soup: BeautifulSoup):
    for sel in MAIN_SELECTORS:
        node = soup.select_one(sel)
        if node and node.get_text(strip=True):
            return node
    candidates = soup.find_all(["div","article"], recursive=True)
    best = None
    best_len = 0
    for c in candidates:
        t = c.get_text(" ", strip=True)
        if len(t) > best_len:
            best = c
            best_len = len(t)
    return best

def looks_like_child_of_statute(url: str, base_path: str) -> bool:
    """
    Only follow pages that:
      - are within the same base path (volume folder) and
      - contain our statute slug in path.
    """
    p = urlparse(url)
    return (base_path in p.path) and (SLUG_HINT in p.path)


def scrape_statute(start_url: str, out_dir: Path, delay: float, depth: int, timeout: int):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    if not same_registered_domain(start_url, "https://www.srilankalaw.lk/"):
        raise ValueError("Please pass a SriLankaLaw URL.")

    if not is_allowed_by_robots(start_url, session):
        raise RuntimeError("Blocked by robots.txt for start URL.")

    sp = urlparse(start_url).path
    parts = sp.strip("/").split("/")
    base_path = "/" + "/".join(parts[:2]) + "/" if len(parts) >= 2 else "/"

    files_dir = out_dir / "files"
    html_dir  = out_dir / "html"
    text_dir  = out_dir / "text"
    json_dir  = out_dir / "json"
    for p in [files_dir, html_dir, text_dir, json_dir]:
        ensure_dir(p)

    meta_csv = out_dir / "metadata.csv"
    meta_exists = meta_csv.exists()
    meta_fp = meta_csv.open("a", newline="", encoding="utf-8")
    meta = csv.writer(meta_fp)
    if not meta_exists:
        meta.writerow(["url","status","content_type","saved_html","saved_text","saved_json","saved_pdf","title","sha256","bytes"])

    visited = set()
    frontier = [(start_url, 0)]
    saved_count = 0

    try:
        while frontier:
            url, d = frontier.pop(0)
            if url in visited:
                continue
            visited.add(url)

            if not is_allowed_by_robots(url, session):
                continue

            try:
                r = session.get(url, timeout=timeout, allow_redirects=True)
            except Exception:
                continue

            ctype = (r.headers.get("Content-Type") or "").lower()
            final_url = r.url

            time.sleep(delay)

            if PDF_HINT.search(final_url) or "application/pdf" in ctype:
                fn = slugify(os.path.basename(urlparse(final_url).path) or "document") + ".pdf"
                dest = files_dir / fn
                content = r.content
                dest.write_bytes(content)
                meta.writerow([url, r.status_code, ctype, "", "", "", str(dest), "", sha256_bytes(content), len(content)])
                meta_fp.flush()
                saved_count += 1
                continue

            is_html = "text/html" in ctype or (r.text.strip().lower().startswith("<!doctype html"))
            if not is_html:
                continue

            soup = BeautifulSoup(r.text, "lxml")

            title = soup.find("h1")
            page_title = title.get_text(" ", strip=True) if title else (soup.title.get_text(" ", strip=True) if soup.title else "")

            pdf_link = None
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full = normalize_url(final_url, href)
                if PDF_HINT.search(full):
                    pdf_link = full
                    break

            main = extract_main(soup)
            saved_html = saved_text = saved_json = saved_pdf = ""
            if main:
                html_name = slugify(page_title or os.path.basename(urlparse(final_url).path) or "page") + ".html"
                html_path = html_dir / html_name
                html_path.write_text(str(main), encoding="utf-8", errors="ignore")
                saved_html = str(html_path)

                text_name = html_name.replace(".html", ".md")
                text_path = text_dir / text_name
                md = clean_text(str(main))
                text_path.write_text(md, encoding="utf-8", errors="ignore")
                saved_text = str(text_path)

                data = {
                    "url": final_url,
                    "title": page_title,
                    "headings": [h.get_text(" ", strip=True) for h in main.find_all(re.compile("^h[1-6]$"))],
                    "text": md,
                }
                json_name = html_name.replace(".html", ".json")
                json_path = json_dir / json_name
                json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                saved_json = str(json_path)

            if pdf_link:
                try:
                    pr = session.get(pdf_link, timeout=timeout)
                    if pr.status_code == 200 and ("application/pdf" in (pr.headers.get("Content-Type") or "").lower() or PDF_HINT.search(pdf_link)):
                        pdf_fn = slugify(os.path.basename(urlparse(pdf_link).path) or "statute") + ".pdf"
                        pdf_path = files_dir / pdf_fn
                        pdf_path.write_bytes(pr.content)
                        saved_pdf = str(pdf_path)
                        saved_count += 1
                        time.sleep(delay)
                except Exception:
                    pass

            body = r.content or b""
            meta.writerow([
                url, r.status_code, ctype, saved_html, saved_text, saved_json, saved_pdf,
                page_title, sha256_bytes(body), len(body)
            ])
            meta_fp.flush()

            if d < depth:
                for a in soup.find_all("a", href=True):
                    nxt = normalize_url(final_url, a["href"])
                    if not nxt or nxt in visited:
                        continue
                    if not same_registered_domain(nxt, start_url):
                        continue
                    if looks_like_child_of_statute(nxt, base_path):
                        frontier.append((nxt, d + 1))

        print(f"[DONE] Saved pages/files: {saved_count}. See:\n- HTML: {html_dir}\n- Text: {text_dir}\n- JSON: {json_dir}\n- Files: {files_dir}\n- Metadata: {meta_csv}")
    finally:
        try:
            meta_fp.close()
        except Exception:
            pass

def parse_args():
    ap = argparse.ArgumentParser(description="SriLankaLaw statute scraper (focused on one statute + subpages)")
    ap.add_argument("--url", required=True, help="Start URL for the statute (e.g., the Registration of Documents Ordinance page).")
    ap.add_argument("--out", default="./data/sll_statutes/registration_of_documents", help="Output directory.")
    ap.add_argument("--delay", type=float, default=1.5, help="Delay between requests (sec).")
    ap.add_argument("--depth", type=int, default=2, help="How deep to follow child links under the same statute.")
    ap.add_argument("--timeout", type=int, default=45, help="HTTP timeout (sec).")
    return ap.parse_args()

if __name__ == "__main__":
    args = parse_args()
    out_dir = Path(args.out); ensure_dir(out_dir)
    scrape_statute(args.url, out_dir, args.delay, args.depth, args.timeout)


# Example usage:

# python .\sll_statute_scraper.py `
#   --url "https://www.srilankalaw.lk/revised-statutes/volume-vii/1013-registration-of-documents-ordinance.html" `
#   --out ".\data\sll_statutes\registration_of_documents" `
#   --delay 1.5 `
#   --depth 2 `
#   --timeout 45
