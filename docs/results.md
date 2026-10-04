# Complete historical tables

These tables reproduce the supplied record. They are not new runs of the private pool. Synthetic demo outputs belong under `artifacts/` and must not be substituted for these numbers. Counts, rounding, qualifiers and the contested label are retained.

## Setting

Conditions: Historical record supplied as of 2026-10-03; setting and timeline are historical, not a measurement of the public synthetic demo.

| Item | Value |
|---|---|
| Host for the router and the embedding service | One Apple-silicon Mac running macOS; the router is a user-level launchd service bound to localhost only. Latency figures below are indicative for that class of machine and were not controlled. |
| Python | 3.11.15 in an isolated virtual environment (uv-managed CPython). The system Python was 3.14, on which `pip install semantic-router` silently resolved to an old 0.0.20 release without the Ollama encoder (the library needs Python below 3.14 for 0.1.x). |
| Routing library | `semantic-router==0.1.15` (MIT). Pinned with `ollama==0.6.2`, `httpx==0.28.1`, `numpy==2.4.6`, `pydantic==2.13.4`; historical tests used `pytest==9.1.0`. The public suite uses standard-library `unittest` and does not require pytest. |
| Embedding model | Qwen3-Embedding 0.6B served through Ollama, 1024 dimensions, tag pinned to the stock weights (tag digest prefix `4c1a55ec`, 0.60 GB). Ollama 0.30.10 was the version in use when the batch-crash of Chapter 5 was observed on 2026-09-23. |
| Persona pool | 395 personas, merged and de-duplicated from two public MIT-licensed persona collections (one English, one Chinese translation/adaptation) as a one-time snapshot on 2026-05-23. 184 of the 395 have English identifiers, 211 have Chinese-language identifiers (mostly translated twins of English personas). Each persona is a markdown file; the index lists name, path, title, description, tags (the category), keywords, capabilities; only 78 of 395 have an `expanded_description`. |
| Pool provenance pins | English upstream pinned at commit prefix `783f6a72bf` (2026-04-12); Chinese upstream at `13b8800f6f` (2026-05-18). Both README pages state the MIT license (checked on the web on 2026-10-03; license files and copyright lines were not independently rechecked for this cookbook; no upstream text is redistributed). |
| Rows embedded | 868 rows without the sidecar (title, description, expanded description per persona) and 2,783 rows with it (exactly +1,915); 2,819 unique texts including the 37 evaluation leads. |
| Evaluation | 27 in-domain terse task requests plus 10 garbage inputs, authored blind to the persona descriptions and to the sidecar (Chapter 2). |
| Utterance generation (sync pipeline) | A local model on a Dell Pro Max with GB10: first choice a 4B instruct model through Ollama, fallback a vLLM-served model, temperature 0.6, 256 max tokens. The generator for the original 1,915 phrasings was a local model whose name was not recorded. |

## Timeline

Conditions: Historical record supplied as of 2026-10-03; setting and timeline are historical, not a measurement of the public synthetic demo.

| Date | Event |
|---|---|
| 06-15 | Router built by adopting the routing library plus a thin adapter; 14 tests; threshold 0.45 raised to 0.50 after a probe; wired into the delegation tool as an opt-in, fail-open call and switched on for all agents later that day. |
| 06-16 | Design reviewed adversarially in three rounds; keyword tier fixes; 1,915 phrasings and keywords generated; offline measure said "go" at threshold 0.50; activation parked. |
| 08-18 | A fine-tuned embedding model is deployed under the stock tag for another consumer; the router silently loses its semantic tier. |
| 09-06 | Outage found (19 days); tag pinned to stock weights; threshold 0.50 to 0.68; three keyword-tier repairs measured and rejected; full A/B blocked by embedding-server crashes. |
| 09-08 | Small-sample A/B (37 personas, 111 phrasings). |
| 09-09 | Full A/B and threshold re-sweep. |
| 09-10 | Consumer check: what happens to the route. |
| 09-14 | Trio activated; gate baseline raised from 11/9 to 14/10. |
| 09-16 | Upstream-sync tooling written and exercised on hand-built inputs. |
| 09-23 | Router fails to restart; fixed with a one-text-per-call encoder. |

## Chapter 1: The router and its contract - Procedure as actually run (first measurements, 2026-06-15)

Conditions: Historical record supplied as of 2026-10-03; initial probe on 2026-06-15, stock Qwen3-Embedding 0.6B, 10 in-domain and 4 out-of-domain tasks; timings indicative.

| Observation | Value |
|---|---|
| In-domain, sensible persona | 10 of 10 |
| In-domain score band | 0.54 to 0.78 |
| Out-of-domain escalated (empty, small talk, off-topic question, random tokens) | 3 of 4 at the final threshold 0.50 with an empty-input short-circuit before embedding; the recorded earlier state (threshold 0.45, no short-circuit) leaked 3 of 4 |
| Random-token garbage | about 0.63, overlapping the low end of the in-domain band |
| Build over 395 personas | about 11 s (embedding all rows once) |
| One query | one local embedding call plus one cosine over the matrix (no latency distribution was recorded) |

## Chapter 1: The router and its contract - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; initial probe on 2026-06-15, stock Qwen3-Embedding 0.6B, 10 in-domain and 4 out-of-domain tasks; timings indicative.

| Symptom | Root cause | Fix |
|---|---|---|
| Install "works" but `OllamaEncoder` is missing | System Python 3.14 resolves an ancient `semantic-router` 0.0.20 | Use a Python 3.11 virtual environment and pin `semantic-router==0.1.15` |
| Enrichment had no effect in a design draft | The router constructor was never passed `aggregation` and `top_k`; every sidecar experiment would have been silently inert | Pass both explicitly; a test mocks the library class and asserts the kwargs (`aggregation`, `top_k == 10`) |
| Raw task text ended up in a world-readable temp file | An early debug log wrote the first 60 characters of every task | Salted-hash-only log, mode 0600, off by default, ignored by version control and sync (a test asserts raw text never appears) |

## Chapter 2: Measuring a router with 37 blind items - Evaluation set

Conditions: Historical record supplied as of 2026-10-03; 27 in-domain and 10 garbage items; uncertainty and overlap statistics derived offline on 2026-10-03; original labels retained.

| Property | Value |
|---|---|
| In-domain items | 27, 6 to 11 words (49 to 67 characters) each, all English |
| Expected-persona categories | engineering 9, finance 4, design 3, marketing 3, testing 3, game development 2, support 2, product 1 (8 categories out of roughly two dozen) |
| Garbage items | 10, 7 to 36 characters: 2 keyboard-mash strings, 2 repeated-character strings, 1 digit string, 4 short off-topic consumer requests, 1 greeting |
| Accept sets | 12 of the 27 items list extra acceptable personas: 11 are the Chinese-language twin of the expected English persona, plus one role synonym (an incident-response persona for a reliability item). 15 items have none (strict match) |

## Chapter 2: Measuring a router with 37 blind items - Metric definitions

Conditions: Historical record supplied as of 2026-10-03; 27 in-domain and 10 garbage items; uncertainty and overlap statistics derived offline on 2026-10-03; original labels retained.

| Metric | Definition |
|---|---|
| exact | routed persona equals the expected persona |
| sibling | routed persona has the same category (second segment of the identifier) but is not the expected one; a Chinese twin counts as sibling unless it is in the accept set |
| wrong | routed to a different category |
| escalated | no persona returned |
| accept-aware hit | routed persona is in {expected} plus the accept set |
| garbage rejected | garbage input returned no persona |
| precision | exact / (exact + sibling + wrong); escalations are excluded from the denominator |

## Chapter 2: Measuring a router with 37 blind items - Uncertainty and paired changes

Conditions: Historical record supplied as of 2026-10-03; 27 in-domain and 10 garbage items; uncertainty and overlap statistics derived offline on 2026-10-03; original labels retained.

| Quantity | Value |
|---|---|
| One in-domain item | 3.7 percentage points |
| Exact, production before | 11 of 27 = 0.407, Wilson 95% interval 0.245 to 0.593 |
| Exact, shipped setting | 14 of 27 = 0.519, Wilson 95% interval 0.340 to 0.693 |
| Paired changes, production to shipped | 5 items gained exact (3 escalated to exact, 2 wrong to exact), 2 lost exact |
| Two-sided exact sign test on 5 versus 2 | p = 0.453 |
| Same, if the contested label below is replaced | 6 gained versus 1 lost, p = 0.125 |
| Garbage rejection 9 of 10 versus 10 of 10 | one item; Wilson intervals 0.596 to 0.982 and 0.722 to 1.0 |

## Chapter 2: Measuring a router with 37 blind items - Lexical overlap

Conditions: Historical record supplied as of 2026-10-03; 27 in-domain and 10 garbage items; uncertainty and overlap statistics derived offline on 2026-10-03; original labels retained.

| Statistic | Value |
|---|---|
| Best-phrasing cosine, all 27 items | min 0.606, mean 0.762, max 0.960 |
| Best phrasing belongs to the expected persona | 17 of 27 |
| Items with token overlap (Jaccard over non-stopword tokens) at least 0.4 with some phrasing | 5 of 27 (values 0.43, 0.44, 0.50, 0.62, 0.83) |
| Of the 5 items that gained exactness under the shipped setting | 2 have overlap at least 0.4 (0.44, 0.50); 3 have 0.33 or less (0.17 to 0.33) |

## Chapter 2: Measuring a router with 37 blind items - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; 27 in-domain and 10 garbage items; uncertainty and overlap statistics derived offline on 2026-10-03; original labels retained.

| Symptom | Root cause | Fix |
|---|---|---|
| "Wrong" routes that look reasonable | Category-level sibling and twin handling in the metric | Report exact, sibling, wrong, escalated separately; keep accept sets minimal |
| A hit counted although the router escalated | Accept-set logic applied before the escalate check | `hit = (not escalate) and persona in accept`; tests cover unlisted personas counting as misses |
| Gate crashes on a persona identifier without a hyphen | Category is derived with `identifier.split("-")[1]` | Derive the category from the index record, not the identifier (latent: five identifiers added later have no such structure; see Chapter 10) |

## Chapter 3: A router that died silently for 19 days - What happened

Conditions: Historical record supplied as of 2026-10-03; 2026-09-06 repair; stock model, mean, no sidecar; 27 in-domain and 10 garbage items where counts are reported.

| Check | Observation |
|---|---|
| Duration | 2026-08-18 to 2026-09-06 = 19 days |
| Same query, swapped model | top 0.44, median 0.06 |
| Same query, stock model | top 0.72 |
| Stock model digest prefix / size | `4c1a55ec` / 0.60 GB |
| Fine-tuned model size | 1.12 GB (different digest) |
| In-domain exact before the repair, at threshold 0.50 | 8 of 27 (as logged; the substring and keyword tiers kept answering, which is the likely source of these 8) |
| In-domain exact after the repair, at threshold 0.50 | 12 of 27 (matches the sweep row at 0.50) |
| Garbage rejected at 0.50, before / after the repair | 8 of 10 (trivially: nothing reached the threshold) / 2 of 10 |

## Chapter 3: A router that died silently for 19 days - Results: the first calibration (stock model, mean aggregation, no sidecar)

Conditions: Historical record supplied as of 2026-10-03; 2026-09-06 repair; stock model, mean, no sidecar; 27 in-domain and 10 garbage items where counts are reported.

| Threshold | exact | escalated | garbage rejected |
|---|---|---|---|
| 0.45 | 12 | 0 | 2 |
| 0.50 | 12 | 0 | 2 |
| 0.55 | 12 | 0 | 5 |
| 0.60 | 12 | 0 | 7 |
| 0.64 | 11 | 3 | 8 |
| 0.67 | 11 | 7 | 8 |
| 0.68 | 11 | 7 | 9 |
| 0.70 | 10 | 9 | 10 |
| 0.72 | 7 | 12 | 10 |

## Chapter 3: A router that died silently for 19 days - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; 2026-09-06 repair; stock model, mean, no sidecar; 27 in-domain and 10 garbage items where counts are reported.

| Symptom | Root cause | Fix |
|---|---|---|
| Health green, every request escalates | Fail-open caller plus a health check that does not exercise routing | Probe with fixed tasks that must route, and alert on the non-escalation rate |
| Same tag, different model | Shared mutable tag; the pull/tag operation replaces content silently | Pin by digest or by a private tag; check a fixed probe pair's cosine against a recorded reference (the stock-versus-fine-tuned cosine for one input ranges 0.74 to 0.96, so test the expected reference, not a loose band) |
| Orphan process holds the port after restart | `kickstart -k` raced the old instance; label disabled | After every restart assert that the process manager's pid equals the pid listening on the port, and inspect the process's own environment |
| Threshold "calibrated" but unusable | Calibrated on one embedding distribution; model changed | Store the model digest next to the threshold; recalibrate when it changes |

## Chapter 4: The keyword tier: no score, twelve decisions, three rejected fixes - Tier contributions

Conditions: Historical record supplied as of 2026-10-03; keyword alternatives measured 2026-09-06 on 27 in-domain and 10 garbage items; source breakdown derived offline on 2026-10-03.

| Source | Items | exact | sibling | wrong |
|---|---|---|---|---|
| keyword (all configurations, unchanged by every experiment) | 12 | 7 | 3 | 2 |
| semantic, production (mean, no sidecar, 0.68) | 15 | 4 | 0 | 4 (plus 7 escalated) |
| semantic, shipped (max, sidecar, 0.72) | 15 | 7 | 3 | 2 (plus 3 escalated) |

## Chapter 4: The keyword tier: no score, twelve decisions, three rejected fixes - Repair comparisons

Conditions: Historical record supplied as of 2026-10-03; keyword alternatives measured 2026-09-06 on 27 in-domain and 10 garbage items; source breakdown derived offline on 2026-10-03.

| Variant | exact | sibling | wrong | escalated | Verdict |
|---|---|---|---|---|---|
| A: current (keyword hit short-circuits) | 11 | 3 | 6 | 7 | best, kept |
| Coverage gate, fraction at least 0.5 | 8 | 2 | 4 | 13 | net loss; correct hits also cut |
| Coverage gate, fraction 0.6 to 0.8 | 5 | 1 | 4 | 17 | worse |
| B: delete the keyword tier (semantic only) | 4 | 1 | 4 | 18 | exact cut by more than half |
| C: semantic review when tiers disagree | 10 | 4 | 6 | 7 | no gain, an extra embedding call |

## Chapter 4: The keyword tier: no score, twelve decisions, three rejected fixes - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; keyword alternatives measured 2026-09-06 on 27 in-domain and 10 garbage items; source breakdown derived offline on 2026-10-03.

| Symptom | Root cause | Fix |
|---|---|---|
| A request is routed to the wrong persona by a word it merely contains | Bigram or token overlap with a persona name, weight 3, no abstain path | Generic-token filter, strict-winner rule; accept that some confident errors remain |
| A short acronym never fires | Token length gate (3) | Curated allow-list of acronyms, not a lower global gate |
| Tie between two personas | Per-token max scoring makes ties common | Ties escalate (strict-winner clause) |

## Chapter 5: The utterance sidecar - Results

Conditions: Historical record supplied as of 2026-10-03; small A/B on 2026-09-08: mean, 0.68, 37 enriched personas, 111 phrasings, 27 in-domain and 10 garbage items.

| Group | exact | sibling | wrong | escalated | garbage rejected | accept-aware hits | precision |
|---|---|---|---|---|---|---|---|
| Baseline (no phrasings) | 11 | 3 | 6 | 7 | 9 | 12 | 0.550 |
| +111 phrasings, 37 personas | 12 | 6 | 5 | 4 | 9 | 15 | 0.522 |

## Chapter 5: The utterance sidecar - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; small A/B on 2026-09-08: mean, 0.68, 37 enriched personas, 111 phrasings, 27 in-domain and 10 garbage items.

| Symptom | Root cause | Fix |
|---|---|---|
| Embedding server runner dies with tokenize EOF | Large or multi-text requests through the library's own sync path | Direct batched `/api/embed` with retries, or one text per call; cache vectors on disk |
| Experiment passes a type check but scores nothing | Duck-typed encoder rejected by pydantic | Subclass the library's dense encoder |
| Experimental numbers do not match live | Different tier state, threshold or model tag | First reproduce the live gate numbers in-process; only then trust the other arms |
| "It restarts fine" | It never restarted; start-up path untested | Run a cold restart rehearsal for any service that has been up for weeks |

## Chapter 6: Mean versus max, and why the threshold moves with them - What we built

Conditions: Historical record supplied as of 2026-10-03; full A/B on 2026-09-09, fixed keyword tier, global top 10; 27 in-domain and 10 garbage items; grid replay and score analyses derived offline on 2026-10-03.

| Pool | Persona | Rows in top 10 | Mean | Max |
|---|---|---|---|---|
| Without sidecar | an agent-orchestration persona | 2 | 0.665 | 0.716 |
| Without sidecar | the expected devops persona | 2 | 0.633 | 0.669 |
| With sidecar | the expected devops persona | 3 | 0.721 | 0.784 |
| With sidecar | its Chinese twin | 2 | 0.698 | 0.746 |

## Chapter 6: Mean versus max, and why the threshold moves with them - Full factorial

Conditions: Historical record supplied as of 2026-10-03; full A/B on 2026-09-09, fixed keyword tier, global top 10; 27 in-domain and 10 garbage items; grid replay and score analyses derived offline on 2026-10-03.

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

## Chapter 6: Mean versus max, and why the threshold moves with them - Threshold sweep

Conditions: Historical record supplied as of 2026-10-03; full A/B on 2026-09-09, fixed keyword tier, global top 10; 27 in-domain and 10 garbage items; grid replay and score analyses derived offline on 2026-10-03.

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

## Chapter 6: Mean versus max, and why the threshold moves with them - Garbage scores

Conditions: Historical record supplied as of 2026-10-03; full A/B on 2026-09-09, fixed keyword tier, global top 10; 27 in-domain and 10 garbage items; grid replay and score analyses derived offline on 2026-10-03.

| Configuration | The ten garbage inputs, highest first |
|---|---|
| Production (mean, none) | 0.694, 0.678, 0.631, 0.579, 0.573, 0.540, 0.519, 0.515, 0.442, 0.412 |
| Max, none | 0.711, 0.678, 0.676, 0.603, 0.579, 0.540, 0.519, 0.515, 0.442, 0.437 |
| Mean, sidecar | 0.694, 0.678, 0.621, 0.603, 0.597, 0.579, 0.553, 0.529, 0.454, 0.412 |
| Max, sidecar (shipped) | 0.711, 0.700, 0.676, 0.603, 0.597, 0.579, 0.558, 0.544, 0.481, 0.437 |

## Chapter 6: Mean versus max, and why the threshold moves with them - Semantic outcome scores

Conditions: Historical record supplied as of 2026-10-03; full A/B on 2026-09-09, fixed keyword tier, global top 10; 27 in-domain and 10 garbage items; grid replay and score analyses derived offline on 2026-10-03.

| Outcome | Scores |
|---|---|
| Correct (9) | 0.667, 0.697, 0.723, 0.742, 0.784, 0.823, 0.858, 0.904, 0.960 |
| Not correct (6) | 0.663, 0.766, 0.769, 0.771, 0.807, 0.840 |

## Chapter 6: Mean versus max, and why the threshold moves with them - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; full A/B on 2026-09-09, fixed keyword tier, global top 10; 27 in-domain and 10 garbage items; grid replay and score analyses derived offline on 2026-10-03.

| Symptom | Root cause | Fix |
|---|---|---|
| Recall barely moves after adding rows | Mean over the top-10 pool dilutes | Use max, or judge the aggregation first |
| Garbage suddenly routes after a "recall improvement" | Max over more rows raises every input's best score | Re-sweep the threshold for the new configuration; check the highest garbage score against it |
| Comparisons that mix arms | Baseline with one aggregation, experiment with another | Same-aggregation or same-sidecar comparisons only (the 2x2 exists for this) |

## Chapter 7: The calibration procedure and where it is weak - Results: the per-configuration optimum

Conditions: Historical record supplied as of 2026-10-03; same full A/B and recorded sweep; 27 in-domain, 10 garbage; optimum requires at least 9 garbage rejections, with all preferred.

| Configuration | Threshold | exact | sibling | wrong | escalated | accept-aware | precision |
|---|---|---|---|---|---|---|---|
| Production (mean, none) | 0.68 (current is optimal) | 11 | 3 | 6 | 7 | 12 | 0.550 |
| Max, none | 0.68 (0.69 and 0.70 give the same exact) | 11 | 3 | 7 | 6 | 12 | 0.524 |
| Mean, sidecar | 0.68 | 11 | 8 | 6 | 2 | 13 | 0.440 |
| Max, sidecar | 0.72 (0.71 rejects only 9) | 14 | 6 | 4 | 3 | 15 | 0.583 |

## Chapter 8: Shipping it - Results

Conditions: Historical record supplied as of 2026-10-03; activation on 2026-09-14; 27 in-domain and 10 garbage items; restart crash observed 2026-09-23.

| Check | Before activation (production) | After activation (shipped) |
|---|---|---|
| Gate: exact / garbage rejected | 11 / 9 | 14 / 10 |
| Gate constants | 11 / 9 | 14 / 10 |
| Default threshold | 0.68 | 0.72 |
| Aggregation | mean | max |
| Sidecar rows | 0 | 1,915 over 395 personas |

## Chapter 8: Shipping it - Failure signatures (strings and numbers to alert on)

Conditions: Historical record supplied as of 2026-10-03; activation on 2026-09-14; 27 in-domain and 10 garbage items; restart crash observed 2026-09-23.

| Signature | Meaning |
|---|---|
| Embedding server error `Post http://localhost:<runner-port>/tokenize: EOF` or `connect timed out` during index build or start-up | Runner crash on a multi-text request; service stays down and the supervisor loops |
| Every fixed probe escalates; top similarity near 0.44 and median near 0.06 where a healthy model gives 0.7 | Embedding model replaced (Chapter 3) |
| `/health` ok but the process manager's pid differs from the pid listening on the port | Orphan holds the port (Chapters 3 and 8) |
| Gate message `ALERT regression: in-domain exact X/27 ... [baseline exact>=14 garbage-rejected>=10]` with the first six misses | Real regression; check model tag, threshold constant, model server, the rejected-repairs list |
| Replay raises on a text missing from the vector cache | Pool, sidecar or model differ from the experiment's inputs |
| Library warning `No config is written for LocalIndex.` | Harmless; the index is in memory |

## Chapter 8: Shipping it - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; activation on 2026-09-14; 27 in-domain and 10 garbage items; restart crash observed 2026-09-23.

| Symptom | Root cause | Fix |
|---|---|---|
| Restart silently changes behaviour | Behavioural switch defaults to the new value, or is applied by a restart nobody planned | Default to the live behaviour, gate the new one behind an explicit variable, test the default |
| Gate stays green after a regression to the old level | Baseline constants not raised | Raise them in the same change as the improvement |
| Green health, unchanged numbers after "restart" | Orphan holds the port | Assert pid == listener pid; read the process environment |
| Service cannot restart | Start-up embedding path never exercised | Rehearse a cold restart; use one text per call |
| Raw task text on disk | Debug logging | Hash only, 0600, default off |

## Chapter 9: Failure cases at the shipped setting - Results (derived for this sheet from a replay, per case, production to shipped)

Conditions: Historical record supplied as of 2026-10-03; paired baseline-to-shipped replay derived offline on 2026-10-03; 27 in-domain items; request descriptions are paraphrases.

| Request (paraphrase) | Production | Shipped | Score | Reading |
|---|---|---|---|---|
| Build a three-statement financial model | escalated | exact (financial analyst) | 0.904 | gain |
| Build an idempotent CI/CD pipeline with canary rollout | escalated | exact (devops) | 0.784 | gain |
| Design a partitioned ETL with backfill and de-duplication | escalated | exact (data engineer) | 0.723 | gain |
| Plan moderated usability interviews | wrong (feedback synthesiser) | exact (UX researcher) | 0.858 | gain |
| Keyword gap analysis and on-page SEO | wrong (search-query analyst) | exact (SEO specialist) | 0.742 | gain |
| Redesign onboarding screens for fewer drop-offs | escalated | sibling (a whimsy-injection design persona) | 0.771 | counted as sibling by category; arguably wrong |
| Map the end-to-end user journey | wrong (feedback synthesiser) | sibling (a Chinese UX researcher persona; the expected one is a UX architect) | 0.769 | better, still not exact |
| Threat-model an OAuth flow | exact (threat-detection persona) | sibling (security engineer) | 0.766 | loss; the label is debatable |
| Triage and respond to an escalating support ticket | exact (support operations persona, score 0.682) | wrong (customer service persona) | 0.840 | loss; the label is contested (Chapter 2) |

## Chapter 10: Keeping the persona pool current (partly validated) - What we built (interfaces and rules)

Conditions: Historical record supplied as of 2026-10-03; partly validated sync evidence from 2026-09-16; shadow evaluation uses 27 in-domain and 10 garbage items; full delta uses scan version 1.

| Tier | Condition (all) | Action |
|---|---|---|
| 1: merge | only added roles; content scan safe; not a sensitive category; shadow exact and garbage rejected at least the baseline | merge, record |
| 2: merge and notify | modified existing roles; scan safe; not sensitive; shadow not lower | merge, record which roles changed |
| 3: human decides | any of: evaluation regressed; an upstream deletion of a role we route to; sensitive category (finance, legal) changed or removed; scan unsafe; apply failed and rolled back | create a card; if not handled in 14 days, create an overdue card (idempotent per week) |

## Chapter 10: Keeping the persona pool current (partly validated) - Results (hand-built deltas, run on 2026-09-16)

Conditions: Historical record supplied as of 2026-10-03; partly validated sync evidence from 2026-09-16; shadow evaluation uses 27 in-domain and 10 garbage items; full delta uses scan version 1.

| Run | Delta | Shadow exact / garbage | Baseline | Tiers |
|---|---|---|---|---|
| Minimal | 2 added, safe, non-sensitive | 14 / 10 | 14 / 10 | both tier 1 |
| Mixed | 5 staged files (2 added safe, 1 modified safe, 1 added sensitive, 1 modified unsafe) plus 2 removals of roles we route to | 15 / 10 | 14 / 10 | 2 tier 1, 1 tier 2, 4 tier 3 (sensitive, unsafe, 2 removed-routable) |
| Unavailable embedding endpoint | 2 added | none | 14 / 10 | all tier 3 with reason "eval unavailable", exit 1; the generator was not called |
| Full real delta (143 files: 105 added, 36 modified, 2 removed; this run used scan version 1) | everything at once | 13 / 8 | 14 / 10 | all 143 tier 3: 105 evaluation regression, 35 unsafe, 2 removed-routable, 1 sensitive |

## Chapter 10: Keeping the persona pool current (partly validated) - Pitfalls

Conditions: Historical record supplied as of 2026-10-03; partly validated sync evidence from 2026-09-16; shadow evaluation uses 27 in-domain and 10 garbage items; full delta uses scan version 1.

| Symptom | Root cause | Fix |
|---|---|---|
| Live pool has 400 personas, the experiments used 395 | Two reviewed merges after the A/B plus, judging by file times, three sample roles left behind while testing the merge step; the index was rebuilt | Hash the pool in every experiment; run merge tests against a copy; fail loudly when the pool no longer matches the evaluated hash |
| Unit test asserts exactly 395 personas | Pool size hard-coded | Compare to the index's declared total; assert against a fixture pool |
| Five index entries have title-style names with no category structure | Index rebuilt from files whose naming differs | Validate identifier shape at index build; the gate's `split("-")[1]` would raise on them |
| Start-up row count 2,793 | 2,783 rows plus 5 new personas x 2 rows | Track rows per persona as a metric |

## Additional recorded quantities

| Quantity | Recorded value and condition |
|---|---|
| Sidecar coverage | 395 personas; 335 with 5 phrasings, 60 with 4; 1,915 total; 0 banned-prefix starts; 1 text shared by two personas; derived offline on 2026-10-03 |
| English-identifier rows | 184 personas, 900 phrasings, median 42 characters, about 6 words, range 10 to 65 characters; same artifact audit |
| Chinese-identifier rows | 211 personas, 1,015 phrasings, median 13 characters; same artifact audit |
| Categories | 1 to 84 personas per identifier category; largest is specialized; same audit |
| Sync upstream changes | 2026-05-23 to 2026-09-16: English +70 / 28 modified / 0 removed; Chinese +35 / 8 modified / 2 removed |
| Content scan | Same 141 real files: version 1 flags 35, version 2 flags 10; 5 of 5 bare secret-prefix hits were ordinary words; all 12 URL-only hits were documentation links |
| Version 2 rule tally | 4 fetch-command, 6 credential-wording, 1 pip-install = 11 hits over 10 flagged files; presumed overlap, not resolved |
| Paired transitions | 9 exact unchanged; 3 escalated to exact; 3 escalated unchanged; 3 sibling unchanged; 3 wrong unchanged; 2 wrong to exact; 1 exact to sibling; 1 escalated to sibling; 1 wrong to sibling; 1 exact to wrong; 27 items, derived offline on 2026-10-03 |
| Historical admission helper | Shipped score distribution: baseline 0.50 returns 0.49; baseline 0.68 returns 0.68; derived offline on 2026-10-03 |

Conditions: supplemental values are source-record quantities; presumed overlap is an inference, and timings elsewhere are indicative observations without a latency distribution.
