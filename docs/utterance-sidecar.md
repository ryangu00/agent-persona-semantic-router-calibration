# Chapter 5: The utterance sidecar

### Problem

A persona is described by a title and a paragraph, while a task is a terse imperative request ("write contract tests for the payments API"). The two sit in different regions of embedding space; the persona's own description is not what a user would type. The sidecar attaches 4 to 5 short task phrasings per persona so a task has something close to match.

### What we built

**Schema.** One JSON object: `{persona_name: ["phrasing", ...]}`; a missing or empty file means no enrichment (pre-sidecar behaviour, regression-safe). The original generated artifact also carried per-persona keywords (`{persona: {keywords, utterances}}`).

**Generation recipe** (the form used in the sync pipeline; the original batch used a similar approach with a local model whose name was not recorded). Prompt per persona:

```
Role: {title}
Description: {description}

Write N short task requests a user would send to ask this specialist for help.
One per line, terse imperative English, no numbering, no quotes, max 15 words each.
Output only the N lines.
```

Parameters: temperature 0.6, 256 max new tokens, N = 5. Parse rules: strip leading bullets and numbering, drop empty lines and lines over 160 characters, drop preamble lines ("here are", "sure", "role:", "description:"), de-duplicate, keep the first N. A candidate model that returns HTTP 500 or empty output falls back to the next candidate; the pipeline stops (all files become "needs a human") if no embedding endpoint is reachable.

**Quality filters.** (1) Content-free prefixes rejected: "help me", "i need", "i want", "do a task", "complete this", "<title>". (2) Garbage-closeness: embed all candidates and a set of garbage exemplars; reject a candidate whose maximum cosine to any garbage vector exceeds `1 - margin`; garbage vectors identical to the candidate are skipped (a degenerate garbage set must not reject by self-identity). (3) De-duplication.

**Artifact statistics (derived offline on 2026-10-03).** 395 personas; 335 have 5 phrasings and 60 have 4 (1,915 total); every persona covered; 0 phrasings start with a banned prefix; 1 phrasing text is shared by two personas. English-identifier personas (184): 900 phrasings, median 42 characters (about 6 words, 10 to 65 characters); Chinese-identifier personas (211): 1,015 phrasings in Chinese, median 13 characters. Personas per category (by the identifier's category segment) range from 1 to 84 (the largest category is the catch-all "specialized" group).

### Procedure as actually run (embedding channel)

*First attempt (2026-09-06).* Building the experimental router through the library embeds all rows in one call (the notes of the time say 2,310 texts, counting one row per persona; the real row count was 2,783 because each persona contributes two or three structural rows). The local embedding server's runner crashed three times in a row with `Post http://localhost:<runner-port>/tokenize: EOF` and `connect timed out`. Batches of 200 did not help: the runner, not the request size, was dying. The 395-row baseline always worked.

*Working path (2026-09-08 and 09-09).* Never build the index through the library. Instead: (1) collect every unique text; (2) embed them with direct `POST /api/embed` calls, batch 64, up to 6 retries with exponential backoff (0.5 s x 2^attempt), 0.25 s pause between batches; (3) persist an `npz` cache (keys plus a float matrix) after every batch so a crash resumes; (4) score in-process with a cache-backed encoder. 2,819 unique texts took 266 s with zero crashes, on an Apple-silicon Mac (indicative).

*Fidelity design.* The experiment must run the production code path, not a lookalike. The cache-backed encoder is a real subclass of the library's dense-encoder base class (the library validates the type with pydantic, so duck-typing is rejected); only the vector source is replaced. Utterances are injected in memory by monkeypatching the loader functions, so production files are only read. The keyword tier was kept at its production value for every configuration. A dimension probe (the library embeds the word "test" once) needs a special case when the cache is the only source. Production was never touched: the sidecar file stayed an empty object, the live port was never queried, and the gate after the experiment gave the same numbers as before.

*Restart-time crash (2026-09-23, observed later).* At start-up the library again embeds all rows in one call (2,793 rows by then). With Ollama 0.30.10 the runner crashed at tokenize time when a request carried five or more texts (one text: fine; five: crash). The sidecar could not start and its supervisor restarted it in a loop; it had only been alive because it had never been restarted. Fix: an encoder subclass that sends one text per call whenever more than one text is passed; start-up then takes about 3 minutes (2,793 sequential calls on an Apple-silicon Mac, indicative). Note the two observations differ: batches of 64 through the direct endpoint worked on 09-09; a batch of 5 through the library path crashed on 09-23. We did not isolate whether the difference is the Ollama version, the request path or runner state.

### Results

**Small-sample A/B (2026-09-08).** Only the 37 personas that appear as expected or accepted personas received phrasings (cap 3 per persona = 111 phrasings; rows 868 to 979); production configuration (mean, 0.68, keyword tier as is). Baseline reproduced production digit for digit before the experiment was believed.

| Group | exact | sibling | wrong | escalated | garbage rejected | accept-aware hits | precision |
|---|---|---|---|---|---|---|---|
| Baseline (no phrasings) | 11 | 3 | 6 | 7 | 9 | 12 | 0.550 |
| +111 phrasings, 37 personas | 12 | 6 | 5 | 4 | 9 | 15 | 0.522 |

Eight of 27 items changed. Gains: two escalated items became exact (a financial-model request and a launch-blog-post request), a third escalated item became an accepted Chinese twin (the CI/CD request), and a wrong route became exact (usability research). A twin flip (reliability item exact to its Chinese twin) is semantically equivalent; one real regression (a threat-modelling request moved from a threat-detection persona to a security-engineer persona; that persona's phrasings are semantically closer and the label is debatable). Garbage rejected stayed 9 of 10 (the miss was the keyboard-mash-with-digits string).

Verdict recorded then: mildly positive, not enough to ship the full sidecar, because a 37-persona change cannot show what happens when all 395 route centres move, the threshold was calibrated on the old distribution, and the aggregation question (mean or max) was open.

**Per-source effect of the full sidecar (derived).** At threshold 0.68 with max aggregation the 15 semantic-tier items go from 4 to 8 exact; the 12 keyword-tier items do not move.

### What did not work

- Building the index through the library (crash) and batching it in 200s (crash).
- An instance-level patch of the encoder's `__call__` to chunk requests: Python resolves dunder methods on the type, so the patch was silently bypassed and the index still crashed; a result was reported through the broken method and subsequently flagged as unreproducible. Patch `type(enc).__call__` instead.
- A first sweep harness rebuilt the baseline router while the environment still said max aggregation and sidecar on; the baseline sweep rows duplicated the experimental rows and polluted the comparison. Isolate configuration construction from sweeps and reuse the router object that was built for each configuration.
- Trusting the small sample to approve the full sidecar.

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| Embedding server runner dies with tokenize EOF | Large or multi-text requests through the library's own sync path | Direct batched `/api/embed` with retries, or one text per call; cache vectors on disk |
| Experiment passes a type check but scores nothing | Duck-typed encoder rejected by pydantic | Subclass the library's dense encoder |
| Experimental numbers do not match live | Different tier state, threshold or model tag | First reproduce the live gate numbers in-process; only then trust the other arms |
| "It restarts fine" | It never restarted; start-up path untested | Run a cold restart rehearsal for any service that has been up for weeks |

### The rule

Attach the phrasings, but never evaluate them on the library's own index build, and never believe an experimental arm until the baseline arm reproduces production exactly.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
