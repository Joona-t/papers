# Bugs and iterations

## ITER-001 · 2026-10-30 · First release
- 63 papers in six field timelines (1958–2026), each with a one-line finding, a link to the full paper and Built on / Led to links between papers.
- Template copied from the Qwen guide (Basalt default, five themes, three reading fonts), plus nine Y2K Korean themes from the LoveSpark Retro Cursor pack.
- Checks: `verify.mjs` (offline) and `check_links.py` (online). Every arXiv title matched arXiv, and every DOI and other link resolved, on 2026-10-30.

## BUG-001 · 2026-10-30 · Link checker: arXiv API rate-limited (429)
- Root cause: `export.arxiv.org/api/query` answered 429 even with backoff and batches of 20.
- Fix: read each title from the abstract page's `citation_title` meta tag instead, 1.5 s apart.

## BUG-002 · 2026-10-30 · Link checker: false failures
- π0's arXiv title is LaTeX (`$\pi_0$`), so the title match failed. The matcher now maps it to π0.
- MIT Press answers scripts with 403, which failed the LSTM DOI. A DOI that redirects to its publisher now counts as resolved.
- 2605.09504 was retitled in v3. The entry now uses the current title, re-checked against the v3 abstract.

## BUG-003 · 2026-10-30 · Theme menu: Korean names broke mid-word and the menu ran off short screens
- Root cause: the template's 220 px menu let Hangul break between syllables (꿀토 / 끼), and 14 themes plus 3 fonts are taller than a phone screen.
- Fix: no-wrap rows, `word-break: keep-all`, a 272 px menu capped to the window and scrollable. Checked at 320 × 640.

## Note · storage keys
- Theme and font are saved under `papers-*`, not the Qwen guide's `qft-*`. Both pages share the lovespark.love origin, and the Qwen guide has no Korean themes to restore.

## ITER-002 · 2026-10-30 · Korean themes are the Retro Cursor popup themes, plus their fonts
- Joona: he wanted the Korean themes for changing the look, not the cursor packs. The nine cursor-pack palettes are gone, replaced by the four Korean popup themes: Seoul Y2K 서울, Gingham Sticker 깅엄, Holo Mochi 모찌 and Neon Usagi 네온, with their backgrounds and card styles. Gingham's pattern stays off the reading area (a top band and the footer), following the popup's rule that text never sits on a pattern.
- Added the extension's reading fonts: Lexend and Comfortaa (variable, one file each) and Atkinson Hyperlegible, inlined as woff2.
- The contrast gate now also checks each theme's gradient stops. It caught Seoul's #c2185b accent at 4.52:1 on the lavender stop, so the accent is now #a8134f.
- A saved theme or font the page no longer offers falls back to Basalt and Serif.
- Checks: verify.mjs passes; in the browser, 9 themes × 6 fonts show no overflow at 320 px and the lowest text contrast is 4.84:1.
