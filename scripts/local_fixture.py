"""Explicit simulated Docker Engine fallback for local QA, never a real Docker proof."""

import json, os, pathlib, socketserver, struct, threading, time
from http.server import BaseHTTPRequestHandler

ROOT = pathlib.Path("state/local-fixture")
ROOT.mkdir(parents=True, exist_ok=True)
WORLD = ROOT / "world"
WORLD.mkdir(exist_ok=True)
RUNNING = True
LOGS = [
    "[LOCAL FIXTURE] Simulated Docker Engine. No Minecraft binary.",
    "FixturePlayer joined the game",
]


class Engine(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.route()

    def do_POST(self):
        self.route()

    def route(self):
        global RUNNING
        prefix = "/v1.45/containers/blockops-fixture"
        if not self.path.startswith(prefix):
            return self.reply(403, b"{}")
        suffix = self.path[len(prefix) :]
        if self.command == "GET" and suffix == "/json":
            return self.reply(
                200,
                json.dumps(
                    {
                        "State": {
                            "Running": RUNNING,
                            "Status": "running" if RUNNING else "exited",
                            "ExitCode": 0,
                            "StartedAt": "2026-10-07T00:00:00Z",
                        }
                    }
                ).encode(),
            )
        if self.command == "GET" and suffix.startswith("/logs?"):
            data = ("\n".join(LOGS) + "\n").encode()
            return self.reply(
                200, b"\x01\x00\x00\x00" + struct.pack(">I", len(data)) + data
            )
        if self.command == "POST" and suffix.split("?")[0] in [
            "/start",
            "/stop",
            "/restart",
        ]:
            RUNNING = not suffix.startswith("/stop")
            LOGS.append("[LOCAL FIXTURE] " + suffix.split("?")[0])
            return self.reply(204, b"")
        return self.reply(403, b"{}")

    def reply(self, status, data):
        self.send_response(status)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


sock = ROOT / "engine.sock"
if sock.exists():
    raise SystemExit("Local fixture socket exists; verify owner before removing it.")


def tick():
    while True:
        if RUNNING:
            (WORLD / "level.dat").write_text(
                "BLOCKOPS LOCAL FIXTURE\n" + str(time.time())
            )
            LOGS.append("[LOCAL FIXTURE] world saved")
            LOGS[:] = LOGS[-150:]
        time.sleep(5)


threading.Thread(target=tick, daemon=True).start()
from status_fixture import serve

threading.Thread(
    target=lambda: serve("127.0.0.1", int(os.environ.get("FIXTURE_MC_PORT", "12518"))),
    daemon=True,
).start()
try:
    with UnixServer(str(sock), Engine) as server:
        server.serve_forever()
finally:
    sock.unlink(missing_ok=True)
