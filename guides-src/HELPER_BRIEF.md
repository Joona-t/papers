# Brief: writing study guides for "Papers worth reading"

You are writing study guides for papers in Joona's archive https://lovespark.love/papers-worth-reading/. Joona reads one paper each morning and wants real understanding. Each guide has two tabs:

- **Plain English**: for someone never formally taught the field. Everyday analogies, no jargon without explanation, short paragraphs. Simplify, but never say something false.
- **In depth**: for academics and professionals. The paper's actual setup, equations, algorithm, experiments with real numbers, limitations, and later refinements, with section/equation/table/figure references.

Accuracy is the top priority. Joona specifically wants guides to note when a later paper refined or replaced an idea (the archive's "finding" text for each paper in `papers.json` often says this; keep that framing). Check facts against the paper itself: fetch it with WebFetch (arXiv abs/html pages such as https://arxiv.org/abs/XXXX and https://arxiv.org/html/XXXXvN work well; curl is blocked by the network proxy, so use WebFetch/WebSearch). Every specific number, equation, quote, section/figure/table reference must come from the paper or a reliable source you checked. If you can't verify a detail, leave it out or phrase it without the specific. Never invent page numbers; prefer section numbers (§3.2), equation numbers, table/figure numbers that you saw.

## Files (all paths absolute)

Working dir: `guides-src/`

- `shell.html` – shared page template (CSS classes and JS helpers). READ IT, DO NOT EDIT IT.
- `build.py` – DO NOT EDIT. Run `python3 build.py <id>` to build `out/<id>.html`.
- `papers.json` – paper metadata (id, title, authors, year, url, finding, next). Read your papers' entries.
- `content/<id>.html` – the ONLY files you write. One per paper, named by the paper id.
- Reference examples, read at least two fully before writing: `content/mcculloch-pitts.html`, `content/backprop.html`, `content/lstm.html`, `content/forget-gate.html`. Match their structure, tone, density and quality.
- `figs.js` – `node figs.js <id>` screenshots every figure into `shots/<id>-figs.png` and reports JS errors. `shot.js` – `node shot.js <id>` screenshots whole pages at desktop/mobile and reports horizontal overflow and errors.

Do not touch other papers' content files, and do not write anything under the shared project folder

## Content file format

Four parts, each introduced by a marker on its own line:

```
<!--LEDE-->
One paragraph (2–3 sentences) shown under the title: the question the paper asks and its answer, plain language.
<!--SIMPLE-->
summary-box ("The paper in four sentences"), <nav class="toc"><p class="eyebrow">Ideas in this guide</p><ol></ol></nav> (auto-filled), then 4–6 <section class="kp" id="s1"> … sections
<!--TECH-->
summary-box ("Abstract, restated" — paraphrase, include venue/year), toc nav, 4–6 sections id="t1"…, last one a glossary with data-extra data-toc="Glossary"
<!--SCRIPT-->
<script> … one IIFE per interactive figure … </script>
```

Each section: `<p class="eyebrow"><b>Idea</b> · §2</p>` (or `<b>Section</b>` on the tech tab; the b text is auto-numbered; after the dot put the paper location such as § numbers, Fig./Table/Eq. numbers), `<h2>`, `<div class="prose">` with `<p>`s, optionally `<div class="analogy"><span class="label">Everyday picture</span>…</div>`, figures, `<div class="later"><span class="label">Later refinement</span>…</div>`, `<p class="takeaway"><span class="label">Takeaway</span>…</p>`, and `<details class="check"><summary>Check yourself</summary><dl><dt>Q</dt><dd>A</dd></dl></details>` (these will become flashcards; make the questions test understanding). Math: use HTML (`<var>`, `<sub>`, `<sup>`, Unicode symbols) inside `<div class="eq">…<span class="n">(3)</span></div>`. No external libraries, no KaTeX, no images. Algorithms can go in `<pre class="algo">`. Tables in `<div class="tablebox"><table>`.

Link to other guides by relative link `<a href="transformer.html">` using paper ids from papers.json (all 75 will exist).

## Interactive figures (the important part)

Each guide needs at least **2 interactive figures on the Plain English tab and at least 1–2 on the In depth tab** that genuinely build understanding of the paper's core mechanism (not decoration). Good patterns from the examples: a toy simulation the reader drives (sliders, buttons, step/run), a live mini-training run, a "try to break it" game, before/after toggles, step-through of an algorithm with real numbers. Where feasible, re-run a scaled-down version of the paper's own idea in the browser (e.g. a tiny attention computation, a 1-D diffusion process, Q-learning on a gridworld, LoRA rank vs parameter count, scaling-law curve with the paper's fitted constants). When showing a paper's reported numbers in a chart, use the real values and say where they come from; when a toy is illustrative, say so in the caption.

Markup: `<figure class="live">` containing `<div class="ctl">` (buttons `<button class="btn">`, ranges `<label>Name <input type="range" id="x" min max step value data-fmt="2"><output id="x-o">…</output></label>`), `<div class="svgbox"><svg id="…" viewBox="0 0 600 260" role="img" aria-label="…"></svg></div>` (add class `wide` to svgbox for wide timelines; it scrolls on phones), `<p class="readout" id="…"></p>`, `<figcaption>` explaining what to try. Static explanatory SVG diagrams (no JS) are also welcome, as plain `<figure>`.

JS: plain ES5-style functions are fine. Use the helpers in shell.html: `S(tag, attrs, parent, text)` creates SVG elements, `clear(el)`, `$`, `$$`, `fmt(x, d)`, `bindRange(id, fn)` (wires a range input to its output and calls fn immediately), `sigmoid`, `rng(seed)` (deterministic PRNG), `gauss(r)`. Always style SVG with the CSS classes from shell.html, never hard-coded colours, so dark mode works: text `t t-s t-h t-fire t-wire t-inh t-ok t-big`, alignment `mid end`, strokes `w w-faint w-fire w-inh w-ok w-ink w-dash axis grid area`, shapes `u u-on u-wire u-off box box-fire box-wire box-ok box-inh`, fills `f-fire f-wire f-inh f-ok f-muted f-ink f-card f-rule`, markers `url(#aw) url(#ai) url(#af) url(#ao) url(#bar)`. Make sure every interaction actually works and gives a sensible result (test it: write a small Playwright script with `require('playwright')`, or reason it through carefully). Avoid text overlapping in SVGs; keep labels inside the viewBox.

## Writing style

Full sentences, conversational and clear; no em-dashes; no arrow chains. British or American spelling is fine but be consistent within a guide (the examples use British: "normalise"). Plain English tab: assume no maths beyond arithmetic; introduce each term when first used. In depth tab: precise, compact, with the real equations and numbers. Include in the In depth tab a section on limitations and later refinements/lineage (linking to later papers in the archive where relevant, and naming important later work outside it). Aim for content files of roughly 25–45 KB each.

## Process per paper

1. Read the paper's papers.json entry, then fetch and read the paper (abstract + method + key results at least).
2. Write `content/<id>.html`.
3. `python3 build.py <id>` then `node figs.js <id>` and `node shot.js <id>`; fix any JS errors or overflow (shot.js prints "overflow 0 errors" when clean). LOOK at `shots/<id>-figs.png` with the Read tool and fix overlaps, empty charts, broken layouts.
4. Re-read your prose once against the paper for accuracy.

## Report back

When all your papers are done, reply with: for each paper id, one line listing its interactive figures, plus any facts you could not verify and left out or hedged. Keep the report under 300 words.
