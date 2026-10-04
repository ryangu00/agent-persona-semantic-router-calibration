# Chapter 2: Measuring a router with 37 blind items

### Problem

We needed a number that would move when routing got better or worse, that no tuning step had seen, and that a script could check on every change.

### What we built

**The set.** `EVAL_SET` has 27 in-domain items and 10 garbage items. Its own note says: hand-authored blind, terse bot-style delegation goals from domain knowledge plus persona names, written without reading the persona descriptions or the sidecar (the anti-Goodhart decorrelation control); used to measure before and after, not to calibrate per persona.

| Property | Value |
|---|---|
| In-domain items | 27, 6 to 11 words (49 to 67 characters) each, all English |
| Expected-persona categories | engineering 9, finance 4, design 3, marketing 3, testing 3, game development 2, support 2, product 1 (8 categories out of roughly two dozen) |
| Garbage items | 10, 7 to 36 characters: 2 keyboard-mash strings, 2 repeated-character strings, 1 digit string, 4 short off-topic consumer requests, 1 greeting |
| Accept sets | 12 of the 27 items list extra acceptable personas: 11 are the Chinese-language twin of the expected English persona, plus one role synonym (an incident-response persona for a reliability item). 15 items have none (strict match) |

The 37 private texts are withheld to preserve their blindness. The public fixtures demonstrate the structure with independently authored synthetic requests.

**Metrics** (all computed per run; the gate and the harness use the same definitions):

| Metric | Definition |
|---|---|
| exact | routed persona equals the expected persona |
| sibling | routed persona has the same category (second segment of the identifier) but is not the expected one; a Chinese twin counts as sibling unless it is in the accept set |
| wrong | routed to a different category |
| escalated | no persona returned |
| accept-aware hit | routed persona is in {expected} plus the accept set |
| garbage rejected | garbage input returned no persona |
| precision | exact / (exact + sibling + wrong); escalations are excluded from the denominator |

By-source reporting (substring / keyword / semantic / none) exists in the evaluation helper because a tier that earns hits must be separable from a tier that earns errors.

**The historical regression gate.** A small script posted all 37 items to the running sidecar and exited non-zero (with the first six misses printed) if `exact < MIN_EXACT` or `garbage rejected < MIN_GARBAGE_REJECT`, or if the health endpoint was not ok. Its alert text listed the four things to check first: whether the embedding tag had been replaced, whether the threshold constant was edited, whether the model server was healthy, and the list of already-rejected repairs. "Retreat is the signal": the two baseline numbers are measurements, not targets. The public gate instead requires a measured synthetic baseline through `--baseline`; it does not define those historical constants.

### Procedure as actually run

1. Author the set blind (before reading persona text). 2. Add accept sets later for twins (a label fix made in June, before the 06-16 offline measure, so near-synonyms are counted fairly). 3. Run it as a gate after every change. 4. For experiments, replay it in-process (Chapter 5) so production is never touched.

### Results

What 27 items can resolve (derived offline on 2026-10-03):

| Quantity | Value |
|---|---|
| One in-domain item | 3.7 percentage points |
| Exact, production before | 11 of 27 = 0.407, Wilson 95% interval 0.245 to 0.593 |
| Exact, shipped setting | 14 of 27 = 0.519, Wilson 95% interval 0.340 to 0.693 |
| Paired changes, production to shipped | 5 items gained exact (3 escalated to exact, 2 wrong to exact), 2 lost exact |
| Two-sided exact sign test on 5 versus 2 | p = 0.453 |
| Same, if the contested label below is replaced | 6 gained versus 1 lost, p = 0.125 |
| Garbage rejection 9 of 10 versus 10 of 10 | one item; Wilson intervals 0.596 to 0.982 and 0.722 to 1.0 |

The embedding is deterministic: three independent runs of the full experiment gave identical numbers (recorded), and an offline replay on 2026-10-03 from the recorded vector cache reproduced all four configurations digit for digit (derived). So the numbers are exactly reproducible; they are not statistically significant estimates of live traffic.

**A contested label.** One item's expected persona (a support-ticket triage request, expected: a support-operations persona) became a "new wrong route" under the shipped setting because the router now returns a customer-service persona at score 0.840. A blind re-check (one judgement, stated confidence 90%) re-read both persona definitions and concluded the label was wrong: the customer-service persona handles a single escalating ticket (de-escalation, complaint handling, escalation protocol), the expected one builds support operations (SLA configuration, analytics, knowledge base). The evaluation set was not changed (anti-Goodhart and single-judge), so every number in this book uses the original label. If the label were replaced, production would have exact 10 (it matched the old label at score 0.682, just above the 0.68 threshold) and the shipped setting exact 15.

**Lexical-overlap audit (derived offline on 2026-10-03, numbers only).** The set was blind to the sidecar, but the sidecar was generated from persona descriptions, and max aggregation is sensitive to near-duplicates. For each of the 27 prompts, the best-matching phrasing in the whole sidecar:

| Statistic | Value |
|---|---|
| Best-phrasing cosine, all 27 items | min 0.606, mean 0.762, max 0.960 |
| Best phrasing belongs to the expected persona | 17 of 27 |
| Items with token overlap (Jaccard over non-stopword tokens) at least 0.4 with some phrasing | 5 of 27 (values 0.43, 0.44, 0.50, 0.62, 0.83) |
| Of the 5 items that gained exactness under the shipped setting | 2 have overlap at least 0.4 (0.44, 0.50); 3 have 0.33 or less (0.17 to 0.33) |

So some of the gain plausibly comes from the generator writing phrasings that resemble common task wording, and some does not. A held-out second set authored after the sidecar existed was never built (open question).

### What did not work

- Treating the set as a calibration target. It was meant to measure, but the threshold, aggregation and sidecar were all swept against the same 37 items; the shipped point is therefore selected on its own test set.
- Measuring only exact: sibling and wrong behave very differently for the caller (a sibling is often an acceptable specialist; a wrong route is not), and exact alone hides a precision collapse (Chapter 6).

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| "Wrong" routes that look reasonable | Category-level sibling and twin handling in the metric | Report exact, sibling, wrong, escalated separately; keep accept sets minimal |
| A hit counted although the router escalated | Accept-set logic applied before the escalate check | `hit = (not escalate) and persona in accept`; tests cover unlisted personas counting as misses |
| Gate crashes on a persona identifier without a hyphen | Category is derived with `identifier.split("-")[1]` | Derive the category from the index record, not the identifier (latent: five identifiers added later have no such structure; see Chapter 10) |

### The rule

Report every metric of a router per tier and per outcome class, say how many items one flip moves, and replay deterministically; never claim significance you do not have.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
