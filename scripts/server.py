"""Loopback sidecar and opt-in salted-hash-only request logging."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from adapter import load_personas
from embeddings import OfflineEncoder, OneTextEncoder, DEFAULT_MODEL, DEFAULT_URL
from hybrid import build_hybrid_router


class RequestLog:
    def __init__(self, path=None, salt=None):
        self.path = Path(path) if path else None
        self.salt = salt or secrets.token_hex()

    def write(self, task, result):
        if self.path is None:
            return
        digest = hashlib.sha256((self.salt + task).encode()).hexdigest()[:16]
        record = dict(taskhash=digest, persona=result.persona, source=result.source, score=result.score)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.fchmod(fd, 0o600)
            os.write(fd, (json.dumps(record) + "\n").encode())
        finally:
            os.close(fd)


def dispatch(router, names, method, path, payload=None, log=None):
    """Pure dispatch enables offline HTTP-contract tests without opening sockets."""
    if method == "GET" and path == "/health":
        return 200, dict(status="ok", routes=len(names))
    if method != "POST" or path != "/route":
        return 404, dict(error="not found")
    if not isinstance(payload, dict) or not isinstance(payload.get("task"), str):
        return 400, dict(error="task must be a string")
    result = router.route(payload["task"])
    if log:
        try:
            log.write(payload["task"], result)
        except OSError:
            pass  # Optional logging must not prevent a routing answer.
    return 200, dict(persona=result.persona, score=result.score, escalate=result.escalate,
                     source=result.source, runner_up=result.runner_up, path=names.get(result.persona))


def handler_for(router, names, log=None):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, code, body):
            encoded = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            self.respond(*dispatch(router, names, "GET", self.path))

        def do_POST(self):
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            except (ValueError, TypeError):
                return self.respond(400, dict(error="bad json"))
            self.respond(*dispatch(router, names, "POST", self.path, payload, log))

        def log_message(self, *args):
            pass
    return Handler


def build_service(pool, threshold=0.72, aggregation=None, backend="offline", model=DEFAULT_MODEL, url=DEFAULT_URL):
    root = Path(pool)
    utterances = json.loads((root / "UTTERANCES.json").read_text())
    keywords = json.loads((root / "KEYWORDS_EXTRA.json").read_text())
    encoder = OfflineEncoder() if backend == "offline" else OneTextEncoder(url, model)
    router = build_hybrid_router(root / "INDEX.json", threshold, utterances, keywords, encoder, aggregation)
    names = {p["name"]: p["path"] for p in load_personas(root / "INDEX.json")}
    return router, names


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pool", default="fixtures/pool")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--threshold", type=float, default=0.72)
    p.add_argument("--aggregation", choices=["mean", "max", "sum"])
    p.add_argument("--backend", choices=["offline", "ollama"], default="offline")
    p.add_argument("--model", default=os.environ.get("PERSONA_ROUTER_MODEL", DEFAULT_MODEL))
    p.add_argument("--url", default=os.environ.get("PERSONA_ROUTER_EMBED_URL", DEFAULT_URL))
    p.add_argument("--log", help="Opt-in persistent log path; omit to disable")
    args = p.parse_args()
    router, names = build_service(args.pool, args.threshold, args.aggregation, args.backend, args.model, args.url)
    log = RequestLog(args.log, os.environ.get("PERSONA_ROUTER_LOG_SALT"))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(router, names, log)) as server:
        print(f"Serving loopback port {server.server_port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
