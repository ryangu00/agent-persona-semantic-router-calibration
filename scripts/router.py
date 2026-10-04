"""Encoder wiring and escalation; a mini backend permits stdlib-only demos."""
import os
from adapter import DEFAULT_INDEX, load_personas, personas_to_routes
from embeddings import OfflineEncoder, OneTextEncoder, DEFAULT_MODEL, DEFAULT_URL
from mini_router import MiniRouter
from models import Routed

# Historical max-plus-phrasings setting: garbage reached 0.711; 0.72 rejected it.
# This is a recorded setting, not a calibrated threshold for synthetic vectors.
DEFAULT_SCORE_THRESHOLD = 0.72
DEFAULT_AGGREGATION = "mean"


def _resolve_aggregation():
    # Explicit activation prevents an unattended restart switching mean to max.
    value = os.environ.get("PERSONA_ROUTER_AGG", "").strip().lower()
    return value if value in {"mean", "max", "sum"} else DEFAULT_AGGREGATION


def make_encoder(model=DEFAULT_MODEL, base_url=DEFAULT_URL, offline=True):
    return OfflineEncoder() if offline else OneTextEncoder(base_url, model)


def make_router(routes, encoder=None, score_threshold=DEFAULT_SCORE_THRESHOLD,
                aggregation=None, engine="mini"):
    encoder = encoder or make_encoder()
    aggregation = aggregation or _resolve_aggregation()
    if engine == "library":
        from library_backend import make_library_router
        return make_library_router(routes, encoder, score_threshold, aggregation)
    if engine != "mini":
        raise ValueError("unknown engine")
    return MiniRouter(routes, encoder, aggregation, score_threshold, top_k=10)


def build_router(index_path=DEFAULT_INDEX, score_threshold=DEFAULT_SCORE_THRESHOLD,
                 utterances=None, encoder=None, aggregation=None, engine="mini"):
    routes = personas_to_routes(load_personas(index_path), utterances_extra=utterances)
    return make_router(routes, encoder, score_threshold, aggregation, engine)


def route_task(router, text):
    if not text or not text.strip():
        return Routed(None, None, True)
    choices = router(text=text, limit=2)
    if not isinstance(choices, list):
        choices = [choices] if choices is not None else []
    top = choices[0] if choices else None
    runner = choices[1] if len(choices) > 1 else None
    if top is None or top.name is None:
        return Routed(None, getattr(top, "similarity_score", None), True)
    return Routed(top.name, top.similarity_score, False,
                  getattr(runner, "name", None), getattr(runner, "similarity_score", None))
