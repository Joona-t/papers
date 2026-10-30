#!/usr/bin/env python3
"""Online check of data/papers.json: arXiv titles match arXiv, every other link answers 2xx/3xx.

Run by hand when adding papers (the page itself never touches the network):
  python3 -I scripts/check_links.py
"""
import html, json, pathlib, re, sys, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data/papers.json").read_text(encoding="utf-8"))
UA = {"User-Agent": "lovespark-papers-linkcheck/1.0 (+https://lovespark.love/papers/)"}

def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.replace("$\\pi_0$", "π0").lower().replace("π", "pi")).strip()

def get(url, method="GET", tries=4):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read() if method == "GET" else b""
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == tries - 1: raise
            time.sleep(15 * (n + 1))   # arXiv asks for backoff on 429

papers = DATA["papers"]
fails = 0
arxiv = {re.search(r"arxiv\.org/abs/([\d.]+)", p["url"]).group(1): p for p in papers if "arxiv.org/abs/" in p["url"]}
for aid, p in list(arxiv.items()):
    # abstract pages carry the title in a citation_title meta tag; the export API rate-limits hard
    _, body = get(f"https://arxiv.org/abs/{aid}")
    m = re.search(r'<meta name="citation_title" content="([^"]*)"', body.decode("utf-8", "replace"))
    title = html.unescape(m.group(1)) if m else ""
    same = norm(title) == norm(p["title"])
    fails += not same; arxiv.pop(aid)
    print(("ok   " if same else "DIFF ") + f"{aid}  {title}" + ("" if same else f"\n      ours: {p['title']}"))
    time.sleep(1.5)
for aid in arxiv:
    fails += 1; print(f"MISSING {aid} (not returned by arXiv)")

others = [(p["id"], p["url"]) for p in papers if "arxiv.org/abs/" not in p["url"]]
others += [(p["id"], a["url"]) for p in papers for a in p.get("also", [])]
class NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a): return None
for pid, url in others:
    try:
        if "doi.org/" in url:   # publishers (MIT Press) block scripts; a DOI that resolves is enough
            try: urllib.request.build_opener(NoFollow).open(urllib.request.Request(url, headers=UA), timeout=30); status = 200
            except urllib.error.HTTPError as e:
                if not 300 <= e.code < 400: raise
                status = f"{e.code} -> {e.headers['Location']}"
        else:
            status, _ = get(url)
        print(f"ok   {status} {pid}  {url}")
    except Exception as e:   # doi.org publishers sometimes refuse bots; report, don't hide
        fails += 1; print(f"FAIL {pid}  {url}  ({e})")
print(f"\n{len(papers)} papers, {fails} problem(s)")
sys.exit(1 if fails else 0)
