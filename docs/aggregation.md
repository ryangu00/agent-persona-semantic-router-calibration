# Chapter 6: Mean versus max, and why the threshold moves with them

### Problem

With the sidecar every persona has 4 to 5 more rows. Whether that helps depends on what is done with a persona's rows, and then on where the threshold sits.

### What we built

A 2x2 of (sidecar absent or present) x (mean or max aggregation) at the production threshold of 0.68, then a threshold sweep from 0.40 to 0.80 in steps of 0.01 for each of the four configurations on the same router object (`set_threshold` was probed as equivalent to a fresh build: both gave exact 11 and garbage 9 at 0.68), plus a score-level look at where garbage and correct routes sit.

**The mechanism.** Retrieval takes the global top 10 rows. Under mean, a persona's score is the mean of its rows inside that top 10; more phrasings put more of a persona's rows into the top 10, and the weaker ones pull the mean down. Under max a persona's score is its best row, which can only rise as rows are added. A worked case (a CI/CD pipeline request, derived):

| Pool | Persona | Rows in top 10 | Mean | Max |
|---|---|---|---|---|
| Without sidecar | an agent-orchestration persona | 2 | 0.665 | 0.716 |
| Without sidecar | the expected devops persona | 2 | 0.633 | 0.669 |
| With sidecar | the expected devops persona | 3 | 0.721 | 0.784 |
| With sidecar | its Chinese twin | 2 | 0.698 | 0.746 |

Without the sidecar the orchestrator wins at a mean of 0.665, below 0.68, so the request escalates. With the sidecar and max the devops persona scores 0.784 and is returned; with mean it would score 0.721, also routable here, but across the whole set mean did not convert the extra rows into more exact routes.

### Procedure as actually run

1. Collect embeddings once: `collect_embeddings` over the unique row texts plus the 37 evaluation leads (about 4.5 minutes for 2,819 texts; resumable). Output: an `npz` of keys and vectors plus a row manifest (rows per configuration).
2. Run the A/B harness (about 15 s, no network): it builds four in-process hybrid routers through the production code path with a cache-backed encoder, evaluates 27 + 10 items per router, then sweeps `set_threshold` from 0.40 to 0.80 and writes one JSON with the per-configuration results, the threshold scans and the per-case detail rows.
3. Expected console lines (recorded, identical across three independent runs and the offline replay):

```
BASELINE-mean : exact=11 sibling=3 wrong=6 escalated=7 | accept=12 | garbage 9/10 | precision 0.55
BASELINE-max  : exact=11 sibling=3 wrong=7 escalated=6 | accept=12 | garbage 9/10 | precision 0.524
EXP-FULL-mean : exact=11 sibling=8 wrong=6 escalated=2 | accept=13 | garbage 9/10 | precision 0.44
EXP-FULL-max  : exact=15 sibling=6 wrong=4 escalated=2 | accept=16 | garbage 8/10 | precision 0.60   (0.68)
EXP-FULL-max at 0.72: exact=14 | accept=15 | garbage 10/10 | precision 0.583
```

4. Run the regression gate against the live sidecar before and after: expected before activation `exact 11/27 (sibling 3, wrong 6, escalated 7) | garbage 9/10`, after `exact 14/27 (6, 4, 3) | garbage 10/10`.
5. Replay on 2026-10-03 (derived): the replay failed first with `CACHE MISS` on the first persona title that was not in the cache, because the live pool had grown from 395 to 400 personas since the experiment (Chapter 10). Removing the five added entries from a copy of the index restored a 395-persona pool and all four configurations reproduced exactly in 8 s. Lesson: the experiment's inputs (pool, sidecar, model) need a recorded hash, and the replay should refuse to run on a mismatch.

### Results

The full 2x2x2 (sidecar x aggregation x threshold), exact / sibling / wrong / escalated out of 27, garbage rejected out of 10, precision = exact/(exact+sibling+wrong). All cells are from the recorded results; the offline replay on 2026-10-03 reproduced the four 0.68 cells and the sweeps.

| Sidecar | Aggregation | Threshold | exact | sibling | wrong | escalated | accept-aware | garbage | precision |
|---|---|---|---|---|---|---|---|---|---|
| none (production) | mean | 0.68 | 11 | 3 | 6 | 7 | 12 | 9 | 0.550 |
| none | mean | 0.72 | 7 | 3 | 5 | 12 | 8 | 10 | 0.467 |
| none | max | 0.68 | 11 | 3 | 7 | 6 | 12 | 9 | 0.524 |
| none | max | 0.72 | 8 | 3 | 5 | 11 | 9 | 10 | 0.500 |
| 1,915 phrasings | mean | 0.68 | 11 | 8 | 6 | 2 | 13 | 9 | 0.440 |
| 1,915 phrasings | mean | 0.72 | 10 | 6 | 6 | 5 | 12 | 10 | 0.455 |
| 1,915 phrasings | max | 0.68 | 15 | 6 | 4 | 2 | 16 | 8 | 0.600 |
| 1,915 phrasings (shipped) | max | 0.72 | 14 | 6 | 4 | 3 | 15 | 10 | 0.583 |

Reading the grid: sidecar alone (mean, 0.68): no gain in exact, siblings 3 to 8, precision down 0.11. Max alone: no gain in exact, one more wrong route. Threshold alone: exact 11 to 7. Sidecar plus max at the old threshold: exact 15 but garbage rejected falls to 8 of 10, below production's 9. Only the last row has exact at least 14 and all garbage rejected.

Threshold sweep, exact / escalated / garbage rejected (recorded sweep, selected rows; the full 0.40 to 0.80 sweep is in the experiment's result file):

| Threshold | Production (mean, none) | Max, none | Mean, sidecar | Max, sidecar |
|---|---|---|---|---|
| 0.50 | 12 / 0 / 2 | 12 / 0 / 2 | 12 / 0 / 2 | 16 / 0 / 2 |
| 0.60 | 12 / 0 / 7 | 12 / 0 / 6 | 12 / 0 / 6 | 16 / 0 / 6 |
| 0.66 | 11 / 5 / 8 | 11 / 3 / 7 | 11 / 2 / 8 | 16 / 0 / 7 |
| 0.67 | 11 / 7 / 8 | 11 / 5 / 7 | 11 / 2 / 8 | 15 / 2 / 7 |
| 0.68 | 11 / 7 / 9 | 11 / 6 / 9 | 11 / 2 / 9 | 15 / 2 / 8 |
| 0.70 | 10 / 9 / 10 | 11 / 6 / 9 | 10 / 4 / 10 | 14 / 3 / 8 |
| 0.71 | 7 / 12 / 10 | 9 / 8 / 9 | 10 / 4 / 10 | 14 / 3 / 9 |
| 0.72 | 7 / 12 / 10 | 8 / 11 / 10 | 10 / 5 / 10 | 14 / 3 / 10 |
| 0.73 | 7 / 12 / 10 | 8 / 11 / 10 | 9 / 6 / 10 | 13 / 4 / 10 |
| 0.75 | 7 / 14 / 10 | 8 / 13 / 10 | 9 / 7 / 10 | 12 / 5 / 10 |
| 0.78 | 7 / 15 / 10 | 7 / 15 / 10 | 8 / 12 / 10 | 12 / 8 / 10 |

For the shipped configuration exact is 16 up to 0.66 (garbage rejected 7), 15 at 0.67 to 0.69 (garbage rejected 7, 8, 8), 14 at 0.70 to 0.72 (garbage rejected 8, 9, 10), 13 at 0.73 and 0.74. 0.72 is the saddle: the last threshold with exact 14 and the first with all garbage rejected.

Where the garbage actually scores (derived offline on 2026-10-03; best persona score per garbage input, sorted):

| Configuration | The ten garbage inputs, highest first |
|---|---|
| Production (mean, none) | 0.694, 0.678, 0.631, 0.579, 0.573, 0.540, 0.519, 0.515, 0.442, 0.412 |
| Max, none | 0.711, 0.678, 0.676, 0.603, 0.579, 0.540, 0.519, 0.515, 0.442, 0.437 |
| Mean, sidecar | 0.694, 0.678, 0.621, 0.603, 0.597, 0.579, 0.553, 0.529, 0.454, 0.412 |
| Max, sidecar (shipped) | 0.711, 0.700, 0.676, 0.603, 0.597, 0.579, 0.558, 0.544, 0.481, 0.437 |

The two highest garbage inputs in the shipped configuration are a keyboard-mash string with digits (0.711) and a short off-topic request (0.700). The old threshold 0.68 lets both through; 0.72 rejects both, and costs one correct semantic-tier route that scored 0.697.

Where correct and incorrect semantic-tier routes sit under the shipped configuration (15 items; score of the best persona, derived):

| Outcome | Scores |
|---|---|
| Correct (9) | 0.667, 0.697, 0.723, 0.742, 0.784, 0.823, 0.858, 0.904, 0.960 |
| Not correct (6) | 0.663, 0.766, 0.769, 0.771, 0.807, 0.840 |

Five of the six non-correct routes score 0.766 or higher. The threshold only separates garbage from content; it does not separate right from wrong.

### What did not work

- Shipping the sidecar with mean aggregation: stale gain, more near-misses.
- Switching to max without the sidecar: the lever only exists once there are extra rows to protect from dilution.
- Keeping 0.68 under max: garbage 8 of 10, a regression against production.
- Per-route thresholds were never tried (the library ships a fitting routine; our README lists it as a follow-up). With 37 items there is not enough data to fit 395 thresholds.

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| Recall barely moves after adding rows | Mean over the top-10 pool dilutes | Use max, or judge the aggregation first |
| Garbage suddenly routes after a "recall improvement" | Max over more rows raises every input's best score | Re-sweep the threshold for the new configuration; check the highest garbage score against it |
| Comparisons that mix arms | Baseline with one aggregation, experiment with another | Same-aggregation or same-sidecar comparisons only (the 2x2 exists for this) |

### The rule

Aggregation decides whether new rows help; the threshold must be re-fit for the aggregation you chose; ship the sidecar, the aggregation and the threshold as one change, and compare configurations at their own optimum, not at a shared threshold.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
