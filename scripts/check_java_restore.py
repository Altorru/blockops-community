"""Read-only comparison of all backup file hashes against a stopped test world.

This does not stop, restore, or start any server, nor accept an EULA.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest(stream):
    result = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(chunk)
    return result.hexdigest()


def compare(archive, world):
    world = world.resolve(strict=True)
    checked = []
    names = set()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or member.name in names:
                raise ValueError("Unsafe or duplicate archive entry")
            names.add(member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Archive contains a non-regular file")
            target = world.joinpath(*name.parts)
            if any(part.is_symlink() for part in [target, *target.parents] if part != world.parent):
                raise ValueError("World path contains a symbolic link")
            if not target.is_file() or not target.resolve().is_relative_to(world):
                checked.append({"file": member.name, "match": False, "reason": "missing"})
                continue
            with tar.extractfile(member) as expected, target.open("rb") as actual:
                a, b = digest(expected), digest(actual)
            checked.append({"file": member.name, "archive_sha256": a,
                            "world_sha256": b, "match": a == b})
    if not checked:
        raise ValueError("Archive contains no regular files")
    expected_files = {entry["file"] for entry in checked}
    extra = []
    for item in world.rglob("*"):
        if item.is_symlink():
            raise ValueError("World contains a symbolic link")
        if item.is_file() and item.relative_to(world).as_posix() not in expected_files:
            extra.append(item.relative_to(world).as_posix())
    return {"read_only": True, "files": checked, "extra_files": sorted(extra),
            "all_match": all(entry["match"] for entry in checked) and not extra,
            "java_boot_verified": False, "stop_verified": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("world", type=Path)
    args = parser.parse_args()
    result = compare(args.archive, args.world)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["all_match"] else 1)
