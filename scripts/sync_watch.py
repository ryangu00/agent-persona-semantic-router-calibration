"""Partly validated sync design: local snapshots replace the hosting API."""
import argparse
import json
from pathlib import Path, PurePosixPath
from content_scan import scan_content


def watch(before, after, directories):
    changes = []
    for name in sorted(set(before) | set(after)):
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("escaping snapshot path")
        if path.suffix != ".md" or path.name == "README.md" or path.parts[0] not in directories:
            continue
        if before.get(name) == after.get(name):
            continue
        status = "removed" if name not in after else "added" if name not in before else "modified"
        safe, reasons = scan_content(after.get(name, ""))
        changes.append(dict(path=name, status=status, safe=safe, unsafe_reasons=reasons,
                            text=after.get(name)))
    return changes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshots", default="fixtures/sync_snapshots.json")
    p.add_argument("--out", default="artifacts/delta.json")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    data = json.loads(Path(args.snapshots).read_text())
    delta = watch(data["before"], data["after"], data["directories"])
    if not delta:
        print("No change; no output created.")
        return 0
    if not args.dry_run:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(delta, indent=2) + "\n")
    print("Changed; review the delta.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
