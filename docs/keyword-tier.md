# Chapter 4: The keyword tier: no score, twelve decisions, three rejected fixes

### Problem

On the 27 in-domain items the keyword tier (second in the order) decides 12 before the semantic tier is consulted. It returns no score, so there is nothing to threshold, and 5 of its 12 decisions are not exact.

### What we built

Per persona, a set of signal tokens: name parts and title tokens (weight 3), keywords (weight 1), injected curated keywords (weight 3). Tokens: English words of at least 3 characters or a curated list of short technical acronyms (ci, cd, qa, ml, ui, ux, db, ...), stop-words removed, slash-joined runs (`ci/cd`) contributing the joined form and each side; Chinese text as character bigrams plus whole runs of 2 to 4 characters. Score per persona = 3 x (query tokens in name/title/injected) + 1 x (query tokens only in keywords); each query token counts once at its highest weight (a token in both name and keywords must not score 3+1). The tier fires only if the best score is at least 3 and strictly greater than the runner-up (ties escalate to the next tier).

Two repairs made in June, both principled and measured against a control: (a) drop name tokens whose document frequency across personas' name sets exceeds 8 (27 tokens dropped on the real index, such as `engineer`, `specialist`, `architect`, `development`; control: of 285 keyword-silenced pairs all routed fine through substring or semantic); (b) per-token maximum scoring instead of summing (the root cause of a security request routing to a QA persona was not generic-token pollution but a token scoring 3+1=4 by sitting in both name and keywords). Injected-keyword lint drops stop-words, one-character terms, terms injected for two or more personas, and terms that whole-token-hit more than 8 personas' title/description sets.

### Results

Tier contribution on the 27 in-domain items (derived offline on 2026-10-03 from the recorded per-case rows):

| Source | Items | exact | sibling | wrong |
|---|---|---|---|---|
| keyword (all configurations, unchanged by every experiment) | 12 | 7 | 3 | 2 |
| semantic, production (mean, no sidecar, 0.68) | 15 | 4 | 0 | 4 (plus 7 escalated) |
| semantic, shipped (max, sidecar, 0.72) | 15 | 7 | 3 | 2 (plus 3 escalated) |

On garbage the keyword tier never fired (0 of 10), so garbage is purely a semantic-tier concern. At the start of the sidecar work the semantic tier alone produced only 4 of 27 exact (the cell "B, semantic only" below).

Three repairs of one keyword failure (a Chinese infrastructure request whose three bigrams hit a persona name, 3 bigrams x weight 3 = 9, short-circuiting the semantic tier), measured on 2026-09-06, columns exact / sibling / wrong / escalated (sum 27), garbage rejected 9 of 10 for all:

| Variant | exact | sibling | wrong | escalated | Verdict |
|---|---|---|---|---|---|
| A: current (keyword hit short-circuits) | 11 | 3 | 6 | 7 | best, kept |
| Coverage gate, fraction at least 0.5 | 8 | 2 | 4 | 13 | net loss; correct hits also cut |
| Coverage gate, fraction 0.6 to 0.8 | 5 | 1 | 4 | 17 | worse |
| B: delete the keyword tier (semantic only) | 4 | 1 | 4 | 18 | exact cut by more than half |
| C: semantic review when tiers disagree | 10 | 4 | 6 | 7 | no gain, an extra embedding call |

Two further keyword-tier failures remain in the shipped setting and were not diagnosed: an endpoint security-review request routes to a legal-document-review persona, and a front-end hydration/memory-leak request routes to a memory-backend architect persona. A game-design request lands on an engine-specific gameplay scripter (sibling).

### What did not work

- All three obvious repairs above. The keyword tier contributes most of the correct hits; weakening it costs more than it saves.
- Tuning keywords at scale: 2,865 injected keywords were generated for all 395 personas, but only one curated seed entry (a tax persona, 8 terms) ever shipped; an earlier offline run reported keyword-only recall 0.444 to 0.481 (recorded, not re-run). Its effect at full scale was not measured separately in the recorded evidence.

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| A request is routed to the wrong persona by a word it merely contains | Bigram or token overlap with a persona name, weight 3, no abstain path | Generic-token filter, strict-winner rule; accept that some confident errors remain |
| A short acronym never fires | Token length gate (3) | Curated allow-list of acronyms, not a lower global gate |
| Tie between two personas | Per-token max scoring makes ties common | Ties escalate (strict-winner clause) |

### The rule

A tier with no confidence signal cannot be calibrated; measure it by source, separately from the tier you are tuning, and expect its errors to be confident.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
