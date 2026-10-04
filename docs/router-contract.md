# Chapter 1: The router and its contract

### Problem

An agent runtime can seed a sub-agent with a specialist persona: a markdown file describing a role, workflow and deliverables, used as the sub-agent's system prompt. With 395 candidate personas nobody (and no calling agent) reliably remembers which one fits. The requirements we set: choose one persona per task, locally, with no LLM call on the hot path; return "no persona" when unsure so the caller falls back to a generic sub-agent; never block the caller.

### What we built

**Engine choice.** We adopted an existing open-source semantic router ([aurelio-labs/semantic-router](https://github.com/aurelio-labs/semantic-router) 0.1.15, MIT) after a prior-art check: a model-routing project routes models, not personas, and a retrieval framework puts an LLM on the hot path. License was checked twice: through the hosting API and the license file bundled in the installed distribution. We wrote only an adapter and glue; no routing math is ours and no library source is modified.

**Three tiers, in order** (the hybrid router):

1. *Substring pass* (deterministic, no embedding). Trusted only on a high-confidence literal hit: the query is exactly a category slug, or appears verbatim inside the matched persona's name or title. Returns score 1.0, source `substring`.
2. *Keyword pass* on the whole query (Chapter 4). Fires only if the best persona has weight at least 3 and strictly beats the runner-up. Returns no score, source `keyword`.
3. *Semantic pass* on the task's lead. One embedding call, cosine against every row, retrieve the global top 10 rows, group by persona, aggregate (mean or max), keep personas whose aggregate meets the threshold, return best plus runner-up, source `semantic`. Below threshold: `persona=None`, `escalate=True`.

**Lead truncation.** Real delegations arrive as elaborated prompts ("do X. Requirements: 1... 2..."); the requirement list dilutes the topic embedding below threshold. A measured failure: the full prompt escalated while its first 60 characters routed correctly. The semantic and substring passes therefore use only the first paragraph, capped at 200 characters; the keyword pass sees the full text. All evaluation prompts are shorter than 200 characters, so this rule is not exercised by the evaluation set (open question).

**Row construction.** For each persona the rows are, in order, title, description, expanded description (quotes stripped, de-duplicated), then the sidecar phrasings (stripped, de-duplicated, empties skipped). A persona never has zero rows (fallback: its name). With no sidecar the behaviour is byte-identical to the pre-sidecar router (a test asserts it).

**Semantic scoring rule (verified).** The library's behaviour, in the form we reimplemented and verified:

```python
def route_semantic(query_vec, row_vecs, row_owner, agg, threshold, top_k=10):
    sims = row_vecs @ query_vec                      # all vectors L2-normalised
    top = np.argsort(-sims)[:top_k]                  # GLOBAL top-k rows, any persona
    by_persona = defaultdict(list)
    for i in top:
        by_persona[row_owner[i]].append(sims[i])     # only rows that made the top-k
    score = {p: (mean(v) if agg == "mean" else max(v)) for p, v in by_persona.items()}
    best = max(score, key=score.get)
    return (best, score[best]) if score[best] >= threshold else (None, score[best])
```

Verification (derived offline on 2026-10-03): this reference function over the recorded vectors reproduced the library's garbage-rejection count in all 164 cells (4 configurations x 41 thresholds) and the persona and score of all 15 evaluation cases that the hybrid router sends to the semantic tier, with zero mismatches. Library defaults are `aggregation="mean"` and `top_k=5`; we pass `top_k=10`. Note that mean is taken only over a persona's rows that landed in the global top 10, which is what makes dilution depend on the neighbourhood and not on the persona's total row count.

**Sidecar and consumer contract.**

- A stdlib HTTP server on localhost builds the hybrid router once at start-up (all embeddings), then serves `GET /health` -> `{"status":"ok","routes":N}` and `POST /route {"task": "..."}` -> `{"persona","score","escalate","source","runner_up","path"}`.
- The delegation tool calls it with a 2-second timeout. `escalate`, a missing persona or path, a timeout, a bad response, an unreadable persona file: all return "no persona" and the delegation proceeds exactly as before (fail-open). An explicit caller-supplied context always beats auto-routing. The persona path must resolve under the pool root (path-escape check). Knobs: a global on/off, a per-call opt-out, a per-turn cap (5) on persona spawns.
- The sidecar runs in its own virtual environment so the agent runtime's environment is never touched; removing the directory fully reverts the feature.
- Request log: default OFF; when on, one line per decision with a salted SHA-256 prefix of the task, never the task text, file mode 0600, never under a temp directory.

### Procedure as actually run (first measurements, 2026-06-15)

Probe of ten in-domain tasks and four out-of-domain inputs through the production router with Qwen3-Embedding 0.6B:

| Observation | Value |
|---|---|
| In-domain, sensible persona | 10 of 10 |
| In-domain score band | 0.54 to 0.78 |
| Out-of-domain escalated (empty, small talk, off-topic question, random tokens) | 3 of 4 at the final threshold 0.50 with an empty-input short-circuit before embedding; the recorded earlier state (threshold 0.45, no short-circuit) leaked 3 of 4 |
| Random-token garbage | about 0.63, overlapping the low end of the in-domain band |
| Build over 395 personas | about 11 s (embedding all rows once) |
| One query | one local embedding call plus one cosine over the matrix (no latency distribution was recorded) |

### What did not work

- A single global threshold cannot cleanly reject random tokens when the in-domain band starts at 0.54: the first documented limitation. The router was declared "a narrowing aid, not a gatekeeper".
- A rewording sensitivity was measured: "high-availability Kubernetes cluster" routed to the reliability-engineering persona (good), "fault-tolerant Kubernetes platform" routed to an enterprise-CRM architect persona at 0.636.

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| Install "works" but `OllamaEncoder` is missing | System Python 3.14 resolves an ancient `semantic-router` 0.0.20 | Use a Python 3.11 virtual environment and pin `semantic-router==0.1.15` |
| Enrichment had no effect in a design draft | The router constructor was never passed `aggregation` and `top_k`; every sidecar experiment would have been silently inert | Pass both explicitly; a test mocks the library class and asserts the kwargs (`aggregation`, `top_k == 10`) |
| Raw task text ended up in a world-readable temp file | An early debug log wrote the first 60 characters of every task | Salted-hash-only log, mode 0600, off by default, ignored by version control and sync (a test asserts raw text never appears) |

### The rule

Decide the cost of a wrong route and the fallback for "no route" before choosing a score rule; put the abstain decision in the router and the fail-open fallback in the caller.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
