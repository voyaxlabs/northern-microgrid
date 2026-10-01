"""Public CLI contracts for round-four missing-cache acquisition."""

import hashlib
import json
import shutil
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest
from click.testing import CliRunner

from northern_microgrid import pipeline, weather
from northern_microgrid.cli import main
from northern_microgrid.sizing import SizingConstraints, optimize_design

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path("data/weather/iqaluit/2018.parquet")


@pytest.fixture
def cache_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "data/weather", tmp_path / "data/weather")
    return tmp_path


def test_cli_acquires_missing_manifest_cache(cache_root: Path, monkeypatch) -> None:
    raw = pd.read_parquet(cache_root / CACHE)
    expected_bytes = (cache_root / CACHE).read_bytes()
    (cache_root / CACHE).unlink()
    chunks = []

    def fake_chunk(latitude, longitude, start, end, session):
        assert (latitude, longitude) == (63.75, -68.52)
        chunks.append((start, end))
        ts = raw["timestamp"]
        return raw.loc[
            (ts >= pd.Timestamp(start, tz="UTC"))
            & (ts < pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1))
        ].reset_index(drop=True)

    monkeypatch.setattr(weather, "fetch_weather_chunk", fake_chunk)
    monkeypatch.setattr(weather.time, "sleep", lambda _: None)
    small = SizingConstraints(
        pv_kw_range=(0, 0, 10), wind_kw_range=(0, 0, 10), battery_kwh_range=(0, 0, 10)
    )

    def small_optimizer(load, weather_opt, peak_kw, constraints):
        assert (cache_root / CACHE).read_bytes() == expected_bytes
        assert (cache_root / CACHE).with_suffix(".metadata.json").exists()
        return optimize_design(load, weather_opt, peak_kw, constraints=small)

    monkeypatch.setattr(pipeline, "optimize_design", small_optimizer)
    monkeypatch.chdir(cache_root)
    result = CliRunner().invoke(main, ["run", "--root", "."])
    assert result.exit_code == 0, result.output + repr(result.exception)
    assert len(chunks) == 13
    assert "Sites evaluated: iqaluit, inuvik, whitehorse, dease_lake" in result.output
    actual = json.loads((cache_root / "results/evaluation_results.json").read_text())
    manifest = json.loads((cache_root / "data/weather/manifest.json").read_text())
    assert actual["run_metadata"]["cache_sha256"] == {
        record["path"]: record["sha256"] for record in manifest["files"]
    }
    assert len(actual["sites"]) == 4


@pytest.mark.parametrize("no_fetch", [False, True])
def test_cli_rejects_modified_inventory_before_fetch(
    cache_root: Path, monkeypatch, no_fetch: bool
) -> None:
    (cache_root / CACHE).unlink()
    # A later site's present cache must fail before any missing cache is acquired.
    (cache_root / "data/weather/whitehorse/2022.parquet").write_bytes(b"modified")
    fetch = Mock(side_effect=AssertionError("must not fetch"))
    simulation = Mock(side_effect=AssertionError("must not simulate"))
    monkeypatch.setattr(pipeline, "fetch_weather_year", fetch)
    monkeypatch.setattr(pipeline, "optimize_design", simulation)
    args = ["run", "--root", str(cache_root)] + (["--no-fetch"] if no_fetch else [])
    result = CliRunner().invoke(main, args)
    assert result.exit_code != 0
    assert isinstance(result.exception, (ValueError, FileNotFoundError))
    fetch.assert_not_called()
    simulation.assert_not_called()


def test_cli_no_fetch_rejects_missing_cache(cache_root: Path, monkeypatch) -> None:
    (cache_root / CACHE).unlink()
    fetch = Mock(side_effect=AssertionError("must not fetch"))
    simulation = Mock(side_effect=AssertionError("must not simulate"))
    monkeypatch.setattr(pipeline, "fetch_weather_year", fetch)
    monkeypatch.setattr(pipeline, "optimize_design", simulation)
    result = CliRunner().invoke(main, ["run", "--root", str(cache_root), "--no-fetch"])
    assert isinstance(result.exception, FileNotFoundError)
    fetch.assert_not_called()
    simulation.assert_not_called()


def test_cli_does_not_acquire_unrequested_missing_cache(cache_root: Path, monkeypatch) -> None:
    (cache_root / CACHE).unlink()
    fetch = Mock(side_effect=AssertionError("must not fetch"))
    monkeypatch.setattr(pipeline, "fetch_weather_year", fetch)
    result = CliRunner().invoke(main, ["run", "--root", str(cache_root), "--site", "inuvik"])
    assert isinstance(result.exception, FileNotFoundError)
    fetch.assert_not_called()


@pytest.mark.parametrize(
    ("damage", "message"),
    [
        ("hash", "manifest mismatch"),
        ("rows", "manifest mismatch"),
        ("calendar", "calendar"),
        ("values", "physical range"),
        ("site", "site metadata"),
        ("coordinates", "coordinates"),
        ("year", "year metadata"),
    ],
)
def test_cli_validates_acquired_cache_before_simulation(
    cache_root: Path, monkeypatch, damage: str, message: str
) -> None:
    path = cache_root / CACHE
    raw = pd.read_parquet(path)
    manifest_path = cache_root / "data/weather/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    record = next(record for record in manifest["files"] if record["path"] == str(CACHE))
    if damage == "calendar":
        raw.loc[100, "timestamp"] = raw.loc[99, "timestamp"]
    elif damage == "values":
        raw.loc[100, "ghi_wh_m2"] = -1.0
    elif damage == "hash":
        raw.loc[100, "temp_c"] += 0.1
    elif damage == "rows":
        raw = raw.iloc[:-1]
    raw.to_parquet(path, index=False)
    fetched_bytes = path.read_bytes()
    fetched_hash = hashlib.sha256(fetched_bytes).hexdigest()
    # Isolate weather validators using an inventory that agrees with invalid content.
    if damage in {"calendar", "values"}:
        record["sha256"] = fetched_hash
    elif damage == "rows":
        record["sha256"] = fetched_hash  # Raw row policy must still reject it.
    manifest_path.write_text(json.dumps(manifest))
    metadata = dict(record, sha256=fetched_hash)
    if damage == "site":
        metadata["site_id"] = "whitehorse"
    elif damage == "coordinates":
        metadata["latitude"] = 0.0
    elif damage == "year":
        metadata["year"] = 2019
    path.unlink()

    def fake_fetch(latitude, longitude, year, weather_dir, site_id):
        assert not path.exists()
        path.write_bytes(fetched_bytes)
        path.with_suffix(".metadata.json").write_text(json.dumps(metadata))
        return path

    fetch = Mock(side_effect=fake_fetch)
    simulation = Mock(side_effect=AssertionError("must not simulate"))
    monkeypatch.setattr(pipeline, "fetch_weather_year", fetch)
    monkeypatch.setattr(pipeline, "optimize_design", simulation)
    result = CliRunner().invoke(main, ["run", "--root", str(cache_root)])
    assert isinstance(result.exception, ValueError)
    assert message in str(result.exception)
    fetch.assert_called_once()
    simulation.assert_not_called()
