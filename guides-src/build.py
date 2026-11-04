#!/usr/bin/env python3
"""Assemble the study guides in guides/ (run: python3 guides-src/build.py).

shell.html + content/<id>.html + data/papers.json -> guides/<id>.html, guides/index.html, guides/make-your-own.html.
Originally: shell.html + content/<id>.html + papers.json -> out/<id>.html and out/index.html.

A content file holds four parts, each introduced by a marker line:
  <!--LEDE-->    one paragraph shown under the title
  <!--SIMPLE-->  the Plain English tab
  <!--TECH-->    the In depth tab
  <!--SCRIPT-->  <script> blocks for the interactive figures
"""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get('PAPERS_JSON', os.path.join(HERE, '..', 'data', 'papers.json'))
OUT = os.environ.get('OUT', os.path.join(HERE, '..', 'guides'))
os.makedirs(OUT, exist_ok=True)

d = json.load(open(DATA))
papers = {p['id']: p for p in d['papers']}
fields = {f['id']: f for f in d['fields']}
shell = open(os.path.join(HERE, 'shell.html')).read()
cdir = os.path.join(HERE, 'content')
have = {f[:-5] for f in os.listdir(cdir) if f.endswith('.html')}
esc = html.escape


def parts(src):
    out, cur = {}, None
    for line in src.splitlines(keepends=True):
        m = re.match(r'\s*<!--(LEDE|SIMPLE|TECH|SCRIPT)-->\s*$', line)
        if m:
            cur = m.group(1); out[cur] = ''; continue
        if cur: out[cur] += line
    return out


def link(pid):
    p = papers[pid]
    label = f'{esc(p["short"])} ({p["year"]})'
    if pid in have:
        return f'<a href="{pid}.html">{label}</a>'
    return f'{label} <span class="cite">(guide coming)</span>'


def nextbox(pid):
    p = papers[pid]
    before = [q['id'] for q in d['papers'] if pid in q.get('next', [])]
    rows = []
    if before:
        rows.append('<p><strong>Built on:</strong> ' + ', '.join(link(x) for x in before) + '</p>')
    if p.get('next'):
        rows.append('<p><strong>Led to:</strong> ' + ', '.join(link(x) for x in p['next']) + '</p>')
    if not rows:
        rows.append('<p>This is the newest step on its timeline so far.</p>')
    return '\n  '.join(rows)


def build(pid):
    p = papers[pid]
    c = parts(open(os.path.join(cdir, pid + '.html')).read())
    for k in ('LEDE', 'SIMPLE', 'TECH'):
        if not c.get(k, '').strip(): sys.exit(f'{pid}: missing {k}')
    links = [f'<a href="{esc(p["url"])}">{"Free explainer (" + esc(p["nofree"]) + ")" if p.get("nofree") else "Read the paper (free)"}</a>']
    if p.get('nofree'): links.append('<span class="badge">No free copy of the original</span>')
    links.append('<a href="https://lovespark.love/papers-worth-reading/">The archive</a>')
    lede = c['LEDE'].strip()
    rep = {
        'SHORT': esc(p['short']), 'YEAR': str(p['year']), 'TITLE': esc(p['title']),
        'AUTHORS': esc(p['authors']), 'VENUE': esc(p['venue']), 'FIELD': esc(fields[p['field']]['name']),
        'DESC': esc(re.sub('<[^>]+>', '', lede))[:300], 'LEDE': lede, 'LINKS': ' '.join(links),
        'ID': pid, 'SIMPLE': c['SIMPLE'], 'TECH': c['TECH'], 'SCRIPT': c.get('SCRIPT', ''), 'NEXT': nextbox(pid),
    }
    s = shell
    for k, v in rep.items(): s = s.replace('{{' + k + '}}', v)
    assert '{{' not in s.replace('{{', '', 0) or True
    open(os.path.join(OUT, pid + '.html'), 'w').write(s)


def index():
    rows = []
    for f in d['fields']:
        items = [p for p in d['papers'] if p['field'] == f['id']]
        lis = []
        for p in items:
            name = f'{esc(p["short"])} <span class="cite">{p["year"]}</span>'
            if p['id'] in have:
                lis.append(f'<li><a href="{p["id"]}.html">{name}</a><br><span class="t2">{esc(p["title"])}</span></li>')
            else:
                lis.append(f'<li class="soon">{name} <span class="cite">coming</span><br><span class="t2">{esc(p["title"])}</span></li>')
        rows.append(f'<section><h2>{esc(f["name"])}</h2><ol>{"".join(lis)}</ol></section>')
    css = re.search(r'<style>.*?</style>', shell, re.S).group(0)
    head = shell.split('<style>')[0].replace('{{SHORT}} ({{YEAR}}) study guide', 'Papers explained').replace('{{DESC}}', 'Study guides for every paper in the Papers worth reading archive.')
    body = f'''{css}
<style>.idx section{{padding-top:36px}} .idx ol{{margin:12px 0 0;padding-left:1.4em;display:grid;gap:10px}} .idx .t2{{color:var(--muted);font-size:.92rem}} .idx .soon{{color:var(--muted)}}</style>
</head><body><div class="wrap idx">
<header class="top"><p class="eyebrow">Study guides · {len(have)} of {len(papers)} ready</p><h1>Papers explained</h1>
<p class="lede">One guide per paper in <a href="https://lovespark.love/papers-worth-reading/">Papers worth reading</a>. Each has a Plain English tab for anyone and an In depth tab for specialists, with diagrams you can play with.</p>
<aside class="aimade"><span class="label">Made with AI · check it yourself</span><p>These guides were written by Claude, an AI model, and each was checked against its paper by a second, separate AI review (also by Claude). Joona, who runs the archive, has not personally read all of them yet, so mistakes can remain. The papers are the authority: verify anything that matters to you.</p><p>You can also <a href="make-your-own.html">ask an AI to make a guide just for you</a>, at your level and in the format you like.</p></aside></header>
{"".join(rows)}
</div></body></html>'''
    open(os.path.join(OUT, 'index.html'), 'w').write(head + body)


def extra_page():
    css = re.search(r'<style>.*?</style>', shell, re.S).group(0)
    head = shell.split('<style>')[0].replace('{{SHORT}} ({{YEAR}}) study guide', 'Make your own study guide').replace('{{DESC}}', 'How to ask Claude or another AI to make a study guide, video or flashcards for a research paper, tailored to you, and how to check it.')
    body = open(os.path.join(HERE, 'extra', 'make-your-own.body.html')).read()
    open(os.path.join(OUT, 'make-your-own.html'), 'w').write(head + css + '\n<style>figure.prompt{gap:8px} figure.prompt pre{white-space:pre-wrap}</style>\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')


ids = sys.argv[1:] or sorted(have)
for pid in ids: build(pid)
index()
extra_page()
print('built', len(ids), 'guides;', len(have), 'content files')
