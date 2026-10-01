"""Extended report tests."""

from pathlib import Path

import pytest

from northern_microgrid.report import load_json_results


def test_load_json_results(tmp_path: Path) -> None:
    p = tmp_path / "data.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    data = load_json_results(p)
    assert data["a"] == 1


def test_load_json_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_json_results(tmp_path / "missing.json")
