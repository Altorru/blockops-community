import io, pathlib, tarfile, tempfile, unittest
from blockops.core import Ops


class FakeAgent:
    def __init__(self):
        self.running = True
        self.exit = 0
        self.calls = []

    def __call__(self, method, path):
        self.calls.append(path)
        if path == "/status":
            return {"running": self.running, "exit_code": self.exit}
        if path == "/stop":
            self.running = False
        else:
            self.running = True
        return {"ok": True}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.world = self.root / "world"
        self.world.mkdir()
        (self.world / "level.dat").write_text("original")
        self.agent = FakeAgent()
        self.ops = Ops(self.world, self.root / "backups", self.agent)

    def tearDown(self):
        self.tmp.cleanup()

    def test_backup_restore_and_safety_copy(self):
        name = self.ops.backup()
        self.assertTrue(self.agent.running)
        (self.world / "level.dat").write_text("changed")
        self.ops.restore(name)
        self.assertEqual((self.world / "level.dat").read_text(), "original")
        self.assertFalse(self.agent.running)
        self.assertEqual(len(self.ops.backups()), 2)

    def test_forced_stop_refuses_backup_and_stays_stopped(self):
        self.agent.exit = 137
        with self.assertRaisesRegex(ValueError, "forcibly killed"):
            self.ops.backup()
        self.assertEqual(self.ops.backups(), [])
        self.assertFalse(self.agent.running)
        self.assertFalse(self.ops.desired)
        self.assertNotIn("/start", self.agent.calls)
        self.assertIn("Inspect server logs", self.ops.alerts[0]["message"])

    def test_unconfirmed_stop_never_copies_live_files(self):
        def ignores_stop(method, path):
            if path == "/stop":
                return {"ok": True}
            return self.agent(method, path)

        self.ops.agent = ignores_stop
        with self.assertRaisesRegex(ValueError, "still running"):
            self.ops.backup()
        self.assertEqual(self.ops.backups(), [])
        self.assertFalse(self.ops.desired)

    def test_retention(self):
        self.ops.config["retention"] = 2
        for _ in range(5):
            self.ops.backup()
        self.assertEqual(len(self.ops.backups()), 2)

    def test_oldest_restore_survives_safety_retention(self):
        self.ops.config["retention"] = 2
        name = self.ops.backup()
        (self.world / "level.dat").write_text("new")
        self.ops.backup()
        self.ops.restore(name)
        self.assertEqual((self.world / "level.dat").read_text(), "original")

    def test_config_invalid(self):
        for data in [
            {"backup_hours": 0, "retention": 7, "auto_restart": False},
            {"backup_hours": True, "retention": 7, "auto_restart": False},
            {"backup_hours": 24, "retention": 1, "auto_restart": False},
            {"backup_hours": 24, "retention": 7, "auto_restart": "yes"},
        ]:
            with self.assertRaises(ValueError):
                self.ops.configure(data)

    def test_manual_stop_never_auto_restarts(self):
        self.ops.config["auto_restart"] = True
        self.ops.power("stop")
        self.agent.exit = 137
        for _ in range(5):
            self.ops.tick(100)
        self.assertFalse(self.agent.running)

    def test_crash_threshold_and_budget(self):
        self.ops.config["auto_restart"] = True
        for _ in range(3):
            self.agent.running = False
            self.agent.exit = 1
            for _ in range(3):
                self.ops.tick(100)
        self.assertEqual(len(self.ops.restarts), 2)
        self.assertFalse(self.agent.running)

    def test_successful_exit_not_restarted(self):
        self.ops.config["auto_restart"] = True
        self.agent.running = False
        for _ in range(5):
            self.ops.tick(100)
        self.assertEqual(self.ops.restarts, [])

    def test_scheduled_copy(self):
        self.ops.tick(100000)
        self.assertEqual(len(self.ops.backups()), 1)

    def test_archive_traversal_rejected(self):
        name = "backup-20261007T000000Z.tar.gz"
        with tarfile.open(self.ops.store / name, "w:gz") as t:
            m = tarfile.TarInfo("../escape")
            m.size = 1
            t.addfile(m, io.BytesIO(b"x"))
        with self.assertRaises(ValueError):
            self.ops.restore(name)
        self.assertEqual((self.world / "level.dat").read_text(), "original")
        self.assertFalse((self.root / "escape").exists())

    def test_symlink_rejected(self):
        (self.world / "link").symlink_to(self.world / "level.dat")
        with self.assertRaises(ValueError):
            self.ops.backup()
        self.assertTrue(self.agent.running)

    def test_restart_budget_persists(self):
        self.ops.restarts = [10, 20]
        (self.ops.store / "restarts.json").write_text("[10,20]")
        reloaded = Ops(self.world, self.ops.store, self.agent)
        self.assertEqual(reloaded.restarts, [10, 20])

    def test_corrupt_archive_checksum_rejected(self):
        name = self.ops.backup()
        (self.ops.store / name).write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            self.ops.restore(name)
        self.assertEqual((self.world / "level.dat").read_text(), "original")

    def test_scheduled_failure_backoff(self):
        from unittest.mock import patch

        with patch.object(
            self.ops, "backup", side_effect=OSError("disk full")
        ) as backup:
            with self.assertRaises(OSError):
                self.ops.tick(100000)
            self.ops.tick(100020)
            self.assertEqual(backup.call_count, 1)

    def test_failed_restart_consumes_budget(self):
        self.ops.config["auto_restart"] = True
        self.agent.running = False
        self.agent.exit = 1

        def failed(method, path):
            if path == "/start":
                raise OSError("unavailable")
            return self.agent(method, path)

        self.ops.agent = failed
        self.ops.tick(100)
        self.ops.tick(120)
        with self.assertRaises(OSError):
            self.ops.tick(140)
        self.assertEqual(len(self.ops.restarts), 1)

    def test_bad_restore_id(self):
        with self.assertRaises(ValueError):
            self.ops.restore("../../secret")


if __name__ == "__main__":
    unittest.main()
