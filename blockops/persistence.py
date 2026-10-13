"""Atomic local state writes. Files are private and never partially replaced."""

import json
import os
import pathlib
import tempfile
from typing import Any


def write_json(path: pathlib.Path, value: Any) -> None:
    temporary: pathlib.Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as f:
            temporary = pathlib.Path(f.name)
            json.dump(value, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
