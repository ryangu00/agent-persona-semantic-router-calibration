"""Partly validated apply protocol, exercised only on a sandbox copy."""
import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import shutil


def overdue_key(created, now):
    if now - created < timedelta(days=14):
        return None
    year, week, _ = now.isocalendar()
    return f"pool-sync-overdue-{year}-W{week}"


def apply(root, delta, verdict, auto_apply=False, dry_run=True, restart=None, identity=None, gate=None):
    root = Path(root)
    tiers = verdict["tiers"]
    selected = tiers["1"] + tiers["2"] if verdict["ok"] else []
    if dry_run:
        return dict(action="dry-run", files=selected, human=tiers["3"])
    if not auto_apply:
        return dict(action="confirm-only", files=selected, human=tiers["3"])
    if not verdict["ok"] or not selected:
        return dict(action="human-only", human=tiers["3"])
    if any(callback is None for callback in (restart, identity, gate)):
        raise ValueError("restart, process identity and gate callbacks are required")
    files = {entry["path"]: entry for entry in delta}
    # The public demonstration backs up a disposable copy, never a live service.
    backup = root.with_name(root.name + ".backup")
    if backup.exists():
        raise ValueError("backup already exists")
    shutil.copytree(root, backup)
    try:
        for name in selected:
            target = (root / name).resolve()
            if not target.is_relative_to(root.resolve()):
                raise ValueError("escaping apply path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(files[name]["text"])
        restart()
        manager_pid, listener_pid = identity()
        if not manager_pid or manager_pid != listener_pid:
            raise RuntimeError("process identity mismatch")
        if gate() != 0:
            raise RuntimeError("regression gate failed")
    except Exception:
        shutil.rmtree(root)
        shutil.copytree(backup, root)
        return dict(action="rollback", human=[dict(reason="apply failed")])
    return dict(action="applied-to-copy", files=selected, human=tiers["3"])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", default="artifacts/sync-copy")
    p.add_argument("--delta", default="artifacts/delta.json")
    p.add_argument("--verdict", default="artifacts/verdict.json")
    args = p.parse_args()
    result = apply(args.root, json.loads(Path(args.delta).read_text()),
                   json.loads(Path(args.verdict).read_text()))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
