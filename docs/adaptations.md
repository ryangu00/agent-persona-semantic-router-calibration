# Adaptation boundaries

The public package is a runnable subset adapted from the supplied scripts. It does not redistribute their private data, paths, endpoints, service labels, or runtime patch. The historical prose comes only from the supplied fact sheet.

| Source responsibility | Public file | Preserved behavior and deliberate adaptation |
|---|---|---|
| Persona adapter | `scripts/adapter.py` | Row ordering, fallback, deduplication, quality filters, missing-file and duplicate-name checks; configurable pool input, category from records, path containment |
| Router wiring | `scripts/router.py`, `scripts/library_backend.py` | Explicit aggregation and top-k, mean fallback, threshold, escalation; optional real library and one-text encoder subclass; standard-library demo backend added |
| Hybrid tiers | `scripts/hybrid.py` | Lead rule, tokenizer, keyword lint, generic filter, per-token maximum, strict winner; unavailable literal dependency replaced by exact-name/title/category matching |
| Server | `scripts/server.py` | Loopback health/route interface, default-off hash logs and 0600; argument-based paths and port, process-local random salt by default |
| Evaluation | `scripts/eval_calibration.py` | Original accept-aware helper and admission refit preserved; correctness-based absolute-invariant helper added |
| Gate | `scripts/regression_gate.py` | Health and measured minimum checks; record-based categories; required measured demo baseline argument; unused historical constants removed from the public script |
| Probe | `scripts/probe.py` | Identity, category, and merely-routes assertions; real-language rejection and surfaced non-fatal noise probe; synthetic requests only |
| Collection | `scripts/collect_embeddings.py`, `scripts/embeddings.py` | Unique texts, direct requests, retries, pause, resumable npz; JSON fallback and frozen-input identity added |
| Full A/B | `scripts/replay.py` | In-memory row injection, fixed keyword state, isolated arms, reusable routers and sweep; explicit threshold axis, per-case dump, derived analyses folded in |
| Original tests | `tests/` | Key adapter, aggregation, keyword, evaluation, logging, cache, restart-channel and gate cases translated into standard-library unittest; dependency-dependent tests skip explicitly |
| Watch/shadow/apply | `scripts/sync_*.py`, `scripts/content_scan.py` | Content scan and policy, fail-closed unavailable evaluation, confirmation, process identity and rollback interfaces; local snapshots, mock scores and callback transports replace private integration |
| Runtime configuration | `configs/config.yaml.snippet` | Boolean opt-in interface only, default false |

The miniature scorer is a new standard-library reference implementation. The optional library path is the fidelity comparison target, not an assertion that the modified public hybrid reproduces all historical behavior. Missing library dependencies leave that comparison unverified.

The original evaluation helper's `precision` is accept-aware. The grid and gate instead expose exact precision, `exact / (exact + sibling + wrong)`, matching the historical tables. These names are kept distinct in the documentation to prevent mixing them.

The public sync tools are protocol demonstrations. They do not fetch upstream repositories, implement the unavailable original pool de-duplication dependency, rebuild and commit a live pool/index/sidecar bundle, advance upstream pins, install schedules, or send external cards. Their CLI shadow scores are mocks, not measured synthetic evaluation. Tests cover decision logic and rollback against a copy. End-to-end real sync remains unimplemented.

The English-only fixture requirement prevents shipping actual translated twin text. English aliases retain the three accept-set pairs without claiming multilingual coverage. Evaluation wording is fixed separately from the sidecar templates, but publishing it makes it unsuitable as a blind bank.

The optional class-level batching appendix is omitted; its lesson is documented in the sidecar chapter. All derived replay and analysis responsibilities are folded into the public harness rather than shipping the original analysis scripts with private paths.

The banner script preserves the supplied template layout and drawing code. Only its wordmark/tagline text and right-hand labels change. It is not executed. The existing footer and layout comments remain template material, not evidence that the router ran on the banner's named hardware.

The license and root ignore file are exact template copies. The license's supplied copyright notice is retained rather than replaced with a new author line. Generated artifacts have a separate directory-level ignore file.
