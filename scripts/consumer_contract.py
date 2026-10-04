"""Caller contract example, not a patch to any agent runtime."""
import json
from pathlib import Path
import urllib.request


def read_persona(response, pool):
    if not isinstance(response, dict) or response.get("escalate") or not response.get("persona"):
        return None
    relative = response.get("path")
    if not isinstance(relative, str) or not relative:
        return None
    root = Path(pool).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        return None
    try:
        return path.read_text()
    except (OSError, UnicodeError):
        return None


def auto_context(task, pool, url, enabled=False, opt_out=False, explicit_context=None,
                 spawned=0, opener=None):
    if explicit_context:
        return explicit_context
    if not enabled or opt_out or spawned >= 5:
        return None
    opener = opener or urllib.request.urlopen
    request = urllib.request.Request(url.rstrip("/") + "/route",
                                     data=json.dumps(dict(task=task)).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with opener(request, timeout=2) as response:
            return read_persona(json.loads(response.read()), pool)
    except Exception:
        return None
