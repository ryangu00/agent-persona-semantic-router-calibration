# Validation of the public package

These are checks of the synthetic public package, not reruns of the private measurements in the historical tables. No dependency installation, external network request, or git command was used. All output files were created inside the repository.

The offline tests and script-entry checks below were rerun for the review fixes. Replay, probe, loopback, mock-sync and original publication-audit results are retained from the initial package validation.

## Offline tests

Command:

```bash
env -u PYTHONPATH -u PYTHONSAFEPATH PYTHONDONTWRITEBYTECODE=1 RUN_OLLAMA_TESTS=0 python3 -m unittest discover -s tests
```

Exact final result lines:

```text
Ran 33 tests in 1.983s

OK (skipped=3)
```

The skipped checks are the random-vector comparison with the real routing library, the library-constructor wiring check, and live Ollama integration. The routing library was unavailable in the execution environment. The live test was disabled. No claim of real-library or real-model acceptance is made.

The executed tests cover row construction, fixture identity, quality filters, path containment, global retrieval, mean dilution, aggregation defaults, keyword ties and lint, accept-set accounting, absolute calibration, deterministic vectors, resumable npz collection, retry behavior, one-text transport, private logs, injected HTTP dispatch and gate checks, fail-open consumption, full replay isolation, content scanning, tier policy, copy-only apply, rollback, and overdue-key behavior.

The calibration-helper test supplies historical score lists directly and checks the selection objectives; it does not reproduce the shipped 14 exact routes and 10 garbage rejections from public fixtures. The synthetic grid and sweep are demonstration-only: their test verifies the full factorial and isolated configurations, not the historical cell counts.

## Script entry points

Commands run from the repository root, with no custom module search path:

```bash
env -u PYTHONPATH -u PYTHONSAFEPATH PYTHONDONTWRITEBYTECODE=1 python3 scripts/replay.py --help
env -u PYTHONPATH -u PYTHONSAFEPATH PYTHONDONTWRITEBYTECODE=1 python3 scripts/regression_gate.py --help
```

Both commands printed their argument help successfully. These checks exercise sibling imports through the documented script-path invocation; they do not run a replay or contact a sidecar.

## Replay and probe

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/replay.py --out artifacts/replay.json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/probe.py
```

Replay completed with exit status 0 and wrote the explicit grid, full sweeps, and derived analysis. Its output begins:

```text
SYNTHETIC DEMONSTRATION; not the historical measurements.
```

Exact probe result lines:

```text
Known-noise probe (non-fatal): rejected
PROBE PASS
```

## Loopback rehearsal

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/smoke_sidecar.py
```

Exact result, exit status 1:

```text
HTTP SMOKE NOT RUN: loopback bind denied by sandbox.
```

The real HTTP gate rehearsal could not execute because socket binding was denied. The injected-transport gate and dispatch tests passed; they do not substitute for a live listener test. No service was installed or left running.

## Mock sync commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_watch.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_shadow.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_apply.py
```

Watcher output was `Changed; review the delta.` with the documented changed-state exit status 2. Shadow output was `MOCK SHADOW: evaluated` with exit status 0. Apply returned a `dry-run` plan with the engineering fixture eligible and the finance fixture marked `sensitive`, exit status 0. These commands used fixture snapshots and mock scores, not live upstream data or routing measurements.

## Publication checks

The source and public results tables were compared mechanically; their numeric tokens were unchanged. The license and root ignore file were compared byte-for-byte. The banner AST was compared against the template and differed only in text constants; the tagline met the required limit, and no image was rendered.

Exact audit result lines:

```text
HISTORICAL TABLE CHECK PASS: 31 complete tables, numeric tokens unchanged.
TEMPLATE COPY CHECK PASS: LICENSE and .gitignore are byte-identical.
BANNER CHECK PASS: text-only changes; tagline within limit; renderer not run.
PUBLICATION SCAN PASS
```

The publication scan checks source syntax, CJK characters, restricted internal names, home-path patterns, and local Markdown links. This scan is not a substitute for supplying the missing owner-qualified upstream URLs in [credits](credits.md).
