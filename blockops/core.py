from typing import Any, Callable, cast
from blockops.persistence import write_json

Agent = Callable[[str, str], dict[str, Any]]

import datetime, hashlib, json, os, pathlib, re, shutil, tarfile, threading, time, urllib.request


class Ops:
    def __init__(
        self, world: str | pathlib.Path, store: str | pathlib.Path, agent: Agent
    ) -> None:
        self.world = pathlib.Path(world)
        self.store = pathlib.Path(store)
        self.store.mkdir(parents=True, exist_ok=True)
        self.agent = agent
        self.lock = threading.RLock()
        self.alerts: list[dict[str, str]] = []
        self.failures = 0
        self.restarts: list[float] = []
        self.last_backup: float = 0
        self.last_attempt: float = 0
        self.maintenance = False
        self.desired = True
        self.config: dict[str, Any] = {
            "backup_hours": 24,
            "retention": 7,
            "auto_restart": False,
        }
        if (self.store / "config.json").exists():
            self.config = json.loads((self.store / "config.json").read_text())
        copies = list(self.store.glob("backup-*.tar.gz"))
        self.last_backup = max((p.stat().st_mtime for p in copies), default=0)
        if (self.store / "desired.json").exists():
            self.desired = json.loads((self.store / "desired.json").read_text())
        if (self.store / "restarts.json").exists():
            self.restarts = json.loads((self.store / "restarts.json").read_text())
        if (self.store / "alerts.json").exists():
            self.alerts = json.loads((self.store / "alerts.json").read_text())

    def alert(self, text: str) -> None:
        self.alerts.insert(
            0,
            {
                "at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "message": text,
            },
        )
        self.alerts = self.alerts[:30]
        write_json(self.store / "alerts.json", self.alerts)

    def configure(self, data: dict[str, Any]) -> None:
        if (
            type(data.get("backup_hours")) is not int
            or not 1 <= data["backup_hours"] <= 168
        ):
            raise ValueError("Backup interval: 1–168 hours")
        if type(data.get("retention")) is not int or not 2 <= data["retention"] <= 30:
            raise ValueError("Retention: 2–30 copies")
        if type(data.get("auto_restart")) is not bool:
            raise ValueError("Restart rule must be boolean")
        with self.lock:
            self.config = {k: data[k] for k in self.config}
            write_json(self.store / "config.json", self.config)

    def metric(self, event: str) -> None:
        if os.environ.get("LOCAL_METRICS", "true") != "true":
            return
        with self.lock:
            path = self.store / "metrics.json"
            values = json.loads(path.read_text()) if path.exists() else {}
            values[event] = values.get(event, 0) + 1
            write_json(path, values)

    def power(self, action: str) -> None:
        with self.lock:
            self.desired = action != "stop"
            write_json(self.store / "desired.json", self.desired)
            self.agent("POST", "/" + action)
            self.alert("Operator requested " + action + ".")

    @staticmethod
    def digest(path: pathlib.Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def backup_hash(self, path: pathlib.Path) -> str:
        sidecar = path.with_suffix(path.suffix + ".sha256")
        if not sidecar.exists():
            sidecar.write_text(self.digest(path))
        return sidecar.read_text().strip()

    def backups(self) -> list[dict[str, str | int]]:
        return [
            {"id": p.name, "bytes": p.stat().st_size, "sha256": self.backup_hash(p)}
            for p in sorted(self.store.glob("backup-*.tar.gz"), reverse=True)
        ]

    def backup(self, resume: bool = True) -> str:
        with self.lock:
            self.maintenance = True
            running = False
            failure = "Backup failed. Check world path and storage permissions."
            try:
                running = self.agent("GET", "/status")["running"]
                if running:
                    self.agent("POST", "/stop")
                    stopped = self.agent("GET", "/status")
                    if stopped["running"] or stopped["exit_code"] == 137:
                        running = False  # Do not hide a failed stop by starting again.
                        self.desired = False
                        write_json(self.store / "desired.json", False)
                        failure = "Backup refused: server still running or forcibly killed. Inspect server logs and shutdown handling before retrying."
                        raise ValueError(failure)
                if not self.world.is_dir():
                    raise ValueError("World directory missing")
                name = (
                    "backup-"
                    + datetime.datetime.now(datetime.timezone.utc).strftime(
                        "%Y%m%dT%H%M%S%fZ"
                    )
                    + ".tar.gz"
                )
                temp = self.store / (name + ".partial")
                with tarfile.open(temp, "w:gz") as tar:
                    for p in sorted(self.world.rglob("*")):
                        if p.is_symlink():
                            raise ValueError(
                                "Symlinks are not supported in world backups"
                            )
                        if p.is_file():
                            tar.add(
                                p,
                                arcname=str(p.relative_to(self.world)),
                                recursive=False,
                            )
                os.replace(temp, self.store / name)
                self.backup_hash(self.store / name)
                for old in sorted(self.store.glob("backup-*.tar.gz"), reverse=True)[
                    self.config["retention"] :
                ]:
                    old.unlink()
                    old.with_suffix(old.suffix + ".sha256").unlink(missing_ok=True)
                self.last_backup = time.time()
                self.alert("Backup completed; world copied while stopped.")
                self.metric("first_value_completed")
                return name
            except Exception:
                self.alert(failure)
                raise
            finally:
                try:
                    if running and resume:
                        self.agent("POST", "/start")
                finally:
                    self.maintenance = False

    def restore(self, name: str) -> None:
        if not re.fullmatch(r"backup-[0-9TZ]+\.tar\.gz", name):
            raise ValueError("Invalid backup identifier")
        source = self.store / name
        if not source.is_file():
            raise ValueError("Backup not found")
        with self.lock:
            # Always retain a safety copy; do not restart after restore until inspected.
            expected = self.backup_hash(source)
            protected = self.store / "restore-source.tar.gz"
            shutil.copyfile(source, protected)
            if self.digest(protected) != expected:
                raise ValueError("Backup checksum mismatch; restore cancelled")
            self.power("stop")
            self.backup(resume=False)
            staging = self.store / "restore-staging"
            shutil.rmtree(staging, ignore_errors=True)
            staging.mkdir()
            try:
                with tarfile.open(protected, mode="r:gz") as tar:
                    for m in tar.getmembers():
                        if (
                            not m.isfile()
                            or m.name.startswith("/")
                            or ".." in pathlib.PurePosixPath(m.name).parts
                        ):
                            raise ValueError("Unsafe archive")
                    tar.extractall(staging, filter="data")
                rollback = self.store / "restore-rollback"
                shutil.rmtree(rollback, ignore_errors=True)
                shutil.copytree(self.world, rollback)

                def clear_world() -> None:
                    for p in self.world.iterdir():
                        if p.is_dir():
                            shutil.rmtree(p)
                        else:
                            p.unlink()

                try:
                    clear_world()
                    for p in staging.iterdir():
                        shutil.move(str(p), self.world / p.name)
                except Exception:
                    clear_world()
                    for p in rollback.iterdir():
                        shutil.move(str(p), self.world / p.name)
                    raise
                self.alert(
                    "World restored. Server remains stopped; inspect before starting."
                )
            finally:
                shutil.rmtree(staging, ignore_errors=True)
                protected.unlink(missing_ok=True)

    def tick(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self.lock:
            s = self.agent("GET", "/status")
            # Only nonzero-exit crashes, three observations, at most two restarts/hour.
            crashed = self.desired and not s["running"] and s["exit_code"] != 0
            self.failures = self.failures + 1 if crashed else 0
            if self.failures == 1:
                self.alert("Crash detected. Review logs before restarting.")
            self.restarts = [x for x in self.restarts if now - x < 3600]
            if (
                self.config["auto_restart"]
                and self.failures >= 3
                and len(self.restarts) < 2
                and not self.maintenance
            ):
                self.restarts.append(now)
                write_json(self.store / "restarts.json", self.restarts)
                self.failures = 0
                self.alert("Crash restart attempted (maximum two/hour).")
                self.agent("POST", "/start")
            if (
                s["running"]
                and now - self.last_backup >= self.config["backup_hours"] * 3600
                and now - self.last_attempt >= 3600
            ):
                self.last_attempt = now
                self.backup()


def agent_client() -> Agent:
    token = (
        open(os.environ.get("AGENT_TOKEN_FILE", "secrets/agent-token")).read().strip()
    )
    url = os.environ.get("AGENT_URL", "http://127.0.0.1:8218")

    def call(method: str, path: str) -> dict[str, Any]:
        req = urllib.request.Request(
            url + path, method=method, headers={"Authorization": "Bearer " + token}
        )
        with urllib.request.urlopen(req, timeout=40) as r:
            return cast(dict[str, Any], json.load(r))

    return call
