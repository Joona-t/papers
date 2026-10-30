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
ok(years.length === data.fields.length, 'field sections');
for (const [f, ys] of years) ok(ys.every((y, i) => i === 0 || ys[i - 1] <= y), `${f}: timeline not in year order`);
const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
ok(ids.length === new Set(ids).size, 'duplicate ids');
for (const [, id] of html.matchAll(/href="#([^"]+)"/g)) ok(ids.includes(id), `missing anchor #${id}`);
for (const m of html.matchAll(/<a [^>]*target="_blank"[^>]*>/g)) ok(/rel="noopener"/.test(m[0]), `target=_blank without noopener: ${m[0]}`);

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
