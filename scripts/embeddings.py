"""Synthetic trigram vectors and an explicit local Ollama transport."""
import hashlib
import json
import time
import urllib.request
from mini_router import normalize

DEFAULT_MODEL = "qwen3-embedding:0.6b"
DEFAULT_URL = "http://127.0.0.1:11434/api/embed"
SYNTHETIC_MODEL = "synthetic-character-trigrams"


class OfflineEncoder:
    """Hash character trigrams; these vectors are not semantic-model evidence."""
    def __init__(self, dimensions=1024):
        self.dimensions = dimensions
        self.score_threshold = 0.72

    def __call__(self, docs):
        result = []
        for doc in docs:
            text = "  " + " ".join(doc.lower().split()) + "  "
            vec = [0.0] * self.dimensions
            for i in range(len(text) - 2):
                digest = hashlib.sha256(text[i:i + 3].encode()).digest()
                slot = int.from_bytes(digest, "big") % self.dimensions
                vec[slot] += 1.0
            result.append(normalize(vec))
        return result


class CacheLookup:
    def __init__(self, cache):
        self.cache = cache
        self.score_threshold = 0.72

    def __call__(self, docs):
        # No network fallback: a missing text is an input-identity failure.
        try:
            return [list(self.cache[d]) for d in docs]
        except KeyError as exc:
            raise ValueError("CACHE MISS: recollect the frozen inputs") from exc


def embed_batch(texts, url=DEFAULT_URL, model=DEFAULT_MODEL, opener=None, sleep=time.sleep):
    opener = opener or urllib.request.urlopen
    req = urllib.request.Request(url, data=json.dumps({"model": model, "input": texts}).encode(),
                                 headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(6):
        try:
            with opener(req, timeout=180) as response:
                vectors = json.loads(response.read())["embeddings"]
            if len(vectors) != len(texts) or not vectors:
                raise ValueError("embedding response count mismatch")
            vectors = [normalize(v) for v in vectors]
            if len({len(v) for v in vectors}) != 1:
                raise ValueError("embedding dimensions differ")
            return vectors
        except Exception as exc:
            last = exc
            sleep(0.5 * 2 ** attempt)
    raise RuntimeError("embedding failed after 6 attempts") from last


class OneTextEncoder:
    """Restart-safe transport: no multi-text request reaches the endpoint."""
    def __init__(self, url=DEFAULT_URL, model=DEFAULT_MODEL, transport=embed_batch):
        self.url, self.model, self.transport = url, model, transport
        self.score_threshold = 0.72

    def __call__(self, docs):
        return [self.transport([doc], url=self.url, model=self.model)[0] for doc in docs]
