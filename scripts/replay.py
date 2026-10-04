"""Offline A/B, explicit factorial grid, sweeps and derived case analysis."""
import argparse
from collections import Counter
import json
import math
import re
from pathlib import Path
from adapter import _utterances_for
from collect_embeddings import collect, load_inputs, read_cache
from embeddings import CacheLookup
from hybrid import build_hybrid_router, _routing_lead, _content_tokens
from mini_router import score_rows, normalize


def evaluate_router(router, cases, garbage, categories):
    counts = dict(exact=0, sibling=0, wrong=0, escalated=0, accept_aware=0, garbage=0)
    details, garbage_details, by_source = [], [], {}
    for case in cases:
        result = router.route(case["prompt"])
        got, expected = result.persona, case["expect"]
        rejected = result.escalate or got is None
        kind = ("escalated" if rejected else "exact" if got == expected else "sibling"
                if got in categories and categories[got] == categories[expected] else "wrong")
        hit = not rejected and got in ({expected} | set(case.get("accept", [])))
        counts[kind] += 1
        counts["accept_aware"] += int(hit)
        source = by_source.setdefault(result.source, Counter())
        source[kind] += 1
        source["total"] += 1
        source["accept_aware"] += int(hit)
        details.append(dict(prompt=case["prompt"], expected=expected, persona=got,
                            outcome=kind, source=result.source, score=result.score, accept=hit))
    for task in garbage:
        result = router.route(task)
        rejected = result.escalate or result.persona is None
        counts["garbage"] += int(rejected)
        garbage_details.append(dict(prompt=task, persona=result.persona, score=result.score,
                                    source=result.source, rejected=rejected))
    admitted = counts["exact"] + counts["sibling"] + counts["wrong"]
    counts.update(precision=round(counts["exact"] / admitted, 3) if admitted else 1.0,
                  n_cases=len(cases), n_garbage=len(garbage))
    return dict(metrics=counts, cases=details, garbage_cases=garbage_details, by_source=by_source)


def analyse(personas, inputs, cache, baseline, shipped):
    transitions = Counter()
    changed, gains, losses = [], 0, 0
    for before, after in zip(baseline["cases"], shipped["cases"]):
        transitions[before["outcome"] + " -> " + after["outcome"]] += 1
        gains += before["outcome"] != "exact" and after["outcome"] == "exact"
        losses += before["outcome"] == "exact" and after["outcome"] != "exact"
        if (before["persona"], before["outcome"]) != (after["persona"], after["outcome"]):
            changed.append(dict(before=before, after=after))
    pairs = gains + losses
    p = min(1.0, 2 * sum(math.comb(pairs, i) for i in range(min(gains, losses) + 1)) / 2 ** pairs)
    distributions, pools = {}, {}
    for enriched in (False, True):
        extra = inputs["UTTERANCES.json"] if enriched else {}
        rows = [(p["name"], t) for p in personas for t in _utterances_for(p, extra.get(p["name"]))]
        owners, texts = zip(*rows)
        vectors = [cache[t] for t in texts]
        for agg in ("mean", "max"):
            key = ("sidecar" if enriched else "none") + "-" + agg
            distributions[key] = sorted([score_rows(cache[_routing_lead(g)], vectors, owners, agg)[0][1]
                                         for g in inputs["EVAL_SET.json"]["garbage"]], reverse=True)
        query = inputs["EVAL_SET.json"]["in_domain"][0]["prompt"]
        q = normalize(cache[_routing_lead(query)])
        similarities = [sum(a * b for a, b in zip(normalize(v), q)) for v in vectors]
        top = sorted(range(len(similarities)), key=lambda i: -similarities[i])[:10]
        groups = {}
        for i in top:
            groups.setdefault(owners[i], []).append(similarities[i])
        pools["sidecar" if enriched else "none"] = [
            dict(persona=name, rows=len(values), mean=sum(values) / len(values), max=max(values))
            for name, values in groups.items()]
    phrasings = [(owner, text) for owner, values in inputs["UTTERANCES.json"].items() for text in values]
    overlaps = []
    for case in inputs["EVAL_SET.json"]["in_domain"]:
        query = _routing_lead(case["prompt"])
        stop = set("a an the of to and or for in on with this that is are as at by from it".split())
        tokens = lambda text: set(re.findall(r"[a-z0-9]+", text.lower())) - stop
        qt = tokens(query)
        best = max((len(qt & tokens(t)) / max(1, len(qt | tokens(t)))
                    for _, t in phrasings), default=0)
        ranked = score_rows(cache[query], [cache[t] for _, t in phrasings],
                            [p for p, _ in phrasings], "max")
        overlaps.append(dict(best_cosine=ranked[0][1], expected_owner=ranked[0][0] == case["expect"],
                             best_token_jaccard=best))
    return dict(transitions=transitions, changed=changed, gained=gains, lost=losses,
                sign_test_p=p, garbage_scores=distributions, example_pool_scores=pools, lexical_overlap=overlaps)


def run(pool, cache_path, engine="mini"):
    personas, inputs, fingerprint = load_inputs(pool)
    cache, metadata = read_cache(cache_path)
    if metadata["pool_hash"] != fingerprint:
        raise ValueError("pool hash mismatch: refuse replay")
    cases, garbage = inputs["EVAL_SET.json"]["in_domain"], inputs["EVAL_SET.json"]["garbage"]
    categories = {p["name"]: p["category"] for p in personas}
    grid, sweeps = [], {}
    for enriched in (False, True):
        for agg in ("mean", "max"):
            extra = inputs["UTTERANCES.json"] if enriched else {}
            # Injection stays in memory, keyword state is fixed, configuration explicit.
            router = build_hybrid_router(Path(pool) / "INDEX.json", 0.68, extra,
                                         inputs["KEYWORDS_EXTRA.json"], CacheLookup(cache), agg, engine)
            key = ("sidecar" if enriched else "none") + "-" + agg
            for threshold in (0.68, 0.72):
                router.semantic.set_threshold(threshold)
                result = evaluate_router(router, cases, garbage, categories)
                grid.append(dict(config=key, threshold=threshold, **result))
            sweeps[key] = []
            for point in range(40, 81):
                threshold = round(point / 100, 2)
                router.semantic.set_threshold(threshold)
                result = evaluate_router(router, cases, garbage, categories)
                sweeps[key].append(dict(threshold=threshold, **result["metrics"]))
    return dict(synthetic=bool(inputs["INDEX.json"].get("synthetic")), engine=engine,
                metadata=metadata, grid=grid, sweeps=sweeps,
                analysis=analyse(personas, inputs, cache, grid[0], grid[-1]))


def print_tables(result):
    print("SYNTHETIC DEMONSTRATION; not the historical measurements." if result["synthetic"]
          else "Reader-supplied data; not the historical measurements.")
    print("| Configuration | Threshold | exact | sibling | wrong | escalated | accept-aware | garbage | precision |")
    print("|---|---|---|---|---|---|---|---|---|")
    for row in result["grid"]:
        m = row["metrics"]
        print(f"| {row['config']} | {row['threshold']:.2f} | " + " | ".join(
            str(m[k]) for k in ("exact", "sibling", "wrong", "escalated", "accept_aware", "garbage", "precision")) + " |")
    print("\nSweep cells: exact / escalated / garbage rejected.")
    names = list(result["sweeps"])
    print("| Threshold | " + " | ".join(names) + " |")
    print("|---|---|---|---|---|")
    for rows in zip(*(result["sweeps"][n] for n in names)):
        print(f"| {rows[0]['threshold']:.2f} | " + " | ".join(
            f"{r['exact']} / {r['escalated']} / {r['garbage']}" for r in rows) + " |")
    print("\n| Configuration | Garbage scores, highest first |")
    print("|---|---|")
    for key, scores in result["analysis"]["garbage_scores"].items():
        print("| " + key + " | " + ", ".join(f"{s:.3f}" for s in scores) + " |")
    print("\n| Pool | Persona | Rows in top 10 | Mean | Max |")
    print("|---|---|---|---|---|")
    for pool, rows in result["analysis"]["example_pool_scores"].items():
        for row in rows:
            print(f"| {pool} | {row['persona']} | {row['rows']} | {row['mean']:.3f} | {row['max']:.3f} |")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", default="fixtures/pool")
    p.add_argument("--cache", default="artifacts/vectors.json")
    p.add_argument("--out", default="artifacts/replay.json")
    p.add_argument("--engine", choices=["mini", "library"], default="mini")
    args = p.parse_args()
    if not Path(args.cache).exists():
        collect(args.pool, args.cache)
    result = run(args.pool, args.cache, args.engine)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print_tables(result)


if __name__ == "__main__":
    main()
