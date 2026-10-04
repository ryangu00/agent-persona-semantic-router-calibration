# Pitfalls: symptom, cause, repair

Each entry is a recorded failure or explicitly identified latent problem. Repairs are scoped to that evidence; the synthetic tests check mechanisms, not the historical deployment.

## Chapter 1: The router and its contract

| Symptom | Root cause | Fix |
|---|---|---|
| Install "works" but `OllamaEncoder` is missing | System Python 3.14 resolves an ancient `semantic-router` 0.0.20 | Use a Python 3.11 virtual environment and pin `semantic-router==0.1.15` |
| Enrichment had no effect in a design draft | The router constructor was never passed `aggregation` and `top_k`; every sidecar experiment would have been silently inert | Pass both explicitly; a test mocks the library class and asserts the kwargs (`aggregation`, `top_k == 10`) |
| Raw task text ended up in a world-readable temp file | An early debug log wrote the first 60 characters of every task | Salted-hash-only log, mode 0600, off by default, ignored by version control and sync (a test asserts raw text never appears) |
## Chapter 2: Measuring a router with 37 blind items

| Symptom | Root cause | Fix |
|---|---|---|
| "Wrong" routes that look reasonable | Category-level sibling and twin handling in the metric | Report exact, sibling, wrong, escalated separately; keep accept sets minimal |
| A hit counted although the router escalated | Accept-set logic applied before the escalate check | `hit = (not escalate) and persona in accept`; tests cover unlisted personas counting as misses |
| Gate crashes on a persona identifier without a hyphen | Category is derived with `identifier.split("-")[1]` | Derive the category from the index record, not the identifier (latent: five identifiers added later have no such structure; see Chapter 10) |
## Chapter 3: A router that died silently for 19 days

| Symptom | Root cause | Fix |
|---|---|---|
| Health green, every request escalates | Fail-open caller plus a health check that does not exercise routing | Probe with fixed tasks that must route, and alert on the non-escalation rate |
| Same tag, different model | Shared mutable tag; the pull/tag operation replaces content silently | Pin by digest or by a private tag; check a fixed probe pair's cosine against a recorded reference (the stock-versus-fine-tuned cosine for one input ranges 0.74 to 0.96, so test the expected reference, not a loose band) |
| Orphan process holds the port after restart | `kickstart -k` raced the old instance; label disabled | After every restart assert that the process manager's pid equals the pid listening on the port, and inspect the process's own environment |
| Threshold "calibrated" but unusable | Calibrated on one embedding distribution; model changed | Store the model digest next to the threshold; recalibrate when it changes |
## Chapter 4: The keyword tier: no score, twelve decisions, three rejected fixes

| Symptom | Root cause | Fix |
|---|---|---|
| A request is routed to the wrong persona by a word it merely contains | Bigram or token overlap with a persona name, weight 3, no abstain path | Generic-token filter, strict-winner rule; accept that some confident errors remain |
| A short acronym never fires | Token length gate (3) | Curated allow-list of acronyms, not a lower global gate |
| Tie between two personas | Per-token max scoring makes ties common | Ties escalate (strict-winner clause) |
## Chapter 5: The utterance sidecar

| Symptom | Root cause | Fix |
|---|---|---|
| Embedding server runner dies with tokenize EOF | Large or multi-text requests through the library's own sync path | Direct batched `/api/embed` with retries, or one text per call; cache vectors on disk |
| Experiment passes a type check but scores nothing | Duck-typed encoder rejected by pydantic | Subclass the library's dense encoder |
| Experimental numbers do not match live | Different tier state, threshold or model tag | First reproduce the live gate numbers in-process; only then trust the other arms |
| "It restarts fine" | It never restarted; start-up path untested | Run a cold restart rehearsal for any service that has been up for weeks |
## Chapter 6: Mean versus max, and why the threshold moves with them

| Symptom | Root cause | Fix |
|---|---|---|
| Recall barely moves after adding rows | Mean over the top-10 pool dilutes | Use max, or judge the aggregation first |
| Garbage suddenly routes after a "recall improvement" | Max over more rows raises every input's best score | Re-sweep the threshold for the new configuration; check the highest garbage score against it |
| Comparisons that mix arms | Baseline with one aggregation, experiment with another | Same-aggregation or same-sidecar comparisons only (the 2x2 exists for this) |
## Chapter 8: Shipping it

| Symptom | Root cause | Fix |
|---|---|---|
| Restart silently changes behaviour | Behavioural switch defaults to the new value, or is applied by a restart nobody planned | Default to the live behaviour, gate the new one behind an explicit variable, test the default |
| Gate stays green after a regression to the old level | Baseline constants not raised | Raise them in the same change as the improvement |
| Green health, unchanged numbers after "restart" | Orphan holds the port | Assert pid == listener pid; read the process environment |
| Service cannot restart | Start-up embedding path never exercised | Rehearse a cold restart; use one text per call |
| Raw task text on disk | Debug logging | Hash only, 0600, default off |
## Chapter 10: Keeping the persona pool current (partly validated)

| Symptom | Root cause | Fix |
|---|---|---|
| Live pool has 400 personas, the experiments used 395 | Two reviewed merges after the A/B plus, judging by file times, three sample roles left behind while testing the merge step; the index was rebuilt | Hash the pool in every experiment; run merge tests against a copy; fail loudly when the pool no longer matches the evaluated hash |
| Unit test asserts exactly 395 personas | Pool size hard-coded | Compare to the index's declared total; assert against a fixture pool |
| Five index entries have title-style names with no category structure | Index rebuilt from files whose naming differs | Validate identifier shape at index build; the gate's `split("-")[1]` would raise on them |
| Start-up row count 2,793 | 2,783 rows plus 5 new personas x 2 rows | Track rows per persona as a metric |

## Why these checks matter

A healthy listener says nothing about semantic discrimination. Probe known-good routes with the pinned model, record their scores, and compare the manager process with the listening process after restarting. A fail-open caller otherwise conceals a dead semantic tier.

The two embedding crashes remain separate observations. Direct batches of 64 worked on 2026-09-09; requests carrying 5 texts through the library path crashed on 2026-09-23 with Ollama 0.30.10. Version, path and runner state were not isolated. One-text calls repaired restart, with about 3 minutes of startup downtime.

A cache miss is evidence of changed inputs, not permission to query a live endpoint during replay. Freeze the pool, phrasings, evaluation and model together. Preserve the keyword tier across arms and reuse each arm's built router during its sweep.

A strict winner still has no calibrated probability. Report keyword mistakes separately. Category siblings can also be unsuitable specialists, so neither sibling counts nor high cosine replace reading the changed cases.

A green old gate cannot detect a retreat from an improvement. Raise its baseline in the release that improves the measured result, and test its failure path. Do not derive category names by splitting identifiers.
