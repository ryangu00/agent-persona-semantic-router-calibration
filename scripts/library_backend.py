"""Optional pinned-library backend; importing the offline demo does not load it."""
from semantic_router import Route, SemanticRouter
from semantic_router.encoders import OllamaEncoder
from semantic_router.encoders.base import DenseEncoder
from semantic_router.index import LocalIndex
from pydantic import PrivateAttr


class CacheEncoder(DenseEncoder):
    """A real DenseEncoder subclass, never a duck-typed substitute."""
    type: str = "ollama"
    _lookup = PrivateAttr()

    def __init__(self, lookup, threshold):
        super().__init__(name="cached-persona-vectors", score_threshold=float(threshold))
        self._lookup = lookup

    def __call__(self, docs):
        return self._lookup(docs)


class SafeBatchOllamaEncoder(OllamaEncoder):
    """The restart repair: dispatch one text per superclass call."""
    def __call__(self, docs):
        if len(docs) <= 1:
            return super().__call__(docs)
        result = []
        for doc in docs:
            result.extend(super().__call__([doc]))
        return result


def make_library_router(routes, lookup, threshold, aggregation):
    return SemanticRouter(
        routes=[Route(name=r.name, utterances=r.utterances, metadata=r.metadata) for r in routes],
        encoder=CacheEncoder(lookup, threshold), index=LocalIndex(), auto_sync="local",
        aggregation=aggregation, top_k=10,
    )
