from __future__ import annotations

from pathlib import Path

from summa_moral_graph.sft.preflight import (
    missing_required_paths,
    module_import_status,
    python_version_ok,
    writable_directory_status,
)


def test_python_version_ok_enforces_python_311_minimum() -> None:
    assert python_version_ok((3, 11, 0))
    assert python_version_ok((3, 12, 1))
    assert not python_version_ok((3, 10, 14))


def test_module_import_status_reports_present_and_missing_modules() -> None:
    status = module_import_status(["json", "definitely_missing_summa_module"])

    assert status["json"] is True
    assert status["definitely_missing_summa_module"] is False


def test_missing_required_paths_and_writable_directory_status(tmp_path) -> None:
    existing_path = tmp_path / "exists.txt"
    existing_path.write_text("fixture", encoding="utf-8")
    missing_path = tmp_path / "missing.txt"

    missing = missing_required_paths([existing_path, missing_path])
    writable_ok, writable_error = writable_directory_status(tmp_path / "nested" / "output")

    assert missing == [str(missing_path)]
    assert writable_ok is True
    assert writable_error is None
    assert Path(tmp_path / "nested" / "output").exists()
