"""Synthetic identity / category / merely-routes probes; noise leak is surfaced."""
import argparse
from server import build_service
from adapter import load_personas
from pathlib import Path


def probe(router, categories):
    cases = [("Compiler Specialist", {"persona": "demo-engineering-compiler"}),
             ("design", {"category": "design"}), ("marketing", {})]
    failures = []
    for task, expected in cases:
        res = router.route(task)
        if res.escalate or not res.persona:
            failures.append("expected a route")
        elif "persona" in expected and res.persona != expected["persona"]:
            failures.append("wrong identity")
        elif "category" in expected and categories.get(res.persona) != expected["category"]:
            failures.append("wrong category")
    if not router.route("").escalate:
        failures.append("empty input must escalate")
    for task in ("Where did my umbrella go", "Good evening everyone"):
        if not router.route(task).escalate:
            failures.append("real-language garbage leaked")
    leak = router.route("zxvqq jkkzz vvv")
    return failures, leak


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", default="fixtures/pool")
    args = p.parse_args()
    router, _ = build_service(args.pool)
    cats = {p["name"]: p["category"] for p in load_personas(Path(args.pool) / "INDEX.json")}
    failures, leak = probe(router, cats)
    print("Known-noise probe (non-fatal):", "rejected" if leak.escalate else "leaked")
    print("PROBE PASS" if not failures else "PROBE FAIL: " + "; ".join(failures))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
