"""Resumable collection: JSON without dependencies, or NumPy npz explicitly."""
import argparse
import hashlib
import json
import time
from pathlib import Path
from adapter import _utterances_for, load_personas, missing_persona_files
from embeddings import OfflineEncoder, embed_batch, DEFAULT_MODEL, DEFAULT_URL, SYNTHETIC_MODEL
from hybrid import _routing_lead


def load_inputs(pool):
    pool = Path(pool)
    names = ("INDEX.json", "UTTERANCES.json", "KEYWORDS_EXTRA.json", "EVAL_SET.json")
    inputs = {name: json.loads((pool / name).read_text()) for name in names}
    persons = load_personas(pool / "INDEX.json")
    if missing_persona_files(persons, pool):
        raise ValueError("missing or escaping persona files")
    digest = hashlib.sha256()
    for name in sorted(set(names) | {p["path"] for p in persons}):
        digest.update(name.encode() + b"\0" + (pool / name).read_bytes() + b"\0")
    return persons, inputs, digest.hexdigest()


def corpus(personas, inputs):
    base = [(p["name"], t) for p in personas for t in _utterances_for(p)]
    extra = inputs["UTTERANCES.json"]
    full = [(p["name"], t) for p in personas for t in _utterances_for(p, extra.get(p["name"]))]
    evaluation = inputs["EVAL_SET.json"]
    leads = [_routing_lead(c["prompt"]) for c in evaluation["in_domain"]]
    garbage = [_routing_lead(g) for g in evaluation["garbage"]]
    # Cache the library's dimension probe explicitly; no hidden live request.
    texts = sorted({t for _, t in full} | set(leads + garbage) | {"test"})
    return texts, dict(base_rows=base, exp_rows=full, eval_leads=leads, garbage_leads=garbage)


def save_cache(path, cache, metadata):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    if path.suffix == ".npz":
        import numpy as np
        with temporary.open("wb") as stream:
            np.savez(stream, keys=np.array(list(cache)), vecs=np.array(list(cache.values())),
                     metadata=json.dumps(metadata, sort_keys=True))
    else:
        temporary.write_text(json.dumps(dict(metadata=metadata, vectors=cache)) + "\n")
    temporary.replace(path)


def read_cache(path):
    path = Path(path)
    if path.suffix == ".npz":
        import numpy as np
        with np.load(path, allow_pickle=False) as z:
            return {str(k): v.tolist() for k, v in zip(z["keys"], z["vecs"])}, json.loads(str(z["metadata"]))
    data = json.loads(path.read_text())
    return data["vectors"], data["metadata"]


def collect(pool, output, backend="offline", model=DEFAULT_MODEL, url=DEFAULT_URL,
            model_digest=None, batch=64, pause=0.25, transport=embed_batch, sleep=time.sleep):
    personas, inputs, fingerprint = load_inputs(pool)
    if batch < 1:
        raise ValueError("batch must be positive")
    if backend == "ollama" and not model_digest:
        raise ValueError("a recorded model digest is required for a real collection")
    metadata = dict(pool_hash=fingerprint, model=SYNTHETIC_MODEL if backend == "offline" else model,
                    model_digest="synthetic" if backend == "offline" else model_digest, backend=backend)
    texts, manifest = corpus(personas, inputs)
    cache = {}
    if Path(output).exists():
        cache, old = read_cache(output)
        if old != metadata:
            raise ValueError("cache input/model identity mismatch")
    todo = [t for t in texts if t not in cache]
    offline = OfflineEncoder()
    for offset in range(0, len(todo), batch):
        chunk = todo[offset:offset + batch]
        vectors = offline(chunk) if backend == "offline" else transport(chunk, url=url, model=model)
        if len(vectors) != len(chunk):
            raise ValueError("embedding response count mismatch")
        cache.update(zip(chunk, vectors))
        save_cache(output, cache, metadata)
        if backend != "offline":
            sleep(pause)
    manifest.update(metadata)
    Path(str(output) + ".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return cache, metadata


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", default="fixtures/pool")
    p.add_argument("--out", default="artifacts/vectors.json")
    p.add_argument("--backend", choices=["offline", "ollama"], default="offline")
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--model-digest")
    args = p.parse_args()
    collect(args.pool, args.out, args.backend, args.model, args.url, args.model_digest)
    print("Vector cache and row manifest written.")


if __name__ == "__main__":
    main()
