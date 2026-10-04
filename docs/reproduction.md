# Reproduction without the original infrastructure

The default path uses only Python's standard library. It does not install dependencies or contact an embedding endpoint. Its vectors are deterministic hashed character-trigram bags. They demonstrate row construction, tier order, aggregation, threshold rejection, and replay; they do not reproduce the historical model's scores.

## Generate and test

Run from the repository root. Invoke the files as `python3 scripts/<name>.py`; Python adds the script directory to its import path, so sibling imports need no `PYTHONPATH` setting or package installation. The public tests use standard-library `unittest`, including the optional integration checks; pytest is not required.

```bash
python3 scripts/generate_fixtures.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/collect_embeddings.py --out artifacts/vectors.json
python3 scripts/replay.py --cache artifacts/vectors.json --out artifacts/replay.json
python3 scripts/probe.py
```

The generator stores the evaluation prompts independently from the description and utterance templates. The category/role list supplies the intended identities. This is public demonstration data, not a newly blind bank. The historical private texts remain withheld.

The replay writes all grid cells, all threshold sweep rows, a source partition, per-case outcomes, paired transitions, a sign test, sorted garbage scores, a worked pool comparison, and lexical overlap. Score-distribution analysis uses pre-rejection semantic scores, so rejected content still has a measurable nearest neighbor. The hybrid's keyword state remains fixed across arms.

The bundled trigram fixture can produce tied grid cells: most of its obvious role words resolve in the unchanged keyword tier. The constructed-vector test separately demonstrates a mean score dropping below threshold while max remains above it. Neither result should be presented as a replication of the historical gain.

The synthetic grid and sweep are demonstration-only: their test verifies the full factorial and isolated configurations, not the historical cell counts. The calibration-helper unit test uses recorded historical score lists directly; public fixtures do not reproduce those scores or the shipped counts of 14 exact routes and 10 garbage rejections.

## Cache identity and optional library replay

Collection fingerprints the index, pool markdown, phrasings, keywords, and evaluation. It stores the embedding backend and model identity with the vectors. Restarting collection resumes an identical cache; a mismatch refuses to mix vectors. Replay refuses a changed pool, and `CacheLookup` never fetches a missing text.

JSON is the dependency-free format. An `.npz` output uses NumPy, stores text keys without object-pickle loading, and persists after every batch. The separate manifest records the baseline and enriched row mappings.

```bash
python3 scripts/collect_embeddings.py --out artifacts/vectors.npz
python3 scripts/replay.py --cache artifacts/vectors.npz --engine library
```

The second command needs a separately prepared environment with the versions in `requirements.txt`; no automatic installation occurs. The historical environment was Python 3.11.15. Python 3.14 resolved an older incompatible library in the original installation attempt. This cookbook's standard-library demo is independent of that library restriction.

The optional backend uses a real `DenseEncoder` subclass and the library's `SemanticRouter` with `LocalIndex`, explicit aggregation, and `top_k=10`. Random-vector equivalence and constructor-wiring tests skip clearly if the library is unavailable. A skipped comparison is not fidelity evidence.

## Reader-controlled real embeddings

Once an Ollama endpoint and a suitable embedding model already exist, collection can use them. Model acquisition, exact digest discovery, and service installation are reader prerequisites; this offline cookbook does not establish them.

```bash
python3 scripts/collect_embeddings.py \
  --backend ollama \
  --url http://127.0.0.1:11434/api/embed \
  --model qwen3-embedding:0.6b \
  --model-digest "$PERSONA_MODEL_DIGEST" \
  --out artifacts/real-vectors.npz
python3 scripts/replay.py --cache artifacts/real-vectors.npz --engine library
```

The public model tag is mutable. The digest argument records a reader-verified identity; the collector does not independently resolve or validate that identity against Ollama. Do not interpret a label as verification. The historical digest prefix was `4c1a55ec`, but no weights are shipped.

Direct collection keeps batch 64, 6 attempts, backoff starting at 0.5 s, and a 0.25 s inter-batch pause. The server's real-embedding path sends one text per call; the optional library module also preserves the original one-text subclass. Neither path has been exercised against a real embedding server in this offline delivery.

## Local sidecar and measured gate baseline

First obtain a baseline from the selected synthetic replay arm. These are demonstration measurements, not the historical gate constants.

```bash
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path('artifacts/replay.json').read_text())
row = next(r for r in data['grid'] if r['config'] == 'sidecar-max' and r['threshold'] == 0.72)
Path('artifacts/baseline.json').write_text(json.dumps(row['metrics']) + '\n')
PY
python3 scripts/server.py --pool fixtures/pool --aggregation max --threshold 0.72 --port 8000
```

In another terminal:

```bash
python3 scripts/regression_gate.py --pool fixtures/pool \
  --url http://127.0.0.1:8000 --baseline artifacts/baseline.json
```

Stop the foreground sidecar with the terminal interrupt when finished. It binds only loopback. `/health` reports process readiness and route count; only the gate exercises routing quality. The server does not install a service definition.

`scripts/smoke_sidecar.py` performs a self-contained loopback rehearsal and shuts the server down. A sandbox may forbid binding a socket; that is reported separately from the injected-transport tests.

Logging is disabled unless `--log` is supplied. Use a persistent path such as `artifacts/requests.log`; generated artifacts are excluded by the directory's own ignore file. Configure `PERSONA_ROUTER_LOG_SALT` if stable local hashes are required; otherwise the process generates a fresh salt. Logs contain only hashes and decisions, use mode 0600, and carry no outcome labels.

The caller example returns explicit context first, honors opt-in and per-call opt-out, applies the spawn cap, resolves paths beneath the pool, and fails open on bad responses or unreadable files. It describes the contract without patching an agent runtime.

## Mock upstream workflow

```bash
python3 scripts/sync_watch.py
# Exit 2 means changes were found; exit 0 means no change.
python3 scripts/sync_shadow.py
python3 scripts/sync_apply.py
```

The watcher reads local snapshots. The shadow command reads explicitly labelled mock scores and generator output. The applier defaults to a read-only plan; no real board, service manager, generator, or hosting API is contacted. Unit tests inject failures into copy-only apply and verify rollback.

The original scan rules and tier priority are retained. The live shadow-pool rebuild and evaluation integration are not supplied as completed production tooling. The recorded real merge, scheduled job, and independent review were also unfinished. See [pool updates](pool-updates.md) and [adaptation boundaries](adaptations.md).
