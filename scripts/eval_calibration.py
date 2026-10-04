"""Original accept-aware evaluation and admission-based threshold helper.

Its precision is accept-aware; replay reports exact precision separately.
"""
from __future__ import annotations
import logging
from typing import Any, Iterable, Mapping, Sequence
_LOG = logging.getLogger(__name__)
SOURCES = ('keyword', 'semantic', 'substring', 'none')
_SWEEP_LO = 0.4
_SWEEP_HI = 0.8
_SWEEP_STEP = 0.01

def evaluate(router: Any, cases: Sequence[Mapping[str, str]], garbage: Iterable[str]) -> dict:
    cases = list(cases)
    garbage = list(garbage)
    by_source: dict[str, dict[str, int]] = {s: {'total': 0, 'correct': 0} for s in SOURCES}
    correct = 0
    non_escalated = 0
    for case in cases:
        prompt = case['prompt']
        expect = case['expect']
        accept = set(case.get('accept') or ())
        accept.add(expect)
        res = router.route(prompt)
        src = getattr(res, 'source', 'none') or 'none'
        if src not in by_source:
            by_source[src] = {'total': 0, 'correct': 0}
        by_source[src]['total'] += 1
        escalate = getattr(res, 'escalate', True)
        persona = getattr(res, 'persona', None)
        if not escalate:
            non_escalated += 1
        hit = not escalate and persona in accept
        if hit:
            correct += 1
            by_source[src]['correct'] += 1
    recall = correct / len(cases) if cases else 1.0
    precision = correct / non_escalated if non_escalated else 1.0
    if garbage:
        escalated = sum((1 for g in garbage if getattr(router.route(g), 'persona', None) is None))
        garbage_escalation_rate = escalated / len(garbage)
    else:
        garbage_escalation_rate = 1.0
    return {'recall': recall, 'precision': precision, 'garbage_escalation_rate': garbage_escalation_rate, 'n_cases': len(cases), 'n_correct': correct, 'n_garbage': len(garbage), 'by_source': by_source}

def _garbage_esc_fraction(garbage_scores: Sequence[float], t: float) -> float:
    if not garbage_scores:
        return 1.0
    return sum((1 for g in garbage_scores if g < t)) / len(garbage_scores)

def _indomain_recall_fraction(indomain_scores: Sequence[float], t: float) -> float:
    if not indomain_scores:
        return 0.0
    return sum((1 for d in indomain_scores if d >= t)) / len(indomain_scores)

def refit_global_threshold(indomain_scores: Sequence[float], garbage_scores: Sequence[float], baseline: float) -> float:
    if not indomain_scores or not garbage_scores:
        return round(baseline, 2)
    baseline_garbage_esc = _garbage_esc_fraction(garbage_scores, baseline)
    n_steps = round((_SWEEP_HI - _SWEEP_LO) / _SWEEP_STEP)
    grid = [round(_SWEEP_LO + i * _SWEEP_STEP, 2) for i in range(n_steps + 1)]
    best_t: float | None = None
    best_recall = -1.0
    for t in grid:
        if _garbage_esc_fraction(garbage_scores, t) < baseline_garbage_esc:
            continue
        recall = _indomain_recall_fraction(indomain_scores, t)
        if recall > best_recall:
            best_recall = recall
            best_t = t
    if best_t is None:
        return round(baseline, 2)
    if best_t <= _SWEEP_LO or best_t >= _SWEEP_HI:
        _LOG.info('refit_global_threshold pinned to sweep boundary %.2f (baseline=%.2f, in-domain recall=%.3f) — data may want to push past the [%.2f, %.2f] sweep range', best_t, baseline, best_recall, _SWEEP_LO, _SWEEP_HI)
    return round(best_t, 2)


def refit_correctness(scored_cases, garbage_scores, minimum_rejected=None):
    """Maximize exact correctness under an absolute garbage-rejection requirement.

    scored_cases contains (best_score, best_persona_is_exact). Ties prefer more
    garbage rejection, then the lowest equally good threshold. None means the
    grid cannot satisfy the requirement; it must not silently weaken it.
    """
    required = len(garbage_scores) if minimum_rejected is None else minimum_rejected
    candidates = []
    for point in range(40, 81):
        threshold = round(point / 100, 2)
        rejected = sum(s < threshold for s in garbage_scores)
        exact = sum(correct and s >= threshold for s, correct in scored_cases)
        if rejected >= required:
            candidates.append((exact, rejected, -threshold))
    return -max(candidates)[2] if candidates else None
