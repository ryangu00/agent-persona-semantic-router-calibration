# Chapter 7: The calibration procedure and where it is weak

### Problem and mechanism

A threshold selected for admission alone can preserve the wrong routes. Calibration must optimize exact correctness under an absolute garbage-rejection requirement.

### Procedure (what we actually ran, as a repeatable list)

1. **Freeze the inputs.** Pool snapshot (hash it), embedding model (digest), evaluation set, sidecar. Cache every text's vector once (here 2,819 vectors of 1,024 float64 values, 23 MB).
2. **Replay production in-process** with the same code path (Chapter 5). The baseline arm must reproduce the live gate numbers exactly (here 11/3/6/7, garbage 9 of 10). If it does not, stop.
3. **Run the factorial** (sidecar x aggregation) at the live threshold. Hold one factor fixed in every comparison.
4. **Sweep the threshold** from 0.40 to 0.80 step 0.01 for every configuration, reusing the built router.
5. **Pick a threshold per configuration** by a stated rule: among thresholds that reject at least as many garbage inputs as production (preferably all), take the highest exact count; if a higher threshold buys a garbage rejection at no exact cost, take the higher one (0.71 to 0.72 here).
6. **Compare configurations at their own optimum**, require that no metric degrades against production, and list newly introduced errors by name.
7. **Look at the score distributions** (garbage maxima, correct minima, the margin between them).
8. **Activate as one bundle** and raise the gate baseline in the same change (Chapter 8). Verify that live numbers equal the replay.

### Results: the per-configuration optimum

Highest-exact threshold that rejects at least 9 of 10 garbage inputs (recorded):

| Configuration | Threshold | exact | sibling | wrong | escalated | accept-aware | precision |
|---|---|---|---|---|---|---|---|
| Production (mean, none) | 0.68 (current is optimal) | 11 | 3 | 6 | 7 | 12 | 0.550 |
| Max, none | 0.68 (0.69 and 0.70 give the same exact) | 11 | 3 | 7 | 6 | 12 | 0.524 |
| Mean, sidecar | 0.68 | 11 | 8 | 6 | 2 | 13 | 0.440 |
| Max, sidecar | 0.72 (0.71 rejects only 9) | 14 | 6 | 4 | 3 | 15 | 0.583 |

Recorded decision numbers, shipped configuration against production: exact 11 to 14, accept-aware 12 to 15, escalated 7 to 3, garbage rejected 9 to 10 of 10, wrong 6 to 4, precision 0.550 to 0.583. The one cost listed: a newly wrong route (support triage, contested above).

### What is weak

1. **The margin is 0.009.** The highest garbage score is 0.711 and the threshold is 0.72. One more adversarial garbage string would defeat it; ten garbage items cannot characterise the tail of nonsense inputs.
2. **Selection on the test set.** The threshold, aggregation and sidecar were all chosen against the same 37 items that report the result. A second set authored after the sidecar existed would be the minimum honest follow-up.
3. **The shipped helper would not have found 0.72.** The module's `refit_global_threshold` maximises the fraction of in-domain scores that are admitted, subject to never admitting more garbage than the baseline threshold does, with ties to the lower threshold. Run on the shipped configuration's scores (derived offline on 2026-10-03), with baseline 0.50 it returns 0.49 and with baseline 0.68 it returns 0.68: it optimises admission, not correctness, and its invariant is relative to a baseline that already leaks. The decision came from the manual sweep with an absolute rule (reject all garbage, maximise exact). If you ship a helper, make the objective correctness and the invariant absolute.
4. **Selection by exact ignores that errors are confident** (Chapter 6 table): raising the threshold will not remove a wrong route that scores 0.84.
5. **One global threshold.** Per-route thresholds need many more labelled items per route.
6. **The evaluation prompts are short and English.** Long prompts, Chinese prompts and mixed-language prompts are covered only by the keyword tier's bigrams and by the lead-truncation rule, not by the sweep.
7. **Significance.** Five gained versus two lost exact items: p = 0.453 (Chapter 2).

### The rule

Write the calibration rule down before you sweep, make its invariant absolute (not relative to a leaky baseline), and report the margin to the nearest failure, not just the point you chose.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
