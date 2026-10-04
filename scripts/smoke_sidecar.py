"""Loopback HTTP rehearsal with a synthetic pool; always shuts down the server."""
import json
from pathlib import Path
from http.server import ThreadingHTTPServer
import threading
from regression_gate import gate, http_json
from server import build_service, handler_for
from adapter import load_personas
from replay import evaluate_router


def main():
    pool = Path("fixtures/pool")
    router, names = build_service(pool, aggregation="max")
    data = json.loads((pool / "EVAL_SET.json").read_text())
    categories = {p["name"]: p["category"] for p in load_personas(pool / "INDEX.json")}
    baseline = evaluate_router(router, data["in_domain"], data["garbage"], categories)["metrics"]
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(router, names))
    except PermissionError:
        print("HTTP SMOKE NOT RUN: loopback bind denied by sandbox.")
        return 1
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        code, line, _ = gate(pool, baseline, lambda path, body: http_json(url + path, body))
        print(line)
        print("HTTP SMOKE PASS" if code == 0 else "HTTP SMOKE FAIL")
        return code
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    raise SystemExit(main())
