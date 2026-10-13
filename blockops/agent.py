from typing import Any

"""Private fixed-target Docker proxy. No arbitrary Docker URL forwarding."""
import http.client, json, os, re, socket, struct
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = os.environ.get("BLOCKOPS_CONTAINER", "blockops-fixture")
if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}", TARGET):
    raise ValueError("Invalid container")
TOKEN = open(os.environ.get("AGENT_TOKEN_FILE", "secrets/agent-token")).read().strip()


class UnixConnection(http.client.HTTPConnection):
    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(35)
        self.sock.connect(os.environ.get("DOCKER_SOCKET", "/var/run/docker.sock"))


def docker(method: str, suffix: str) -> bytes:
    c = UnixConnection("localhost", timeout=35)
    c.request(method, "/v1.45/containers/" + TARGET + suffix)
    r = c.getresponse()
    data = r.read(1024 * 1024)
    status = r.status
    c.close()
    if status not in (200, 204, 304):
        raise RuntimeError("Docker operation failed (%s)" % status)
    return data


def logs() -> str:
    raw = docker("GET", "/logs?stdout=1&stderr=1&tail=150&timestamps=1")
    out = b""
    while len(raw) >= 8 and raw[0] in (0, 1, 2) and raw[1:4] == b"\0\0\0":
        n = struct.unpack(">I", raw[4:8])[0]
        out += raw[8 : 8 + n]
        raw = raw[8 + n :]
    return (out or raw).decode("utf-8", errors="replace")[-30000:]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass

    def do_GET(self) -> None:
        self.handle_request()

    def do_POST(self) -> None:
        self.handle_request()

    def handle_request(self) -> None:
        import hmac

        if not hmac.compare_digest(
            self.headers.get("Authorization", ""), "Bearer " + TOKEN
        ):
            return self.reply(401, {"error": "Unauthorized"})
        try:
            if self.command == "GET" and self.path == "/status":
                d = json.loads(docker("GET", "/json"))
                s = d["State"]
                return self.reply(
                    200,
                    {
                        "name": TARGET,
                        "running": s["Running"] and s["Status"] == "running",
                        "status": s["Status"],
                        "exit_code": s["ExitCode"],
                        "started_at": s["StartedAt"],
                    },
                )
            if self.command == "GET" and self.path == "/players":
                host = os.environ.get("MC_HOST")
                if not host:
                    return self.reply(200, {"online": None, "source": "not_configured"})
                try:
                    from mcstatus import JavaServer

                    status = JavaServer(
                        host, int(os.environ.get("MC_PORT", "25565")), timeout=3
                    ).status()
                    return self.reply(
                        200,
                        {"online": status.players.online, "source": "server_list_ping"},
                    )
                except Exception:
                    return self.reply(200, {"online": None, "source": "unavailable"})
            if self.command == "GET" and self.path == "/logs":
                return self.reply(200, {"logs": logs()})
            if self.command == "POST" and self.path in ("/start", "/stop", "/restart"):
                docker("POST", self.path + ("" if self.path == "/start" else "?t=30"))
                return self.reply(200, {"ok": True})
            self.reply(403, {"error": "Operation is not allowlisted"})
        except Exception:
            self.reply(
                502,
                {
                    "error": "Docker target unavailable. Check target name and agent socket."
                },
            )

    def reply(self, status: int, data: dict[str, Any]) -> None:
        b = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


if __name__ == "__main__":
    ThreadingHTTPServer(
        (
            os.environ.get("AGENT_BIND", "127.0.0.1"),
            int(os.environ.get("AGENT_PORT", "8218")),
        ),
        Handler,
    ).serve_forever()
