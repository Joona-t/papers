# Papers worth reading

A small archive of the AI research papers worth reading, laid out as **timelines by field**: neural networks, machine learning & training, language models, computer vision, robotics & reinforcement learning, and safety & security.

Each entry gives the year, the paper's **main finding in one line**, and its title, which opens the full paper (usually its free arXiv page). **Built on** and **Led to** link each paper to the ones before and after it, so you can follow an idea from where it started to the technique that improved on or replaced it: LSTM → attention → the transformer, RLHF → DPO → GRPO → DeepSeek-R1, abliteration → its follow-ups and defences.

Read it at **[lovespark.love/papers](https://lovespark.love/papers/)**, or open `index.html` in any browser. It's one self-contained file: fonts and the mascot are inlined, it makes no network requests, and nothing leaves your machine except the papers you choose to open.

## Editing

`data/papers.json` is the source of truth. `index.html` is generated from it:

```bash
python3 scripts/build.py           # regenerate index.html
node scripts/verify.mjs            # offline: build freshness, links point forward in time, anchors, no network, no personal paths
python3 -I scripts/check_links.py  # online: every arXiv title matches arXiv, every other link resolves
```

To add a paper, add an object to `papers` with `id`, `field`, `year`, `short`, `title`, `authors`, `venue`, `finding`, `url` and `next` (ids of later papers that built on or replaced it), then run all three. Findings are one-line summaries in our own words, never quotes. Incident reports carry `"kind": "Incident report"` so they are never mistaken for peer-reviewed work.

## Design and accessibility

Same template as the [Qwen guide](https://lovespark.love/qwen-guide/): flat paper, hairline rules, a contents rail of numbered field cards. The **Change Font & Theme** menu has the five LoveSpark themes (Basalt, the lovespark.love default, plus Bubblegum, Retro Pink, Dark Noir and Beige Paper) and the nine **Y2K Korean** themes from the LoveSpark Retro Cursor pack: Honey Bunny 꿀토끼, Cyworld Dotti 싸이월드, Coquette Ribbon 리본, Strawberry Milk 딸기우유, Glossy Pearl, Bubble Boba 버블티, Phone Charm 폰꽂이, Heart Locket 하트 로켓 and Cyber Butterfly 나비. Each Korean theme uses its cursor pack's own colours; the build refuses any theme whose text falls below 4.8:1 contrast. Reading fonts: Serif, Sans and OpenDyslexic (bundled). Keyboard navigation, visible focus, `prefers-reduced-motion`, and it works down to 320 px.

## License

MIT. The papers belong to their authors; this archive only links to them.

100% local · no tracking · made for neurodivergent learners 🐺
