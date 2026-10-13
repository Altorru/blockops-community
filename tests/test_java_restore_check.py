import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("restore_check", Path(__file__).resolve().parents[1] / "scripts/check_java_restore.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class RestoreProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.world = self.root / "world"
        self.world.mkdir()
        self.archive = self.root / "backup.tar.gz"

    def pack(self, entries):
        with tarfile.open(self.archive, "w:gz") as tar:
            for name, data in entries:
                item = tarfile.TarInfo(name)
                item.size = len(data)
                tar.addfile(item, io.BytesIO(data))

    def test_full_match_then_changed_file_and_extra_detected(self):
        (self.world / "level.dat").write_bytes(b"binary fixture\x00")
        (self.world / "region").mkdir()
        (self.world / "region/r.0.0.mca").write_bytes(b"region fixture")
        self.pack([("level.dat", b"binary fixture\x00"), ("region/r.0.0.mca", b"region fixture")])
        self.assertTrue(check.compare(self.archive, self.world)["all_match"])
        (self.world / "region/r.0.0.mca").write_bytes(b"changed")
        self.assertFalse(check.compare(self.archive, self.world)["all_match"])
        (self.world / "extra").write_bytes(b"extra")
        self.assertEqual(check.compare(self.archive, self.world)["extra_files"], ["extra"])

    def test_missing_file_detected(self):
        self.pack([("missing.dat", b"data")])
        self.assertFalse(check.compare(self.archive, self.world)["all_match"])

    def test_traversal_rejected_without_writes(self):
        self.pack([("../outside", b"data")])
        with self.assertRaises(ValueError):
            check.compare(self.archive, self.world)
        self.assertFalse((self.root / "outside").exists())

    def test_duplicate_rejected(self):
        self.pack([("same", b"a"), ("same", b"b")])
        with self.assertRaises(ValueError):
            check.compare(self.archive, self.world)

    def test_world_symlink_rejected(self):
        outside = self.root / "outside"
        outside.write_bytes(b"data")
        (self.world / "link").symlink_to(outside)
        self.pack([("link", b"data")])
        with self.assertRaises(ValueError):
            check.compare(self.archive, self.world)
