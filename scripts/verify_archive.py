"""Fresh archive smoke with private simulated Engine; never a Docker/Java claim."""

import datetime
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--archive", type=Path, default=ROOT / "dist/blockops-0.1.0.tar.gz")
parser.add_argument("--report", type=Path, default=ROOT / "evidence/archive-verification.json")
args = parser.parse_args()
archive = args.archive.resolve(strict=True)
run = (
    ROOT
    / "state/archive-check"
    / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
)
run.mkdir(parents=True)
started = time.monotonic()
with tarfile.open(archive) as pack:
    packaged_commit = pack.pax_headers.get("comment")
    pack.extractall(run, filter="data")
app = run / "blockops-0.1.0"
subprocess.run(
    [sys.executable, "scripts/seed_fixture.py"],
    cwd=app,
    check=True,
    stdout=subprocess.DEVNULL,
)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


agent_port, console_port, mc_port = [free_port() for _ in range(3)]
env = dict(
    os.environ,
    BIND="127.0.0.1",
    AGENT_BIND="127.0.0.1",
    AGENT_PORT=str(agent_port),
    PORT=str(console_port),
    DOCKER_SOCKET="state/local-fixture/engine.sock",
    AGENT_URL=f"http://127.0.0.1:{agent_port}",
    MC_HOST="127.0.0.1",
    MC_PORT=str(mc_port),
    FIXTURE_MC_PORT=str(mc_port),
    WORLD_PATH="state/local-fixture/world",
    BACKUP_PATH="state/local-fixture/backups",
    FIXTURE="true",
    FIXTURE_TRANSPORT="local",
    BLOCKOPS_CONTAINER="blockops-fixture",
    USERS_FILE="secrets/users.json",
    AGENT_TOKEN_FILE="secrets/agent-token",
    LOCAL_METRICS="false",
    COOKIE_SECURE="false",
)
processes = []
log = (run / "processes.log").open("w")
checks = []
try:
    for command in [
        ("scripts/local_fixture.py",),
        ("-m", "blockops.agent"),
        ("-m", "blockops.server"),
    ]:
        processes.append(
            subprocess.Popen(
                [sys.executable, *command], cwd=app, env=env, stdout=log, stderr=log
            )
        )
    deadline = time.monotonic() + 30
    while True:
        if any(p.poll() is not None for p in processes):
            raise RuntimeError(
                "Owned QA process exited; see state/archive-check process log."
            )
        try:
            urllib.request.urlopen(
                f"http://127.0.0.1:{console_port}/api/state", timeout=1
            )
        except urllib.error.HTTPError as e:
            if e.code == 401 and (app / "state/local-fixture/engine.sock").exists():
                break
        except OSError:
            pass
        if time.monotonic() > deadline:
            raise RuntimeError("Fresh archive startup timed out")
        time.sleep(0.1)
    boot_seconds = round(time.monotonic() - started, 3)
    for route in [
        "/landing",
        "/brand",
        "/guide.html",
        "/assets/console-preview.jpg",
        "/assets/world-floating.png",
        "/assets/fonts/manrope-variable.ttf",
        "/assets/lucide/sprite.svg",
    ]:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{console_port}" + route, timeout=5
        ) as r:
            assert r.status == 200
            checks.append({"path": route, "status": r.status, "bytes": len(r.read())})
    qaenv = dict(
        env,
        VERIFY_BASE_URL=f"http://127.0.0.1:{console_port}",
        VERIFY_WORLD_PATH="state/local-fixture/world",
        VERIFY_REPORT="evidence/archive-lifecycle.json",
    )
    subprocess.run(
        [sys.executable, "scripts/verify_fixture.py"],
        cwd=app,
        env=qaenv,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    lifecycle = json.loads((app / "evidence/archive-lifecycle.json").read_text())
    token = (app / "secrets/agent-token").read_text().strip()
    for route, authenticated, expected in [
        ("/status", False, 401),
        ("/status", True, 200),
        ("/containers/json", True, 403),
        ("/exec", True, 403),
    ]:
        headers = {"Authorization": "Bearer " + token} if authenticated else {}
        req = urllib.request.Request(
            f"http://127.0.0.1:{agent_port}" + route, headers=headers
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                status = r.status
        except urllib.error.HTTPError as e:
            status = e.code
        assert status == expected, (route, status)
        checks.append(
            {"proxy": route, "authenticated": authenticated, "status": status}
        )
    report = {
        "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "transport": "simulated_engine_fixture",
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "packaged_commit": packaged_commit,
        "fresh_archive": True,
        "qa_boot_seconds": boot_seconds,
        "qa_total_seconds": round(time.monotonic() - started, 3),
        "operator_install_seconds": None,
        "checks": checks,
        "lifecycle": lifecycle,
        "limit": "No Docker build, real Minecraft server or human operator installation validated.",
    }
    args.report.write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))
finally:
    for p in reversed(processes):
        if p.poll() is None:
            p.terminate()
    for p in processes:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    log.close()
