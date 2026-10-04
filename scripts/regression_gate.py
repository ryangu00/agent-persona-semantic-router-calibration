"""HTTP or injected-transport gate. Always supply a measured demo baseline."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.request
from adapter import load_personas
from replay import evaluate_router

# Raise the supplied measured baseline with each improvement, or retreat stays green.
# Historical private-bank measurements are not demo targets.


def http_json(url, payload=None):
    request = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


def gate(pool, baseline, transport):
    try:
        if transport("/health", None).get("status") != "ok":
            raise ValueError("health not ok")
        class Remote:
            def route(self, task):
                data = transport("/route", dict(task=task))
                if not isinstance(data, dict) or not {"persona", "escalate", "source", "score"} <= data.keys():
                    raise ValueError("invalid routing response")
                return SimpleNamespace(**data)
        root = Path(pool)
        evaluation = json.loads((root / "EVAL_SET.json").read_text())
        categories = {p["name"]: p["category"] for p in load_personas(root / "INDEX.json")}
        report = evaluate_router(Remote(), evaluation["in_domain"], evaluation["garbage"], categories)
    except Exception as exc:
        return 1, f"ALERT gate unavailable: {type(exc).__name__}", None
    m = report["metrics"]
    bad = m["exact"] < baseline["exact"] or m["garbage"] < baseline["garbage"]
    line = (f"exact {m['exact']}/{m['n_cases']} (sibling {m['sibling']}, wrong {m['wrong']}, "
            f"escalated {m['escalated']}) | garbage {m['garbage']}/{m['n_garbage']}")
    if bad:
        line = "ALERT regression: " + line
        for row in [r for r in report["cases"] if r["outcome"] != "exact"][:6]:
            line += f"\nMISS expected={row['expected']} got={row['persona']}"
        line += "\nCheck model identity, threshold, embedding service, and the rejected keyword repairs."
    return int(bad), line, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", default="fixtures/pool")
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--baseline", required=True)
    args = p.parse_args()
    baseline = json.loads(Path(args.baseline).read_text())
    code, line, _ = gate(args.pool, baseline, lambda path, body: http_json(args.url + path, body))
    print(line)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
