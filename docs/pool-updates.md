# Chapter 10: Keeping the persona pool current (partly validated)

**Partly validated design.** The real end-to-end merge, scheduled job and independent deep review were not recorded as completed. Hand-built acceptance cases and a real-delta shadow run are the evidence; this is not a finished deployment.

### Problem

The pool is a one-time snapshot of two third-party collections, and both keep changing. Between the snapshot (2026-05-23) and 2026-09-16 the role files changed by these counts (from the watcher's delta file, README files excluded): English upstream +70 added, 28 modified, 0 removed; Chinese upstream +35 added, 8 modified, 2 removed. Both removed Chinese roles still exist in our pool and are routable (the shadow verdict lists both as removed-but-routed). Persona files become system prompts, so an upstream edit is a prompt-injection channel as well as a recall question.

### What we built (interfaces and rules)

1. **Watcher.** Reads a source-marker file (repository, pinned commit, directories), diffs pinned to head through the hosting API, keeps only role markdown files, stages added and modified files, runs a content scan on each, writes a delta file. Exit 0 no change (prints one line, creates nothing), 2 changed, 1 error.
2. **Shadow evaluation.** Builds a shadow pool in a temporary directory (current pool plus staged added plus staged modified minus removed; same-name English/Chinese duplicates resolved by the original de-duplication rules), generates phrasings for the new roles (the Chapter 5 prompt, 5 per role), runs the 37-item set in-process with max aggregation at the current threshold, reads the gate baseline from the gate file (not hard-coded), writes a verdict. If the embedding endpoint is unreachable it fails closed: everything becomes "human decides".
3. **Apply.** Backs up the pool, index, sidecar and gate; creates cards for the human tier; with auto-apply on, copies staged files, rebuilds the index, appends phrasings, restarts the sidecar, asserts pid == listener pid (up to 60 s), runs the gate (without a pipe, so the exit code is real), and rolls back plus creates a card on any failure. Auto-apply defaults to off: then even passing tiers produce a "confirm only" card.
4. **Tiers.**

| Tier | Condition (all) | Action |
|---|---|---|
| 1: merge | only added roles; content scan safe; not a sensitive category; shadow exact and garbage rejected at least the baseline | merge, record |
| 2: merge and notify | modified existing roles; scan safe; not sensitive; shadow not lower | merge, record which roles changed |
| 3: human decides | any of: evaluation regressed; an upstream deletion of a role we route to; sensitive category (finance, legal) changed or removed; scan unsafe; apply failed and rolled back | create a card; if not handled in 14 days, create an overdue card (idempotent per week) |

Verdict priority per file: unsafe, then sensitive, then regression, then modified, then added.

5. **Content scan.** Version 1 flagged any bare `sk-`, any URL, any "environment variable" wording. On the 141 real upstream files (the 143-file delta below includes two removals) it flagged 35 as unsafe: 5 of 5 bare `sk-` hits were words like "risk-adjusted", all 12 URL-only hits were documentation links. Version 2 requires secret shapes with a word boundary and minimum length (`sk-` plus 20 characters, `ghp_` plus 20, `AKIA` plus 12, PEM private-key header), counts a URL only on the same line as a fetch-and-execute command, requires read/export verbs for environment-variable wording, and keeps English and Chinese exfiltration/credential wording rules. On the same 141 files version 2 flags 10; the recorded tally by rule is 4 fetch-command, 6 credential-wording and 1 pip-install, which sums to 11, so presumably one file trips two rules. The remaining 10 were judged worth a human look (two ask for a local POST to a publishing service). A planted fake role containing a fetch-and-pipe-to-shell line is still flagged.

### Results (hand-built deltas, run on 2026-09-16)

| Run | Delta | Shadow exact / garbage | Baseline | Tiers |
|---|---|---|---|---|
| Minimal | 2 added, safe, non-sensitive | 14 / 10 | 14 / 10 | both tier 1 |
| Mixed | 5 staged files (2 added safe, 1 modified safe, 1 added sensitive, 1 modified unsafe) plus 2 removals of roles we route to | 15 / 10 | 14 / 10 | 2 tier 1, 1 tier 2, 4 tier 3 (sensitive, unsafe, 2 removed-routable) |
| Unavailable embedding endpoint | 2 added | none | 14 / 10 | all tier 3 with reason "eval unavailable", exit 1; the generator was not called |
| Full real delta (143 files: 105 added, 36 modified, 2 removed; this run used scan version 1) | everything at once | 13 / 8 | 14 / 10 | all 143 tier 3: 105 evaluation regression, 35 unsafe, 2 removed-routable, 1 sensitive |

Observations: (1) adding about a quarter more personas at once lowered both exact (14 to 13) and garbage rejected (10 to 8) with no recalibration; consistent with the mechanism of Chapter 6 (more rows raise max-aggregated garbage scores) but not tested separately; the generated phrasings for the new roles also differ in provenance from the original ones. (2) The evaluation scores the bundle, so one regressing bundle puts every file in tier 3; there is no bisection. (3) Small deltas passed and merged tier 1 in the dry runs. Dry-run mode was verified read-only (verdict file mtime unchanged); production pid and sidecar file mtime did not change across three runs. Apply was exercised with hand-built verdicts: the card-only path, a forced failure that rolled back and left a rollback record, and the overdue-card logic with a faked clock across three week buckets (create, do not duplicate, create new).

### What did not work

- A single bundled verdict for a large delta (above).
- Content-scan v1 (35 of 141 false alarms would have buried the human tier in noise).
- The first 90-turn budget for the three scripts: they were written but untested; the verification pass found four truncated f-strings in the apply script (idempotency keys) that compiled but would have collided. Lesson recorded: give "write, then really run the acceptance cases" tasks a bigger budget.

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| Live pool has 400 personas, the experiments used 395 | Two reviewed merges after the A/B plus, judging by file times, three sample roles left behind while testing the merge step; the index was rebuilt | Hash the pool in every experiment; run merge tests against a copy; fail loudly when the pool no longer matches the evaluated hash |
| Unit test asserts exactly 395 personas | Pool size hard-coded | Compare to the index's declared total; assert against a fixture pool |
| Five index entries have title-style names with no category structure | Index rebuilt from files whose naming differs | Validate identifier shape at index build; the gate's `split("-")[1]` would raise on them |
| Start-up row count 2,793 | 2,783 rows plus 5 new personas x 2 rows | Track rows per persona as a metric |

### The rule

Treat a pool update as a model change: evaluate the whole system before and after, keep the baseline that decides "no worse" in a file the apply step reads, make the unsafe and sensitive paths human-only, and never test a merge step against the live pool.

## Public implementation boundary

The shipped watcher consumes local snapshot fixtures in place of the hosting API. The shadow tool preserves tier priority and accepts injected evaluation and generation callbacks. Its command-line demo uses labelled mock scores. The apply tool demonstrates dry-run, confirmation, copy-only apply, process-identity checks and rollback through callbacks. Live hosting, pool de-duplication, index rebuilding, scheduling, external cards and service-manager wiring are not packaged as a finished integration. Generator URL and model are configurable; no local generator is called by the demo.

The content scanner is adapted from the supplied rules. It also flags standalone fetch commands and package-install commands; this conservative executable behavior is broader than the prose description of URL-plus-execution matching. The recorded scan tallies remain unchanged.


[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
