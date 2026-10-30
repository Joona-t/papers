// Offline checks for the built archive. Run: node scripts/verify.mjs  (exit 0 = PASS)
// Online link/title checks are separate: python3 -I scripts/check_links.py
import { readFileSync } from 'node:fs';
import { strict as assert } from 'node:assert';
import { execFileSync } from 'node:child_process';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const html = readFileSync(new URL('index.html', root), 'utf8');
const data = JSON.parse(readFileSync(new URL('data/papers.json', root), 'utf8'));
let checks = 0;
const ok = (c, msg) => { assert.ok(c, msg); checks++; };

// 1. index.html is exactly what the build produces from the data
execFileSync('python3', ['-I', 'scripts/build.py', '--check'], { cwd: root, stdio: 'pipe' }); checks++;

// 2. the data: unique ids, known fields, https links, findings present, links point forward in time
const byId = new Map(data.papers.map(p => [p.id, p]));
ok(byId.size === data.papers.length, 'duplicate paper id');
const fieldIds = new Set(data.fields.map(f => f.id));
for (const f of data.fields) ok(data.papers.some(p => p.field === f.id), `empty field ${f.id}`);
for (const p of data.papers) {
  ok(fieldIds.has(p.field), `${p.id}: unknown field ${p.field}`);
  ok(/^https:\/\//.test(p.url), `${p.id}: url must be https`);
  for (const k of ['title', 'short', 'authors', 'venue', 'finding']) ok(p[k] && p[k].trim(), `${p.id}: missing ${k}`);
  ok(Number.isInteger(p.year) && p.year >= 1900 && p.year <= 2100, `${p.id}: bad year`);
  for (const n of p.next) {
    ok(byId.has(n), `${p.id}: next -> unknown ${n}`);
    ok(byId.get(n).year >= p.year, `${p.id} (${p.year}) leads to an older paper ${n} (${byId.get(n).year})`);
    ok(n !== p.id, `${p.id} leads to itself`);
  }
  for (const a of p.also || []) ok(/^https:\/\//.test(a.url), `${p.id}: also url must be https`);
}

// 3. page integrity: every paper rendered once, linked to its url, ids unique, anchors resolve
for (const p of data.papers) {
  ok(html.split(`<article class="entry" id="${p.id}">`).length === 2, `${p.id} not rendered exactly once`);
  ok(html.includes(`href="${p.url.replace(/&/g, '&amp;')}"`), `${p.id}: paper link missing`);
}
const years = [...html.matchAll(/<section class="field" id="([^"]+)">([\s\S]*?)<\/section>/g)].map(m => [m[1], [...m[2].matchAll(/class="entry-year">(\d+)</g)].map(y => +y[1])]);
const fieldSet = new Set(data.fields.map(f => f.id));
years.splice(0, years.length, ...years.filter(([f]) => fieldSet.has(f)));
ok(years.length === data.fields.length, 'field sections');
for (const [f, ys] of years) ok(ys.every((y, i) => i === 0 || ys[i - 1] <= y), `${f}: timeline not in year order`);
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
ok(ids.length === new Set(ids).size, 'duplicate ids');
for (const [, id] of html.matchAll(/href="#([^"]+)"/g)) ok(ids.includes(id), `missing anchor #${id}`);
for (const m of html.matchAll(/<a [^>]*target="_blank"[^>]*>/g)) ok(/rel="noopener"/.test(m[0]), `target=_blank without noopener: ${m[0]}`);

// 3b. further reading: unique ids, https, rendered once, the path points at real items
const res = data.resources, resIds = new Set(res.items.map(r => r.id));
ok(resIds.size === res.items.length, 'duplicate resource id');
for (const id of res.path) ok(resIds.has(id), `path -> unknown resource ${id}`);
const groups = new Set([...fieldSet, 'start', 'papers']);
for (const r of res.items) {
  ok(groups.has(r.field), `${r.id}: unknown group ${r.field}`);
  ok(/^https:\/\//.test(r.url), `${r.id}: url must be https`);
  for (const k of ['title', 'by', 'kind', 'why']) ok(r[k] && r[k].trim(), `${r.id}: missing ${k}`);
  ok(html.split(`href="${r.url.replace(/&/g, '&amp;')}"`).length === 2, `${r.id}: not rendered exactly once`);
}

// 3c. Joona 2026-10-30: only open, free links that need no sign-in. Publisher and course hosts that show
//     paywalls or sign-in walls are refused outright; link an author's, lab's or arXiv copy instead.
const WALLED = /\b(doi\.org|dl\.acm\.org|nature\.com|science\.org|ieeexplore\.ieee\.org|psycnet\.apa\.org|doi\.apa\.org|direct\.mit\.edu|sciencedirect\.com|link\.springer\.com|onlinelibrary\.wiley\.com|researchgate\.net|academia\.edu|scribd\.com|medium\.com|coursera\.org|udemy\.com|linkedin\.com)\b/i;
for (const [, href] of html.matchAll(/href="(https?:[^"]+)"/g)) ok(!WALLED.test(href), `walled or sign-in host linked: ${href}`);

// 4. no network: no external scripts, styles or images; no network APIs in the script
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script); checks++;
ok(!/<(?:script|img|iframe)\b[^>]*\bsrc\s*=\s*["']https?:/i.test(html), 'external script/img');
ok(!/<link\b[^>]*\bhref\s*=\s*["']https?:/i.test(html), 'external stylesheet');
ok(!/\b(fetch|XMLHttpRequest|WebSocket|sendBeacon)\s*\(/.test(script), 'network API in script');

// 5. no local paths ship
const personal = /\/Users\/[A-Za-z]|\/home\/[A-Za-z]|C:\\Users\\/;
for (const [name, text] of [['index.html', html.replace(/data:[^"')]+/g, '')], ['data', JSON.stringify(data)]]) ok(!personal.test(text), `personal reference in ${name}: ${text.match(personal)}`);

console.log(JSON.stringify({ result: 'PASS', papers: data.papers.length, checks }, null, 1));
