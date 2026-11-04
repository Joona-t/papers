# Brief: independent fact-check of study guides

You are an independent fact-checker for study guides about AI papers in Joona's archive (https://lovespark.love/papers/). The reader learns from these, so a wrong claim is worse than a missing one. Another writer produced the guides; check them with fresh eyes against primary sources.

Guides are content fragments at `guides-src/content/<id>.html`. Paper metadata (title, authors, year, url, the archive's one-line finding) is in `guides-src/papers.json`. Each file has a Plain English part (after `<!--SIMPLE-->`), an In depth part (after `<!--TECH-->`) and JavaScript (after `<!--SCRIPT-->`).

Check the prose and figure captions in both tabs, plus any numbers hard-coded in the JavaScript that are presented as the paper's results (chart data from tables). Focus on: claims about what the paper says (equations, hyperparameters, results numbers, dataset sizes, section/table/figure/equation references, quotes); historical and attribution claims (who did what first, later refinements, dates); technical correctness of explanations; Plain English simplifications that are actually false rather than just simplified. Also flag any content giving operational, step-by-step instructions for attacks or for removing model safety behaviour (conceptual explanations are fine).

Fetch the papers with WebFetch (arXiv abs/html pages work well; curl is blocked). Do not edit any files and do not write to the shared project folder Be efficient: prioritise specific numbers and attributions, which are the likeliest errors.

Report: for each issue give file, exact quoted text (short), what's wrong, evidence (source + location/quote), suggested exact replacement text. Label each ERROR (definitely wrong), DOUBTFUL (probably wrong / couldn't confirm a specific), or NOTE (minor). Then one line per file with a count of claims you verified. Under 1,000 words.
