# Chapter 3: A router that died silently for 19 days

### Problem

On 2026-09-06 a manual check found that the semantic tier had not returned a persona in 19 days. Nothing alerted: the health endpoint was green, the process was alive, and the caller's fail-open path quietly used a generic sub-agent.

### What happened

- On 2026-08-18 a fine-tuned embedding model was deployed under the stock tag `qwen3-embedding:0.6b` for another consumer on the same machine (the deliberate "fine-tune hides under the stock name" pattern; see [training-embedding-finetune](https://github.com/ryangu00/training-embedding-finetune)). The router's embedding tag was the stock name, and its threshold had been calibrated on stock vectors.
- Under the swapped model the cosine distribution collapsed: for the same query the top similarity was 0.44 and the median 0.06 where the stock model gave 0.72. No row cleared even the 0.50 threshold, so every request that reached the semantic tier escalated (the substring and keyword tiers still answered some requests, so the outage was partial and easy to miss).
- The serving process was a 7-day-old orphan: its launchd label had been disabled in the user's domain, so nothing restarted or reloaded it.

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

### What we changed

1. Pin the router to a dedicated tag that always points at the stock weights (a copy under a second name) and never to the shared tag. The router default now names that tag, with a comment saying why.
2. Re-enable and re-bootstrap the service definition.
3. Re-calibrate the threshold on the repaired model with the evaluation set (below).
4. Add the first three checks the gate prints on failure (is the tag replaced, was the constant edited, is the model server up).

### Results: the first calibration (stock model, mean aggregation, no sidecar)

Threshold sweep on the 37-item set, production configuration (derived from the recorded sweep, which reproduces the 2026-09-06 numbers):

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

At the old 0.50 the repaired router rejected only 2 of 10 garbage inputs. 0.68 was the highest-exact point that rejected at least 9 of 10 (11 exact, 3 sibling, 6 wrong, 7 escalated). 0.70 rejects all garbage but costs one exact route and escalates 9.

### What did not work

- Raising the threshold alone to clear garbage entirely (0.70 to 0.72) costs exact 11 to 7: a global threshold trades recall against garbage on one axis.
- The process restart: two `kickstart -k` attempts each left an orphan holding the port (the new instance crash-looped 21 times against an occupied port) until we ran bootout, killed the orphan, then bootstrap; only then did the process manager's pid equal the pid holding the port.

### Pitfalls

| Symptom | Root cause | Fix |
|---|---|---|
| Health green, every request escalates | Fail-open caller plus a health check that does not exercise routing | Probe with fixed tasks that must route, and alert on the non-escalation rate |
| Same tag, different model | Shared mutable tag; the pull/tag operation replaces content silently | Pin by digest or by a private tag; check a fixed probe pair's cosine against a recorded reference (the stock-versus-fine-tuned cosine for one input ranges 0.74 to 0.96, so test the expected reference, not a loose band) |
| Orphan process holds the port after restart | `kickstart -k` raced the old instance; label disabled | After every restart assert that the process manager's pid equals the pid listening on the port, and inspect the process's own environment |
| Threshold "calibrated" but unusable | Calibrated on one embedding distribution; model changed | Store the model digest next to the threshold; recalibrate when it changes |

### The rule

A threshold belongs to an embedding model. Pin the model by digest, store them together, and monitor the non-escalation rate of known-good probes, because a fail-open caller turns a dead router into normal-looking behaviour.

[Back to the book](../README.md) · [Complete tables](results.md) · [Expanded pitfalls](pitfalls.md)
