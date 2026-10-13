"""Read-only gate for the exact disposable Java target. Never accepts EULA."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def preflight(config):
    required = ["container", "data_path", "world_path", "network", "owner_authorization_reference"]
    missing = [key for key in required if not config.get(key)]
    if missing or config.get("disposable") is not True:
        return {"status": "blocked", "missing": missing, "reason": "Exact disposable target not identified", "mutations": False}
    name = config["container"]
    if not re.fullmatch(r"blockops-java-drill[-a-zA-Z0-9_]*", name):
        raise ValueError("Dedicated blockops-java-drill container required")
    data = Path(config["data_path"]).resolve(strict=True)
    world = Path(config["world_path"]).resolve(strict=True)
    if not data.is_dir() or not world.is_dir() or not world.is_relative_to(data) or world == data:
        raise ValueError("Test world must be a dedicated child of the data bind")
    eula = data / "eula.txt"
    if eula.is_symlink() or not eula.is_file() or not re.search(r"^\s*eula\s*=\s*true\s*$", eula.read_text(), re.M):
        return {"status": "blocked", "reason": "Existing owner-accepted eula.txt missing", "mutations": False}
    inspection = json.loads(subprocess.check_output(["docker", "container", "inspect", name], text=True))[0]
    if inspection["Name"].lstrip("/") != name or inspection["HostConfig"]["RestartPolicy"]["Name"] not in ["no", ""]:
        raise ValueError("Exact target with restart disabled required")
    if not any(m["Type"] == "bind" and Path(m["Source"]).resolve() == data for m in inspection["Mounts"]):
        raise ValueError("Data bind does not match the inspected target")
    if config["network"] not in inspection["NetworkSettings"]["Networks"]:
        raise ValueError("Private target network does not match")
    ports = inspection["HostConfig"].get("PortBindings") or {}
    if any(p.get("HostIp") not in ["127.0.0.1", "::1"] for bindings in ports.values() for p in bindings or []):
        raise ValueError("Public target ports forbidden for this drill")
    return {"status": "ready_for_authorized_drill", "container": name,
            "image_id": inspection["Image"], "running": inspection["State"]["Running"],
            "owner_reference": config["owner_authorization_reference"],
            "existing_eula_true": True, "mutations": False,
            "real_java_backup_restore_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    result = preflight(json.loads(args.target.read_text()))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "ready_for_authorized_drill" else 2)
