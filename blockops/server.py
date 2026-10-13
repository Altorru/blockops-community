from typing import Any
import hashlib, hmac, json, os, pathlib, re, secrets, threading, time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from blockops.core import Ops, agent_client

ROOT = pathlib.Path(__file__).resolve().parent.parent
USERS = json.loads(
    pathlib.Path(os.environ.get("USERS_FILE", "secrets/users.json")).read_text()
)
ops = Ops(
    os.environ.get("WORLD_PATH", "world"),
    os.environ.get("BACKUP_PATH", "backups"),
    agent_client(),
)
sessions: dict[str, dict[str, Any]] = {}
attempts: dict[str, list[float]] = {}


def scheduler() -> None:
    while True:
        time.sleep(20)
        try:
            ops.tick()
        except Exception:
            ops.alert("Agent offline or backup failed. Check Docker agent and storage.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args: Any) -> None:
        pass

    def reply(
        self, status: int, data: dict[str, Any], extra: dict[str, str] | None = None
    ) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def session(self) -> dict[str, Any] | None:
        c: SimpleCookie = SimpleCookie()
        c.load(self.headers.get("Cookie", ""))
        token = c.get("blockops")
        s = sessions.get(token.value if token else "")
        return s if s and s["expires"] > time.time() else None

    def do_GET(self) -> None:
        if self.path.startswith("/api/"):
            s = self.session()
            if not s:
                return self.reply(401, {"error": "Sign in to your local console."})
            if self.path == "/api/state":
                try:
                    status = ops.agent("GET", "/status")
                    logs = ops.agent("GET", "/logs")["logs"]
                    player_status = ops.agent("GET", "/players")
                    players = set()
                    for line in logs.splitlines():
                        m = re.search(
                            r"([A-Za-z0-9_]{1,16}) (joined|left) the game", line
                        )
                        if m:
                            if m[2] == "joined":
                                players.add(m[1])
                            else:
                                players.discard(m[1])
                    return self.reply(
                        200,
                        {
                            "server": status,
                            "logs": logs,
                            "players": sorted(players) if status["running"] else [],
                            "player_status": player_status,
                            "player_source": "Recent log events only; not an authoritative live count.",
                            "backups": ops.backups(),
                            "config": ops.config,
                            "alerts": ops.alerts,
                            "csrf": s["csrf"],
                            "role": s["role"],
                            "fixture": os.environ.get("FIXTURE", "false") == "true",
                            "fixture_transport": os.environ.get(
                                "FIXTURE_TRANSPORT", "docker"
                            ),
                        },
                    )
                except Exception:
                    return self.reply(
                        503,
                        {
                            "error": "Agent unavailable. Check private proxy, target container and world mount."
                        },
                    )
            return self.reply(404, {"error": "Unknown endpoint"})
        files = {
            "/": "index.html",
            "/app.js": "app.js",
            "/style.css": "style.css",
            "/landing": "landing.html",
            "/brand": "brand.html",
            "/guide.html": "guide.html",
        }
        if self.path in {
            "/assets/logo.svg",
            "/assets/icon.svg",
            "/assets/mark.svg",
            "/assets/logo-dark.svg",
            "/assets/logo-light.svg",
            "/assets/logo-monochrome.svg",
            "/assets/icon-light.svg",
            "/assets/system-map.svg",
            "/assets/world-hero.png",
            "/assets/world-floating.png",
            "/assets/social-card.svg",
            "/assets/lucide/sprite.svg",
            "/assets/fonts/manrope-variable.ttf",
            "/assets/console-preview.jpg",
        }:
            p = ROOT / self.path.lstrip("/")
        elif self.path in files:
            p = ROOT / "web" / files[self.path]
        else:
            return self.reply(404, {"error": "Not found"})
        b = p.read_bytes()
        self.send_response(200)
        self.send_header(
            "Content-Type",
            {
                ".html": "text/html; charset=utf-8",
                ".js": "text/javascript",
                ".css": "text/css",
                ".svg": "image/svg+xml",
                ".ttf": "font/ttf",
                ".png": "image/png",
                ".jpg": "image/jpeg",
            }[p.suffix],
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'",
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self) -> None:
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n < 1 or n > 4096:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(n))
            if not isinstance(data, dict):
                raise ValueError("Expected object")
        except Exception:
            return self.reply(400, {"error": "Invalid JSON request"})
        if self.path == "/api/login":
            ip = self.client_address[0]
            now = time.time()
            attempts[ip] = [x for x in attempts.get(ip, []) if now - x < 300]
            if len(attempts[ip]) >= 10:
                return self.reply(
                    429, {"error": "Too many attempts. Wait five minutes."}
                )
            attempts[ip].append(now)
            username = data.get("username", "")
            if not isinstance(username, str) or not 1 <= len(username) <= 40:
                return self.reply(400, {"error": "Username required (1–40 characters)"})
            u = USERS.get(username)
            password = data.get("password", "")
            if not isinstance(password, str):
                return self.reply(400, {"error": "Password required"})
            salt = bytes.fromhex(u["salt"]) if u else b"unknown-user-salt"
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode(), salt, 300000
            ).hex()
            if not u or not hmac.compare_digest(digest, u["hash"]):
                return self.reply(401, {"error": "Username or password incorrect"})
            ops.metric("onboarding_started")
            token = secrets.token_urlsafe(32)
            sessions[token] = {
                "role": u["role"],
                "expires": now + 28800,
                "csrf": secrets.token_urlsafe(24),
            }
            for k in list(sessions):
                if sessions[k]["expires"] < now:
                    del sessions[k]
            secure = "; Secure" if os.environ.get("COOKIE_SECURE") == "true" else ""
            return self.reply(
                200,
                {"ok": True},
                {
                    "Set-Cookie": "blockops="
                    + token
                    + "; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800"
                    + secure
                },
            )
        s = self.session()
        if not s:
            return self.reply(401, {"error": "Session expired. Sign in again."})
        if not hmac.compare_digest(self.headers.get("X-CSRF-Token", ""), s["csrf"]):
            return self.reply(403, {"error": "Refresh the console before retrying."})
        if self.path == "/api/logout":
            c: SimpleCookie = SimpleCookie()
            c.load(self.headers.get("Cookie", ""))
            sessions.pop(c["blockops"].value, None)
            return self.reply(
                200,
                {"ok": True},
                {
                    "Set-Cookie": "blockops=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
                },
            )
        if s["role"] != "admin":
            return self.reply(403, {"error": "Administrator access required."})
        try:
            with ops.lock:
                if self.path == "/api/config":
                    ops.configure(data)
                elif self.path == "/api/action":
                    action = data.get("action")
                    if action not in ("start", "stop", "restart", "backup", "restore"):
                        raise ValueError("Unknown operation")
                    if data.get("confirmation") != "CONFIRM":
                        raise ValueError("Explicit confirmation required")
                    if action == "backup":
                        ops.backup()
                    elif action == "restore":
                        ops.restore(data.get("id", ""))
                    else:
                        ops.power(action)
                else:
                    return self.reply(404, {"error": "Unknown endpoint"})
            return self.reply(200, {"ok": True})
        except ValueError as e:
            return self.reply(400, {"error": str(e)})
        except Exception:
            return self.reply(
                503,
                {
                    "error": "Operation failed. Review local alerts, agent and disk permissions before retrying."
                },
            )


if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()
    ThreadingHTTPServer(
        (os.environ.get("BIND", "127.0.0.1"), int(os.environ.get("PORT", "4218"))),
        Handler,
    ).serve_forever()
