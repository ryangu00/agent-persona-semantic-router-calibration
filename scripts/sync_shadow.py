"""Partly validated tier policy with injected evaluation and generation."""
import argparse
import json
import os
from pathlib import Path
import re

# Real transports are deployment-specific; unset means no live generation.
GENERATOR_URL = os.environ.get("PERSONA_GENERATOR_URL")
GENERATOR_MODEL = os.environ.get("PERSONA_GENERATOR_MODEL")


def parse_lines(text, n=5):
    lines = []
    for raw in text.splitlines():
        value = re.sub(r"^\d+[.)]\s*", "", raw.strip().lstrip("-* ")).strip().strip('"')
        if not value or len(value) > 160 or value.lower().startswith(
                ("here are", "sure", "role:", "description:", "utterance", "task request")):
            continue
        if value not in lines:
            lines.append(value)
    return lines[:n]


def shadow(delta, baseline, routed_paths, evaluate, generate):
    tiers = {"1": [], "2": [], "3": []}
    try:
        # The callback includes embedding preflight; never generate if unavailable.
        scores = evaluate()
    except Exception:
        tiers["3"] = [dict(file=f["path"], reason="eval unavailable") for f in delta]
        return dict(ok=False, baseline=baseline, shadow=None, tiers=tiers, utterances={})
    regression = any(scores[k] < baseline[k] for k in ("exact", "garbage"))
    utterances = {}
    for entry in delta:
        path = entry["path"]
        category = path.split("/")[0]
        reason = None
        if not entry["safe"]:
            reason = "unsafe"
        elif category in {"finance", "legal"}:
            reason = "sensitive"
        elif entry["status"] == "removed" and path in routed_paths:
            reason = "removed-routable"
        elif regression:
            reason = "evaluation regression"
        if reason:
            tiers["3"].append(dict(file=path, reason=reason))
        elif entry["status"] != "removed":
            tiers["2" if entry["status"] == "modified" else "1"].append(path)
        if entry["status"] == "added":
            utterances[path] = parse_lines(generate(entry))
    return dict(ok=True, baseline=baseline, shadow=scores, tiers=tiers, utterances=utterances)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--delta", default="artifacts/delta.json")
    p.add_argument("--baseline", default="fixtures/sync_mock.json")
    p.add_argument("--mock", default="fixtures/sync_mock.json")
    p.add_argument("--out", default="artifacts/verdict.json")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    delta = json.loads(Path(args.delta).read_text())
    fixture = json.loads(Path(args.mock).read_text())
    baseline = json.loads(Path(args.baseline).read_text())["baseline"]
    def evaluate():
        if not fixture["available"]:
            raise RuntimeError("mock unavailable")
        return fixture["scores"]
    verdict = shadow(delta, baseline, fixture["routed_paths"], evaluate, lambda e: fixture["generation"])
    if not args.dry_run:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(verdict, indent=2) + "\n")
    print("MOCK SHADOW: " + ("evaluated" if verdict["ok"] else "unavailable; human review"))
    return 0 if verdict["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
