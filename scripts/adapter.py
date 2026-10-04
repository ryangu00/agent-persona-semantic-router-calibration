"""Adapt persona records to rows; preserve row order and quality filters."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from models import Route
POOL_ROOT = Path(__file__).resolve().parents[1] / 'fixtures/pool'
DEFAULT_INDEX = POOL_ROOT / 'INDEX.json'

def load_personas(index_path: str | Path=DEFAULT_INDEX) -> list[dict[str, Any]]:
    """Flatten category records and refuse a silently truncated index."""
    index_path = Path(index_path)
    data = json.loads(index_path.read_text(encoding='utf-8'))
    cats = data.get('categories') or {}
    personas: list[dict[str, Any]] = []
    for _cat_name, cat in cats.items():
        if not isinstance(cat, dict):
            continue
        for p in cat.get('personas', []):
            if isinstance(p, dict) and p.get('name'):
                p = dict(p)
                p.setdefault('category', _cat_name)
                personas.append(p)
    declared = data.get('total_personas')
    if declared is not None and declared != len(personas):
        raise ValueError(f'INDEX.json total_personas={declared} but flattened {len(personas)} persona records — index is inconsistent (refusing to build a partial router).')
    return personas

def _utterances_for(p: dict[str, Any], extra_utterances: list[str] | None=None) -> list[str]:
    """Structural rows first, then enrichment; absent enrichment changes nothing."""
    out: list[str] = []
    for key in ('title', 'description', 'expanded_description'):
        val = p.get(key)
        if isinstance(val, str):
            val = val.strip().strip('"').strip()
            if val and val not in out:
                out.append(val)
    if not out:
        out.append(p['name'])
    if extra_utterances:
        for u in extra_utterances:
            if isinstance(u, str):
                u = u.strip()
                if u and u not in out:
                    out.append(u)
    return out

def persona_to_route(p: dict[str, Any], utterances_extra: dict[str, list[str]] | None=None) -> Route:
    extra = utterances_extra.get(p['name']) if utterances_extra else None
    return Route(name=p['name'], utterances=_utterances_for(p, extra_utterances=extra), metadata={'path': p.get('path', ''), 'category': p.get('category') or (p.get('tags') or [p.get('original_category', '')])[0], 'title': p.get('title', '')})

def personas_to_routes(personas: list[dict[str, Any]], utterances_extra: dict[str, list[str]] | None=None) -> list[Route]:
    return [persona_to_route(p, utterances_extra=utterances_extra) for p in personas]
UTTERANCES_PATH = POOL_ROOT / 'UTTERANCES.json'

def load_utterances_extra(path: str | Path=UTTERANCES_PATH) -> dict[str, list[str]]:
    path = Path(path)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    out: dict[str, list[str]] = {}
    if isinstance(data, dict):
        for name, lst in data.items():
            if isinstance(name, str) and isinstance(lst, list):
                out[name] = [u for u in lst if isinstance(u, str) and u.strip()]
    return out

def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum((x * y for x, y in zip(a, b)))
    na = sum((x * x for x in a)) ** 0.5
    nb = sum((y * y for y in b)) ** 0.5
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
_BANNED_PREFIXES = ('help me', 'i need', 'i want', '<title>', 'do a task', 'complete this')

def qc_filter_utterances(cands: list[str], *, garbage_set: list[str], encoder: Any, margin: float) -> tuple[list[str], list[tuple[str, str]]]:
    """Reject boilerplate and garbage-close rows; skip degenerate self-identity."""
    kept: list[str] = []
    rejects: list[tuple[str, str]] = []
    seen: set[str] = set()
    garbage_vecs = encoder(list(garbage_set)) if garbage_set else []
    for cand in cands:
        if cand in seen:
            continue
        seen.add(cand)
        low = cand.strip().lower()
        if any((low.startswith(pre) for pre in _BANNED_PREFIXES)):
            rejects.append((cand, 'content-free prefix'))
            continue
        cand_vec = encoder([cand])[0]
        max_cos = max((_cosine(cand_vec, g) for g in garbage_vecs if g != cand_vec), default=0.0)
        if max_cos > 1.0 - margin:
            rejects.append((cand, f'garbage-close (max_cos={max_cos:.3f})'))
            continue
        kept.append(cand)
    return (kept, rejects)

def missing_persona_files(personas: list[dict[str, Any]], pool_root: str | Path=POOL_ROOT) -> list[str]:
    pool_root = Path(pool_root)
    missing: list[str] = []
    for p in personas:
        rel = p.get('path')
        target = (pool_root / rel).resolve() if rel else pool_root.resolve()
        if not rel or not target.is_relative_to(pool_root.resolve()) or not target.is_file():
            missing.append(p['name'])
    return missing

def duplicate_route_names(personas: list[dict[str, Any]]) -> list[str]:
    seen: dict[str, int] = {}
    for p in personas:
        seen[p['name']] = seen.get(p['name'], 0) + 1
    return sorted((n for n, c in seen.items() if c > 1))
