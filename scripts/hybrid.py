"""Lead truncation, token lint, generic-token filtering and hybrid routing."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
from typing import Any
SemanticRouter = Any
from adapter import DEFAULT_INDEX, load_personas
from router import DEFAULT_SCORE_THRESHOLD, Routed, build_router, route_task
LEAD_CHARS = 200

def _routing_lead(query: str) -> str:
    """Use the first paragraph only; keyword matching still sees the full task."""
    lead = query.strip().split('\n\n', 1)[0].strip()
    return lead[:LEAD_CHARS]
import re as _re
_STOP = frozenset('a an the of to and or for in on with you your is are be this that it as at by from will would should can could need please write create make build give list one detail task help using use into out over under not no yes'.split() + '\u7684 \u4e86 \u548c \u4e0e \u662f \u5728 \u7528 \u53ea \u4e0d \u8981 \u53e5 \u8bdd \u4e2d\u6587 \u8f93\u51fa \u5c55\u5f00 \u4e3e\u4f8b \u64b0\u5199 \u4e00\u4efd \u4e0d\u8981 \u7ed9\u51fa \u8fd9\u662f \u4e00\u4e2a \u4ee5\u53ca \u8fdb\u884c \u9700\u8981 \u5e2e\u6211 \u5b8c\u6210 \u5173\u4e8e \u5305\u542b \u8986\u76d6'.split())
_TECH_ACRONYMS = frozenset('ci cd qa ml ai ux ui db aa js ts go os vm io'.split())
_SLASH_RUN = _re.compile('[a-z0-9]+(?:/[a-z0-9]+)+')

def _content_tokens(text) -> set:
    """English signal tokens, curated acronyms, slash runs, and character bigrams."""
    if not isinstance(text, str) or not text:
        return set()
    low = text.lower()
    toks = set()
    for run in _SLASH_RUN.findall(low):
        sides = [s for s in run.split('/') if s]
        for s in sides:
            if _admit(s):
                toks.add(s)
        joined = ''.join(sides)
        if _admit(joined):
            toks.add(joined)
    for p in _re.findall('[a-z0-9]+|[\u4e00-\u9fff]+', low):
        if '\u4e00' <= p[0] <= '\u9fff':
            for i in range(len(p) - 1):
                bg = p[i:i + 2]
                if bg not in _STOP:
                    toks.add(bg)
            if 2 <= len(p) <= 4 and p not in _STOP:
                toks.add(p)
        elif _admit(p):
            toks.add(p)
    return toks

def _admit(p: str) -> bool:
    return (len(p) >= 3 or p in _TECH_ACRONYMS) and p not in _STOP

def _eff_len(term: str) -> int:
    cjk = sum((1 for c in term if '\u4e00' <= c <= '\u9fff'))
    if cjk:
        return cjk
    return sum((1 for c in term if c.isalnum()))
_NONDISCRIMINATING_MAX = 8

def _generic_name_tokens(ptok_rows, max_df: int=_NONDISCRIMINATING_MAX) -> set:
    """Remove high-document-frequency tokens from name/title weight-3 sets."""
    from collections import Counter
    df: Counter = Counter()
    for _name, nt, _kw, _extra in ptok_rows:
        for tok in set(nt):
            df[tok] += 1
    return {tok for tok, c in df.items() if c > max_df}

def _lint_keywords_extra(index: dict, extra: dict | None):
    cleaned: dict[str, list[str]] = {}
    rejects: list[tuple[str, str, str]] = []
    if not extra:
        return (cleaned, rejects)
    norm: dict[str, list[str]] = {}
    term_personas: dict[str, set[str]] = {}
    for persona, terms in extra.items():
        seen: list[str] = []
        for t in terms or []:
            if not isinstance(t, str):
                continue
            lt = t.strip().lower()
            if not lt or lt in seen:
                continue
            seen.append(lt)
            term_personas.setdefault(lt, set()).add(persona)
        norm[persona] = seen
    doc_token_sets: list[set] = []
    for cat in (index.get('categories') or {}).values():
        if not isinstance(cat, dict):
            continue
        for p in cat.get('personas', []):
            if not isinstance(p, dict):
                continue
            doc_token_sets.append(_content_tokens(p.get('title', '')) | _content_tokens(p.get('description', '')))

    def _doc_freq(term: str) -> int:
        tt = _content_tokens(term)
        if not tt:
            return 0
        return sum((1 for ts in doc_token_sets if tt & ts))
    for persona, terms in norm.items():
        keep: list[str] = []
        for lt in terms:
            if lt in _STOP:
                rejects.append((persona, lt, 'stopword'))
                continue
            if _eff_len(lt) < 2:
                rejects.append((persona, lt, 'too-short'))
                continue
            if len(term_personas.get(lt, ())) >= 2:
                rejects.append((persona, lt, 'collision'))
                continue
            if _doc_freq(lt) > _NONDISCRIMINATING_MAX:
                rejects.append((persona, lt, 'non-discriminating'))
                continue
            keep.append(lt)
        if keep:
            cleaned[persona] = keep
    return (cleaned, rejects)

class HybridRouter:

    def __init__(self, index: dict, semantic: SemanticRouter | None, keywords_extra: dict[str, list[str]] | None=None):
        self.index = index
        self.semantic = semantic
        cleaned, self.keyword_rejects = _lint_keywords_extra(index, keywords_extra)
        extra_by_name: dict[str, set] = {}
        for persona, terms in cleaned.items():
            ts: set = set()
            for t in terms:
                ts |= _content_tokens(t)
            if ts:
                extra_by_name[persona] = ts
        self._ptok = []
        for cat_name, cat in (index.get('categories') or {}).items():
            if not isinstance(cat, dict):
                continue
            for p in cat.get('personas', []):
                if not isinstance(p, dict) or not p.get('name'):
                    continue
                drop = {'pool', str(cat_name)} | {str(t).lower() for t in p.get('tags') or []}
                nameparts = {x for x in p['name'].lower().split('-') if x not in drop and len(x) >= 3}
                nt = nameparts | _content_tokens(p.get('title', ''))
                kw = {k.lower() for k in p.get('keywords') or [] if isinstance(k, str) and len(k) >= 3 and (k.lower() not in _STOP)}
                extra = extra_by_name.get(p['name'], set())
                self._ptok.append((p['name'], nt, kw, extra))
        generic = _generic_name_tokens(self._ptok)
        self.generic_name_tokens = generic
        self._ptok = [(name, nt - generic, kw, extra) for name, nt, kw, extra in self._ptok]

    def _keyword_route(self, query: str):
        qt = _content_tokens(query)
        if not qt:
            return None
        best = None
        best_s = 0
        runner_s = 0
        for name, nt, kw, extra in self._ptok:
            s = 3 * len(qt & (nt | extra)) + len(qt & kw - nt - extra)
            if s > best_s:
                runner_s, best_s, best = (best_s, s, name)
            elif s > runner_s:
                runner_s = s
        if best_s >= 3 and best_s > runner_s:
            return (best, best_s)
        return None

    def route(self, query: str) -> Routed:
        if not query or not query.strip():
            return Routed(persona=None, score=None, escalate=True, source='none')
        full = query
        lead = _routing_lead(query)
        hits = literal_hits(self.index, lead)
        if hits:
            q = lead.strip().lower()
            top = hits[0]
            cat_hit = q in self.index.get('categories', {})
            nt_hit = q == (top.get('name') or '').lower() or q == (top.get('title') or '').lower()
            if cat_hit or nt_hit:
                return Routed(persona=top['name'], score=1.0, escalate=False, runner_up=hits[1]['name'] if len(hits) > 1 else None, source='substring')
        kwr = self._keyword_route(full)
        if kwr:
            return Routed(persona=kwr[0], score=None, escalate=False, source='keyword')
        if self.semantic is None:
            return Routed(persona=None, score=None, escalate=True, source='none')
        res = route_task(self.semantic, lead)
        return replace(res, source='semantic')

def literal_hits(index, query):
    """Public replacement: exact name/title or category, in index order."""
    q = query.strip().lower()
    hits = []
    for category, group in index.get('categories', {}).items():
        for persona in group.get('personas', []):
            if q in (category.lower(), persona['name'].lower(), persona.get('title', '').lower()):
                hits.append(persona)
    return hits[:2]


def build_hybrid_router(index_path=DEFAULT_INDEX, score_threshold=DEFAULT_SCORE_THRESHOLD,
                        utterances=None, keywords=None, encoder=None, aggregation=None,
                        engine='mini'):
    import json
    index = json.loads(Path(index_path).read_text())
    load_personas(index_path)
    semantic = build_router(index_path=index_path, score_threshold=score_threshold,
                            utterances=utterances, encoder=encoder,
                            aggregation=aggregation, engine=engine)
    return HybridRouter(index, semantic, keywords_extra=keywords)
