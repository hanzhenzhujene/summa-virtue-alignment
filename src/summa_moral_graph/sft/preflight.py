"""Shared environment and filesystem checks for SFT preflight entrypoints."""

from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from .run_layout import ensure_writable_directory


def python_version_ok(
    version_info: tuple[int, int, int] | tuple[int, int, int, str, int],
    *,
    minimum: tuple[int, int] = (3, 11),
) -> bool:
    return (int(version_info[0]), int(version_info[1])) >= minimum


def module_import_status(module_names: list[str]) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for name in module_names:
        try:
            importlib.import_module(name)
        except Exception:
            status[name] = False
        else:
            status[name] = True
    return status


def missing_required_paths(paths: list[Path]) -> list[str]:
    return [str(path) for path in paths if not path.exists()]


def workspace_free_gb(path: Path) -> float:
    usage = shutil.disk_usage(path)
    return round(usage.free / (1024**3), 2)


def python_version_string() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def writable_directory_status(path: Path) -> tuple[bool, str | None]:
    try:
        ensure_writable_directory(path)
    except OSError as exc:
        return False, str(exc)
    return True, None
