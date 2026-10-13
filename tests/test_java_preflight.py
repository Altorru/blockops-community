import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("java_preflight", Path(__file__).resolve().parents[1] / "scripts/preflight_java.py")
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class JavaGateTests(unittest.TestCase):
    def test_empty_target_never_calls_docker(self):
        with patch.object(preflight.subprocess, "check_output") as docker:
            self.assertEqual(preflight.preflight({})["status"], "blocked")
            docker.assert_not_called()

    def test_existing_eula_required_then_public_port_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory); world = data / "world"; world.mkdir()
            config = {"container": "blockops-java-drill", "data_path": str(data),
                      "world_path": str(world), "network": "java-private",
                      "owner_authorization_reference": "synthetic test only", "disposable": True}
            with patch.object(preflight.subprocess, "check_output") as docker:
                self.assertEqual(preflight.preflight(config)["status"], "blocked")
                docker.assert_not_called()
            # Synthetic data tests the gate; no Minecraft EULA is accepted.
            (data / "eula.txt").write_text("eula=true\n")
            inspect = {"Name": "/blockops-java-drill", "Image": "sha256:synthetic",
                       "Mounts": [{"Type": "bind", "Source": str(data)}],
                       "State": {"Running": False},
                       "HostConfig": {"RestartPolicy": {"Name": "no"}, "PortBindings": {}},
                       "NetworkSettings": {"Networks": {"java-private": {}}}}
            with patch.object(preflight.subprocess, "check_output", return_value=json.dumps([inspect])):
                result = preflight.preflight(config)
                self.assertEqual(result["status"], "ready_for_authorized_drill")
                self.assertFalse(result["mutations"])
                self.assertFalse(result["real_java_backup_restore_verified"])
            inspect["HostConfig"]["PortBindings"] = {"25565/tcp": [{"HostIp": "0.0.0.0"}]}
            with patch.object(preflight.subprocess, "check_output", return_value=json.dumps([inspect])):
                with self.assertRaises(ValueError):
                    preflight.preflight(config)
