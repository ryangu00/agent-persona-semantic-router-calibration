"""Dependency-free reference: global top-k, then aggregate per persona."""
from collections import defaultdict
from math import isfinite, sqrt
from types import SimpleNamespace


def normalize(vector):
    values = [float(v) for v in vector]
    if not values or not all(isfinite(v) for v in values):
        raise ValueError("vectors must be nonempty and finite")
    norm = sqrt(sum(v * v for v in values))
    return [v / norm for v in values] if norm else values


def score_rows(query_vec, row_vecs, row_owner, agg, top_k=10):
    if agg not in {"mean", "max", "sum"} or top_k < 1:
        raise ValueError("invalid aggregation or top_k")
    if len(row_vecs) != len(row_owner):
        raise ValueError("row owners do not match vectors")
    q = normalize(query_vec)
    rows = [normalize(v) for v in row_vecs]
    if any(len(v) != len(q) for v in rows):
        raise ValueError("vector dimensions differ")
    sims = [sum(a * b for a, b in zip(v, q)) for v in rows]
    top = sorted(range(len(sims)), key=lambda i: -sims[i])[:top_k]
    groups = defaultdict(list)
    for i in top:
        groups[row_owner[i]].append(sims[i])
    scores = {p: max(v) if agg == "max" else sum(v) / len(v) if agg == "mean"
              else sum(v) for p, v in groups.items()}
    return sorted(scores.items(), key=lambda pair: -pair[1])


def route_semantic(query_vec, row_vecs, row_owner, agg, threshold, top_k=10):
    ranked = score_rows(query_vec, row_vecs, row_owner, agg, top_k)
    if not ranked:
        return None, None
    persona, score = ranked[0]
    return (persona if score >= threshold else None), score


class MiniRouter:
    def __init__(self, routes, encoder, aggregation="mean", score_threshold=0.72, top_k=10):
        self.routes, self.encoder = routes, encoder
        self.aggregation, self.top_k = aggregation, top_k
        self.score_threshold = score_threshold
        self.owners = [r.name for r in routes for _ in r.utterances]
        self.texts = [t for r in routes for t in r.utterances]
        self.vectors = encoder(self.texts)
        self._scores = {}

    def set_threshold(self, threshold):
        self.score_threshold = threshold

    def ranked(self, text):
        # Replay reuses scores as well as vectors; configuration stays immutable.
        if text not in self._scores:
            self._scores[text] = score_rows(self.encoder([text])[0], self.vectors,
                                           self.owners, self.aggregation, self.top_k)
        return self._scores[text]

    def __call__(self, text, limit=2):
        return [SimpleNamespace(name=p, similarity_score=s)
                for p, s in self.ranked(text) if s >= self.score_threshold][:limit]
