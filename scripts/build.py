#!/usr/bin/env python3
"""Build index.html from data/papers.json (the source of truth).

Each field is a timeline; each paper is one entry: year, title (links to the full paper),
main finding, and "Led to" / "Built on" links to the papers around it.
Run: python3 scripts/build.py          (writes index.html)
     python3 scripts/build.py --check  (exit 1 if index.html is stale)
"""
import base64, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
T = ROOT / "template"
esc = lambda s: html.escape(s, quote=True)

THEMES = [("basalt", "Basalt", "#16171a", "#d9a23b"), ("bubblegum", "Bubblegum", "#fbf3f5", "#a52f66"), ("retro", "Retro Pink", "#fdeef4", "#b8175a"),
          ("noir", "Dark Noir", "#17131b", "#f09cc4"), ("beige", "Beige Paper", "#f3eee4", "#9c4a2b")]
FONTS = [("serif", "Serif", "font-family:var(--serif)"), ("sans", "Sans", "font-family:var(--sans)"),
         ("dyslexic", "OpenDyslexic", "font-family:var(--dys)"),
         ("lexend", "Lexend", "font-family:Lexend,sans-serif"), ("comfortaa", "Comfortaa", "font-family:Comfortaa,sans-serif"),
         ("atkinson", "Atkinson Hyperlegible", "font-family:'Atkinson Hyperlegible',sans-serif")]
# S. Keshav, "How to Read a Paper", ACM SIGCOMM CCR 37(3), 2007 (doi 10.1145/1273445.1273458)
PASSES = [("First pass: the shape", "Title, abstract, introduction, headings, conclusion. Five to ten minutes tells you what it claims and whether to go on."),
          ("Second pass: the content", "Read it properly, with care over the figures and graphs. Skip the proofs. Note what you don't follow."),
          ("Third pass: rebuild it", "Re-create the work in your head, or in code, from the same assumptions. This is where you find what it got wrong.")]
# Korean themes: the four Korean popup themes of the LoveSpark Retro Cursor extension
# (themes/lovespark-retro-cursor/popup.css): same palettes and backgrounds, mapped onto this page's tokens.
# "stops" are the colours text can sit on (background gradient stops, card fills); the build checks them all.
KOREAN = [
    ("seoul", "Seoul Y2K", "서울", dict(
        paper="#fdf9ff", deep="#ffe8f2", wash="#e9dcff", ink="#3a2a3a", soft="#4e3a50", muted="#6b4a66",
        line="#ecd6ec", strong="#c4a8e0", accent="#a8134f", swatch="#ff5baa",
        bg="linear-gradient(160deg, #dff1ff 0%, #ffe8f2 45%, #fff4d6 78%, #e9dcff 100%)",
        stops=["#dff1ff", "#ffe8f2", "#fff4d6", "#e9dcff"],
        extra="""{t} .entry-card, {t} .plaque, {t} .toc-group {{ border-radius: 10px; border-color: #c4a8e0; box-shadow: 3px 3px 0 #c4a8e0; }}
{t} .entry-card:hover, {t} .entry-card:focus-within {{ box-shadow: 4px 4px 0 #ff8fc6; }}
{t} .entry-rel a, {t} .button {{ border-radius: 6px; }}""")),
    ("gingham", "Gingham Sticker", "깅엄", dict(
        paper="#fffafc", deep="#ffe3ee", wash="#fff3f7", ink="#2a1824", soft="#3e2434", muted="#6e3a57",
        line="#f0c3d5", strong="#2a1824", accent="#b0124f", swatch="#f6a6c4",
        bg="linear-gradient(180deg, #fff3f7 0%, #fff3f7 100%)",
        stops=["#fff3f7", "#fffafc"],
        # the gingham itself stays off the reading area (text never sits on a pattern): a fixed top band and the footer
        extra="""{t} body::before {{ content: ""; position: fixed; inset: 0 0 auto 0; height: 10px; z-index: 30; pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(246,166,196,.6) 0 5px, transparent 5px 10px), repeating-linear-gradient(90deg, rgba(246,166,196,.6) 0 5px, transparent 5px 10px), #fff3f7; }}
{t} footer {{ background: repeating-linear-gradient(0deg, rgba(246,166,196,.42) 0 9px, transparent 9px 18px), repeating-linear-gradient(90deg, rgba(246,166,196,.42) 0 9px, transparent 9px 18px), #fff3f7; }}
{t} footer .foot-inner {{ background: #fffafc; border: 2px solid #2a1824; box-shadow: 3px 3px 0 #2a1824; border-radius: 14px; }}
{t} .entry-card, {t} .plaque, {t} .toc-group.current {{ background: #fffafc; border: 2px solid #2a1824; border-radius: 14px; box-shadow: 3px 3px 0 #2a1824; }}
{t} .entry-card:hover, {t} .entry-card:focus-within {{ box-shadow: 4px 4px 0 #ff4f9a; border-color: #2a1824; }}
{t} .entry-rel a {{ border: 2px solid #2a1824; border-radius: 10px; box-shadow: 2px 2px 0 #2a1824; }}""")),
    ("holo", "Holo Mochi", "모찌", dict(
        paper="#faf7ff", deep="#f3ebff", wash="#e9d5ff", ink="#2b1b4a", soft="#3d2c63", muted="#54447a",
        line="#e3d6f7", strong="#c7b2ee", accent="#6d35d8", swatch="#9b6cf0",
        bg="radial-gradient(60% 45% at 12% 8%, #ffd1ea 0%, transparent 70%), radial-gradient(55% 40% at 92% 18%, #cfe6ff 0%, transparent 70%), radial-gradient(60% 50% at 80% 88%, #c8f7e1 0%, transparent 72%), radial-gradient(55% 45% at 10% 80%, #ffd8c2 0%, transparent 70%), linear-gradient(#efe4ff, #efe4ff)",
        stops=["#ffd1ea", "#cfe6ff", "#c8f7e1", "#ffd8c2", "#efe4ff"],
        extra="""{t} body {{ background-attachment: fixed; }}
{t} .entry-card, {t} .plaque, {t} .toc-group {{ background: rgba(255,255,255,.62); border-color: rgba(255,255,255,.9); border-radius: 22px; box-shadow: 0 10px 28px rgba(140,100,230,.18), 0 2px 6px rgba(255,180,220,.3); }}
{t} .entry-card:hover, {t} .entry-card:focus-within {{ background: rgba(250,247,255,.92); border-color: #9b6cf0; box-shadow: 0 14px 36px rgba(140,100,230,.3); }}
{t} .entry-rel a, {t} .button {{ border-radius: 14px; }}""")),
    ("neon", "Neon Usagi", "네온", dict(
        paper="#120b18", deep="#1e1030", wash="#2a1740", ink="#f3eaf2", soft="#e4d5ea", muted="#c9b3dc",
        line="#2e1a40", strong="#7d2a8e", accent="#ff46d6", on="#120b18", swatch="#ff46d6", dark=True,
        bg="radial-gradient(80% 50% at 50% -10%, rgba(255,70,214,.22) 0%, transparent 70%), radial-gradient(70% 45% at 100% 110%, rgba(110,17,145,.45) 0%, transparent 70%)",
        stops=["#120b18", "#3e1a40", "#3a0f50", "#2a1740"],   # base, top pink glow, bottom violet glow, card fill
        extra="""{t} body {{ background-attachment: fixed; }}
{t} .entry-card, {t} .plaque, {t} .toc-group {{ background: rgba(42,23,64,.88); border-color: rgba(255,70,214,.45); border-radius: 16px; }}
{t} .entry-card:hover, {t} .entry-card:focus-within {{ border-color: #ff46d6; box-shadow: 0 0 0 1px rgba(255,70,214,.55), 0 0 14px rgba(255,70,214,.45), 0 0 34px rgba(255,70,214,.2); }}
{t} .entry::before {{ box-shadow: 0 0 10px rgba(255,70,214,.7); }}
{t} .entry-rel a {{ border-radius: 12px; border-color: rgba(255,70,214,.35); background: #1e1030; }}""")),
]

def _lum(h):
    c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
def contrast(a, b):
    A, B = _lum(a), _lum(b); return (max(A, B) + .05) / (min(A, B) + .05)
def mix(a, b, t):
    return "#" + "".join(f"{round(int(a[i:i+2], 16) * t + int(b[i:i+2], 16) * (1 - t)):02x}" for i in (1, 3, 5))

def korean_css():
    """CSS for the Korean themes; the build fails if any text pair drops below 4.8:1 (the template's floor)."""
    out = "\n/* ---------- Korean themes (generated by scripts/build.py from KOREAN) ---------- */\n"
    for key, name, _, t in KOREAN:
        bgs = [t["paper"], t["deep"], t["wash"], mix(t["deep"], t["paper"], .6)] + t["stops"]
        for fg in ("ink", "soft", "muted", "accent"):
            for col in bgs:
                r = contrast(t[fg], col)
                assert r >= 4.8, f"{name}: {fg} on {col} is {r:.2f}:1, below 4.8"
        on = t.get("on", "#ffffff")
        assert contrast(on, t["accent"]) >= 4.8, f"{name}: text on accent below 4.8"
        sel = f':root[data-theme="kr-{key}"]'
        out += (f'{sel} {{\n  --paper: {t["paper"]}; --paper-deep: {t["deep"]}; --wash: {t["wash"]};\n'
                f'  --ink: {t["ink"]}; --ink-soft: {t["soft"]}; --muted: {t["muted"]};\n  --line: {t["line"]}; --line-strong: {t["strong"]};\n'
                f'  --accent: {t["accent"]}; --on-accent: {on};\n  --ls-bg-gradient: {t["bg"]};\n  color-scheme: {"dark" if t.get("dark") else "light"};\n}}\n'
                + t["extra"].format(t=sel) + "\n")
    return out

# Reading fonts from the same extension (lib/fonts, SIL OFL 1.1), inlined so the page stays offline.
EXTRA_FONTS = [("Lexend", "lexend-400-latin", "300 700", "normal"), ("Comfortaa", "comfortaa-400-latin", "300 700", "normal"),
               ("Atkinson Hyperlegible", "atkinson-hyperlegible-400-normal-latin", "400", "normal"),
               ("Atkinson Hyperlegible", "atkinson-hyperlegible-700-normal-latin", "700", "normal"),
               ("Atkinson Hyperlegible", "atkinson-hyperlegible-400-italic-latin", "400", "italic")]
def extra_fonts_css():
    out = "\n/* ---------- extra reading fonts (generated by scripts/build.py) ---------- */\n"
    for fam, f, w, style in EXTRA_FONTS:
        b64 = base64.b64encode((T / "fonts" / f"{f}.woff2").read_bytes()).decode()
        out += f'@font-face {{ font-family: "{fam}"; src: url(data:font/woff2;base64,{b64}) format("woff2"); font-weight: {w}; font-style: {style}; font-display: swap; }}\n'
    return out + """:root { --lexend: "Lexend", system-ui, sans-serif; --comfortaa: "Comfortaa", "Trebuchet MS", sans-serif; --atkinson: "Atkinson Hyperlegible", "Trebuchet MS", sans-serif; }
:root[data-font="lexend"] { --read: var(--lexend); --display: var(--lexend); }
:root[data-font="comfortaa"] { --read: var(--comfortaa); --display: var(--comfortaa); }
:root[data-font="atkinson"] { --read: var(--atkinson); --display: var(--atkinson); }
"""

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

def source_label(url):
    m = re.search(r"arxiv\.org/abs/([\d.]+)", url)
    if m: return f"arXiv {m.group(1)}"
    if "doi.org/" in url: return "DOI " + url.split("doi.org/", 1)[1]
    if url.endswith(".pdf"): return "PDF"
    return re.sub(r"^https?://(www\.)?([^/]+).*$", r"\2", url)

def rel_links(label, ids, by_id):
    if not ids: return ""
    chips = "".join(f'<a href="#{i}">{esc(by_id[i]["short"])} <span class="rel-year">{by_id[i]["year"]}</span></a>' for i in ids)
    return f'<div class="entry-rel"><span class="rel-label">{label}</span>{chips}</div>'

def entry(p, by_id, built_on):
    kind = f'<span class="entry-kind">{esc(p["kind"])}</span>' if p.get("kind") else ""
    also = "".join(f'<a href="{esc(a["url"])}" target="_blank" rel="noopener">{esc(a["label"])} <span aria-hidden="true">↗</span></a>' for a in p.get("also", []))
    also = f'<div class="entry-rel entry-also"><span class="rel-label">Also read</span>{also}</div>' if also else ""
    return f"""<article class="entry" id="{p["id"]}">
        <div class="entry-year">{p["year"]}</div>
        <div class="entry-card">
          <div class="entry-label">{esc(p["short"])}{kind}</div>
          <h3><a class="entry-link" href="{esc(p["url"])}" target="_blank" rel="noopener">{esc(p["title"])}<span class="sr-only"> (opens the full paper in a new tab)</span></a></h3>
          <p class="entry-finding">{esc(p["finding"])}</p>
          <div class="entry-meta">{esc(p["authors"])} · {esc(p["venue"])} · <span class="entry-src">{esc(source_label(p["url"]))} <span aria-hidden="true">↗</span></span></div>
          {rel_links("Built on", built_on.get(p["id"], []), by_id)}{rel_links("Led to", p["next"], by_id)}{also}
        </div>
      </article>"""

def build():
    data = json.loads((ROOT / "data/papers.json").read_text(encoding="utf-8"))
    papers = data["papers"]
    by_id = {p["id"]: p for p in papers}
    built_on = {}
    for p in papers:
        for n in p["next"]: built_on.setdefault(n, []).append(p["id"])
    fields, toc = [], []
    for k, f in enumerate(data["fields"]):
        items = sorted((p for p in papers if p["field"] == f["id"]), key=lambda p: p["year"])   # stable: same-year order follows the data
        span = f'{items[0]["year"]}–{items[-1]["year"]}'
        fields.append(f"""<section class="field" id="{f["id"]}">
      <p class="kicker"><span class="rule"></span>Field {ROMAN[k]} · {span} · {len(items)} papers</p>
      <h2>{esc(f["name"])}</h2>
      <p class="field-intro">{esc(f["intro"])}</p>
      <div class="timeline">
      {"".join(entry(p, by_id, built_on) for p in items)}
      </div>
    </section>""")
        links = "".join(f'<li><a href="#{p["id"]}">{p["year"]} · {esc(p["short"])}</a></li>' for p in items)
        toc.append(f'<li class="toc-group"><a class="toc-head" href="#{f["id"]}"><span class="toc-num" aria-hidden="true">{ROMAN[k]}</span>'
                   f'<span class="toc-title"><small>{span}</small>{esc(f["name"])}</span></a><ol>{links}</ol></li>')
    toc_items = f'<a class="toc-start" href="#start">How to use this archive</a><ol class="toc-parts">{"".join(toc)}</ol>'
    nav = "".join(f'<a href="#{f["id"]}">{esc(f["nav"])}</a>' for f in data["fields"])
    years = sorted(p["year"] for p in papers)
    count = f'{len(papers)} papers · {len(data["fields"])} fields · {years[0]} to {years[-1]}'
    mascot = (T / "mascot.datauri").read_text(encoding="utf-8").strip()
    ankh = (T / "ankh.datauri").read_text(encoding="utf-8").strip()   # Basalt wordmark, as on lovespark.love
    desc = f"A small archive of AI research papers worth reading, laid out as timelines by field: neural networks, training, language models, vision, robotics and safety. Each entry gives the main finding and links to the full paper. {count}."
    css = (T / "fonts.css").read_text(encoding="utf-8") + extra_fonts_css() + (T / "style.css").read_text(encoding="utf-8") + (T / "timeline.css").read_text(encoding="utf-8") + korean_css()
    themes = "".join(f'<button type="button" role="menuitemradio" aria-checked="false" data-theme="{k}"><span class="swatch" style="background:linear-gradient(135deg,{bg} 50%,{ac} 50%)"></span>{n}</button>' for k, n, bg, ac in THEMES)
    korean = "".join(f'<button type="button" role="menuitemradio" aria-checked="false" data-theme="kr-{k}"><span class="swatch" style="background:linear-gradient(135deg,{t["paper"]} 50%,{t["swatch"]} 50%)"></span>{n}<span class="kr-name" lang="ko">{ko}</span></button>' for k, n, ko, t in KOREAN)
    fonts = "".join(f'<button type="button" role="menuitemradio" aria-checked="false" data-font="{k}"><span class="fontpreview" style="{st}" aria-hidden="true">Aa</span>{n}</button>' for k, n, st in FONTS)
    passes = "".join(f"<li><h3>{esc(t)}</h3><p>{esc(d)}</p></li>" for t, d in PASSES)
    field_links = "".join(f'<a class="text-link" href="#{f["id"]}">{ROMAN[k]} · {esc(f["nav"])} →</a>' for k, f in enumerate(data["fields"]))
    return f"""<!doctype html>
<html lang="en" data-theme="basalt" data-font="serif">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Papers worth reading · a LoveSpark archive</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="Papers worth reading · a LoveSpark archive">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="https://lovespark.love/papers/">
<meta name="theme-color" content="#16171a">
<style>
{css}</style>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<div id="progress" class="progress" aria-hidden="true"></div>

<header class="topbar">
  <a class="wordmark" href="#top" aria-label="Papers worth reading, back to top">
    <img src="{mascot}" alt="Sparky, the LoveSpark wolf mascot">
    <img class="wordmark-ankh" src="{ankh}" alt="" aria-hidden="true">
    <span class="wordmark-text"><span class="wordmark-title">Papers worth reading</span><span class="wordmark-sub">A LoveSpark archive · {esc(data["checked"])}</span></span>
  </a>
  <nav class="topnav" aria-label="Main navigation">
    {nav}
    <div class="appearance">
      <button id="themeBtn" type="button" aria-haspopup="true" aria-expanded="false" aria-controls="themeMenu">Change Font &amp; Theme</button>
      <div id="themeMenu" role="menu" aria-label="Theme and reading font" hidden>
        <p class="menu-label">Theme</p>{themes}
        <p class="menu-label">Korean</p>{korean}
        <hr>
        <p class="menu-label">Reading font</p>{fonts}
      </div>
    </div>
  </nav>
</header>

<section class="hero" id="top" aria-labelledby="hero-title">
  <div class="hero-copy">
    <p class="eyebrow"><span class="rule"></span>A LoveSpark archive</p>
    <h1 id="hero-title">Papers worth<br>reading</h1>
    <p class="hero-dates">{count}</p>
    <p class="hero-description">The research behind modern AI, as timelines by field. Each entry gives the paper's main finding in one line; click it to open the full paper. When a later paper improved on or replaced an idea, the entry links forward to it, so you can follow a technique from where it started to what replaced it.</p>
    <div class="hero-actions">
      <a class="button" href="#start">Start reading <span aria-hidden="true">→</span></a>
      {field_links}
    </div>
  </div>
  <figure class="plaque" aria-labelledby="plaque-cap">
    <figcaption id="plaque-cap" class="plaque-cap">Three passes, from <a href="https://doi.org/10.1145/1273445.1273458" target="_blank" rel="noopener">Keshav, “How to Read a Paper”</a></figcaption>
    <ol>{passes}</ol>
  </figure>
</section>

<div class="layout">
  <nav class="toc" aria-label="Contents"><p class="eyebrow">Contents</p>{toc_items}</nav>
  <main id="main">
    <details class="toc-mobile"><summary>Contents</summary>{toc_items}</details>
    <section id="start">
      <p class="kicker"><span class="rule"></span>Start here</p>
      <h2>How to use this archive</h2>
      <p>Each field runs oldest to newest. Pick a field, read down the line, and open the papers whose finding surprises you. The <strong>title</strong> opens the full paper in a new tab, usually its free arXiv page. <strong>Built on</strong> and <strong>Led to</strong> jump to the papers before and after it, sometimes in another field: the transformer came out of translation work, and diffusion moved from images into robot control.</p>
      <p>The one-line findings are summaries, not quotes, so the paper is always the authority. Every title and link was checked against its source in {esc(data["checked"])}. Incident reports are marked as such: they are not peer-reviewed papers.</p>
    </section>
    {"".join(fields)}
  </main>
</div>

<footer>
  <div class="foot-inner">
    <img src="{mascot}" alt="Sparky, the LoveSpark wolf mascot">
    <div>One self-contained page: no server, no tracking, nothing leaves your machine except the papers you choose to open. Built from <code>data/papers.json</code> · MIT licensed · a <a href="https://lovespark.love/" rel="noopener">LoveSpark</a> archive · <a href="https://github.com/Joona-t/papers" rel="noopener">source on GitHub</a>.</div>
  </div>
</footer>

<script>
{(T / "base.js").read_text(encoding="utf-8")}}})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    out = build()
    target = ROOT / "index.html"
    if "--check" in sys.argv:
        ok = target.exists() and target.read_text(encoding="utf-8") == out
        print("index.html is up to date" if ok else "index.html is STALE: run python3 scripts/build.py"); sys.exit(0 if ok else 1)
    target.write_text(out, encoding="utf-8")
    print(f"wrote index.html ({len(out)//1024} KB)")
