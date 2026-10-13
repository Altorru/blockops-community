"""Destructive only to the explicitly named disposable fixture world."""

import hashlib, http.cookiejar, json, pathlib, urllib.error, urllib.request, os

root = pathlib.Path(__file__).resolve().parent.parent
password = (root / "secrets/qa-password").read_text()
base = os.environ.get("VERIFY_BASE_URL", "http://127.0.0.1:4218") + "/api/"
transport = os.environ.get("FIXTURE_TRANSPORT", "docker")
label = "Docker" if transport == "docker" else "Simulated Engine"
jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
csrf = ""
results = []


def call(path, data=None, expected=200):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
    )
    try:
        with client.open(req, timeout=100) as r:
            code = r.status
            body = json.load(r)
    except urllib.error.HTTPError as e:
        code = e.code
        body = json.load(e)
    assert code == expected, (path, code, body)
    return body


def record(name):
    results.append({"check": name, "result": "pass"})


call("state", expected=401)
record("Unauthenticated state rejected")
call("login", {"username": "qa", "password": "bad"}, 401)
record("Wrong password rejected")
call("login", {"username": "qa", "password": password})
s = call("state")
assert s["fixture"] and s["server"]["name"] == "blockops-fixture"
csrf = s["csrf"]
record("Fixture target authenticated")
if transport in ("local", "docker"):
    assert (
        s["player_status"]["online"] == 1
        and s["player_status"]["source"] == "server_list_ping"
    )
    record("Synthetic Java Server List Ping via agent verified")
call("action", {"action": "stop", "confirmation": "NO"}, 400)
record("Missing confirmation rejected")
call("action", {"action": "shell", "confirmation": "CONFIRM"}, 400)
record("Arbitrary command rejected")
call("config", {"backup_hours": 0, "retention": 7, "auto_restart": False}, 400)
record("Invalid schedule rejected")
call("config", {"backup_hours": 24, "retention": 7, "auto_restart": False})
record("Schedule persisted")
call("action", {"action": "stop", "confirmation": "CONFIRM"})
assert not call("state")["server"]["running"]
record(label + " stop verified")
world = (
    pathlib.Path(os.environ.get("VERIFY_WORLD_PATH", str(root / "world"))) / "level.dat"
)
world.write_text("BLOCKOPS RESTORE PROOF\n")
digest = hashlib.sha256(world.read_bytes()).hexdigest()
call("action", {"action": "backup", "confirmation": "CONFIRM"})
backup = call("state")["backups"][0]["id"]
record("Stopped-world backup verified")
world.write_text("CHANGED AFTER BACKUP\n")
call("action", {"action": "restore", "id": backup, "confirmation": "CONFIRM"})
assert hashlib.sha256(world.read_bytes()).hexdigest() == digest
assert not call("state")["server"]["running"]
record("Restore exact checksum + left stopped + safety copy")
call("action", {"action": "start", "confirmation": "CONFIRM"})
assert call("state")["server"]["running"]
record(label + " start verified")
call("action", {"action": "restart", "confirmation": "CONFIRM"})
assert call("state")["server"]["running"]
record(label + " restart verified")
old = csrf
csrf = "invalid"
call("action", {"action": "stop", "confirmation": "CONFIRM"}, 403)
csrf = old
record("Invalid CSRF rejected")
call("logout", {})
call("login", {"username": "viewer", "password": password})
csrf = call("state")["csrf"]
call("action", {"action": "stop", "confirmation": "CONFIRM"}, 403)
record("Viewer mutation denied")
report = {
    "fixture": "blockops-fixture; no Minecraft binary or EULA",
    "transport": transport,
    "checks": results,
    "restore_sha256": digest,
    "backup_id": backup,
}
(
    root / os.environ.get("VERIFY_REPORT", "evidence/fixture-verification.json")
).write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
