# Chapter 8: Shipping it

### Problem

A calibrated trio is three coupled changes in three places: a data file, an environment switch and a constant in code. Applying only one of them is the worst outcome (Chapter 6). A restart can apply some of them without anyone choosing to.

### What we built

- **Environment-gated aggregation.** `PERSONA_ROUTER_AGG` selects `mean`, `max` or `sum`; unset or unknown values fall back to `mean` (the live baseline) instead of failing. Reason recorded in the code: the live process predated the committed `max` wiring, and an unattended restart would silently flip live behaviour. Tests lock the default, `max` selection, four invalid values, and `top_k == 10` in every case.
- **Activation steps (2026-09-14, supervised; reconstructed from the recorded recommended steps and the artifacts that confirm them: the sidecar file's modification time, the service-definition backup and the edited constants):** (1) write the 1,915 phrasings into the sidecar file (a backup of the previous file is dated 2026-09-14 08:38); (2) set the aggregation variable in the service definition; (3) change the default threshold constant from 0.68 to 0.72 with a comment recording why (max pushes garbage above 0.68; 0.72 is the saddle); (4) restart; (5) run the gate, expecting exact 14 (sibling 6, wrong 4, escalated 3) and garbage 10 of 10; (6) raise the gate constants from 11 and 9 to 14 and 10 in the same change.
- **The gate baseline rule.** The experiment write-up said it in so many words: if the constants are not raised, the gate never alarms on "better than it was", so a later retreat to 11 would still pass. The historical gate then used `MIN_EXACT = 14`, `MIN_GARBAGE_REJECT = 10`, with a comment saying that not raising them makes the gate mute. The public gate requires a measured synthetic baseline through `--baseline`; those historical constants are not defined in the public script.
- **Process identity after restart.** After every restart assert that the process manager's reported pid equals the pid listening on the sidecar's port, and inspect the process's real environment. An orphan holding the port gives a green health check, unchanged numbers, and a silently ineffective change. (Observed on 2026-09-06: two restarts left orphans and a 21-iteration crash loop. Observed again on 2026-09-14.)
- **Cold restart reality.** After the Chapter 5 incident the encoder is a one-text-per-call subclass; start-up is about 3 minutes, during which the service is down. Take a baseline of route scores before restarting production: we did not, and spent three rounds working out whether escalations right after the restart were normal.
- **Do not run full embeddings on the production model server for diagnosis.** The second full embedding run on 2026-09-23 crashed the runner again.

### The consumer check we skipped

On 2026-09-10 we recommended shipping the trio on the strength of one metric (11 to 14) without having looked at who calls the router and what is done with the result. Only a direct question led us to read the call site. What we found:

- The delegation tool calls the router for every sub-agent goal with an empty context; a returned persona's full text becomes the sub-agent's system prompt, so the sub-agent behaves as that specialist for the whole task.
- A wrong route is therefore silent and total: the caller cannot see it, and the sub-agent has no reason to doubt its role.
- At production on that date (09-10, measured with the gate): 7 of 27 requests were abandoned (fall back to generic), 20 matched but only 11 exactly; visible wrong routes at category level included a security-review request going to a legal-document-review persona, a front-end hydration fix going to a memory-backend architect persona, and an infrastructure-monitoring request going to a customer-response persona.

Rule recorded: do not recommend shipping any component before checking its consumer; a metric says how much better, the consumer says better for whom. Practical guidance recorded: treat auto-routing as a suggestion and pin the persona explicitly when it matters.

### Results

| Check | Before activation (production) | After activation (shipped) |
|---|---|---|
| Gate: exact / garbage rejected | 11 / 9 | 14 / 10 |
| Gate constants | 11 / 9 | 14 / 10 |
| Default threshold | 0.68 | 0.72 |
| Aggregation | mean | max |
| Sidecar rows | 0 | 1,915 over 395 personas |

### Failure signatures (strings and numbers to alert on)

| Signature | Meaning |
|---|---|
| Embedding server error `Post http://localhost:<runner-port>/tokenize: EOF` or `connect timed out` during index build or start-up | Runner crash on a multi-text request; service stays down and the supervisor loops |
| Every fixed probe escalates; top similarity near 0.44 and median near 0.06 where a healthy model gives 0.7 | Embedding model replaced (Chapter 3) |
| `/health` ok but the process manager's pid differs from the pid listening on the port | Orphan holds the port (Chapters 3 and 8) |
| Gate message `ALERT regression: in-domain exact X/27 ... [baseline exact>=14 garbage-rejected>=10]` with the first six misses | Real regression; check model tag, threshold constant, model server, the rejected-repairs list |
| Replay raises on a text missing from the vector cache | Pool, sidecar or model differ from the experiment's inputs |
| Library warning `No config is written for LocalIndex.` | Harmless; the index is in memory |

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| Restart silently changes behaviour | Behavioural switch defaults to the new value, or is applied by a restart nobody planned | Default to the live behaviour, gate the new one behind an explicit variable, test the default |
| Gate stays green after a regression to the old level | Baseline constants not raised | Raise them in the same change as the improvement |
| Green health, unchanged numbers after "restart" | Orphan holds the port | Assert pid == listener pid; read the process environment |
| Service cannot restart | Start-up embedding path never exercised | Rehearse a cold restart; use one text per call |
| Raw task text on disk | Debug logging | Hash only, 0600, default off |

### The rule

Ship coupled changes as one reviewed step, raise the gate in the same change, prove the new process is the one answering, and look at what the caller does with a wrong answer before you recommend it.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
