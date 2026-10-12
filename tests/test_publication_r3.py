"""Known-answer and release contracts for the twelve round-three findings."""

import copy
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from northern_microgrid.dispatch import aggregate_metrics, simulate_hourly
from northern_microgrid.evaluation import composite_score
from northern_microgrid.results_doc import generate_results_markdown
from northern_microgrid.types import BatteryConfig, DieselConfig, PvConfig, SystemDesign, WindConfig
from northern_microgrid.weather import align_weather_hours

ROOT = Path(__file__).resolve().parents[1]


def test_f01_storage_source_and_conversion_loss() -> None:
    design = SystemDesign(
        PvConfig(100, 90, derate=1),
        WindConfig(0),
        BatteryConfig(50, 200),
        DieselConfig(80),
    )
    dispatch = simulate_hourly(
        np.array([0.0, 40.0]),
        np.array([1000.0, 0.0]),
        np.full(2, 25.0),
        np.zeros(2),
        np.zeros(2),
        design,
    )
    eff = 0.92**0.5
    expected_credit = 40 * (50 * eff) / (110 + 50 * eff)
    assert dispatch.renewable_to_load_kw[1] == pytest.approx(expected_credit)
    metrics = aggregate_metrics(dispatch, design.diesel)
    assert metrics.battery_storage_loss_kwh == pytest.approx(50 * (1 - eff) + 40 / eff - 40)
    assert 100 + metrics.diesel_kwh + metrics.initial_soc_kwh == pytest.approx(
        40
        + metrics.curtailed_kwh
        + metrics.diesel_dump_kwh
        + metrics.battery_storage_loss_kwh
        + metrics.terminal_soc_kwh
    )


def test_f02_no_obsolete_public_conclusions() -> None:
    for name in ["M0", "M1", "M2", "M3"]:
        text = (ROOT / f"docs/milestones/{name}_REPORT.md").read_text()
        assert "Superseded" in text.splitlines()[2]
        assert not re.search(r"142 MB|H[13].*PASS|ground truth|17\.4.?24\.5", text)
    assert "17-25%" not in (ROOT / "docs/technical-report.md").read_text()


def test_f03_subset_failed_outcomes_are_reported() -> None:
    results = copy.deepcopy(json.loads((ROOT / "results/evaluation_results.json").read_text()))
    site = results["sites"]["iqaluit"]
    results["sites"] = {"iqaluit": site}
    results["archetype"] = "research_station"
    site["optimized_design"]["wind"]["capacity_kw"] = 10
    year = str(results["weather_years"][0])
    site["year_metrics"][year]["metrics"]["unmet_fraction"] = 0.25
    site["year_metrics"][year]["lifecycle"]["npc_cad"] = (
        1.5 * site["baselines"]["diesel_only"]["npc_cad"]
    )
    text = generate_results_markdown(results, "test")
    assert "50.0% higher" in text
    assert "25.000%" in text
    assert "| Step | Iqaluit |" in text
    assert "| Step | Iqaluit | Inuvik" not in text
    assert "H1: untested" in text
    assert "Iqaluit: 10.0 kW" in text
    assert "0.000% unmet" not in text


def test_f03_single_year_and_relaxed_search_do_not_copy_hypotheses() -> None:
    results = copy.deepcopy(json.loads((ROOT / "results/evaluation_results.json").read_text()))
    site = results["sites"]["iqaluit"]
    results["sites"] = {"iqaluit": site}
    year = str(results["weather_years"][0])
    results["weather_years"] = [int(year)]
    site["year_metrics"] = {year: site["year_metrics"][year]}
    site["year_metrics"][year]["metrics"]["unmet_fraction"] = 0.02
    site["year_metrics"][year]["lifecycle"]["npc_cad"] = (
        0.5 * site["baselines"]["diesel_only"]["npc_cad"]
    )
    results["run_metadata"]["search_constraints"]["max_unmet_fraction"] = 0.25
    text = generate_results_markdown(results, "test")
    assert "met at 0 of 1" in text
    assert "H2: untested" in text
    assert "mean of 1 evaluated weather years" in text
    assert "five-year mean" not in text


def test_f04_portable_constraints_are_used() -> None:
    text = (ROOT / "constraints.txt").read_text()
    assert not re.search(r"^-e |/Users/|file://", text, re.M)
    for name in ["README.md", "CONTRIBUTING.md", ".github/workflows/ci.yml"]:
        assert "-c constraints.txt" in (ROOT / name).read_text()
    assert "hatchling==" in text


def test_f05_raw_manifest_hashes_and_leap_calendar() -> None:
    manifest = json.loads((ROOT / "data/weather/manifest.json").read_text())
    assert len(manifest["files"]) == 20
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        df = pd.read_parquet(path)
        assert len(df) == entry["rows"] == (8784 if entry["year"] == 2020 else 8760)
        assert entry["acquired_at"] is None


def test_f06_license_scope_is_explicit() -> None:
    text = (ROOT / "docs/LICENSING.md").read_text()
    for path in ["src/", "tests/", "README.md", "RESULTS.md", "results/", "data/weather/"]:
        assert path in text
    assert "CC BY 4.0" in text and "Apache-2.0" in text
    assert "LICENSING.md" in (ROOT / "README.md").read_text()


def test_f07_prior_art_revisions_and_bounded_contribution() -> None:
    text = (ROOT / "docs/PRIOR_ART.md").read_text()
    for repo, sha in [
        ("Sas1997/SAMA", "383d229a51c380bb923e2f284e2e3f5466a2f9ff"),
        ("sambaenergies/samba", "fc5b8b5c11b0f4a89031680c0c6f2a568c17fb45"),
        ("MicroGridsPy/ECOS_2024_MultiGood", "9ddae36012efe7bb1c726504d2b6b073ba7b66df"),
    ]:
        assert f"{repo}/blob/{sha}/README.md#" in text
    assert "10.1016/j.enconman.2023.117686" in text
    assert "none bundle" not in (ROOT / "README.md").read_text()


def test_f08_limits_and_sensitivity_cover_material_assumptions() -> None:
    from northern_microgrid.sensitivity import sensitivity_cases

    cases = sensitivity_cases()
    assert {
        "fuel_low",
        "fuel_high",
        "capex_high",
        "replacements",
        "snow_high",
        "battery_no_temp_penalty",
    } <= set(cases)
    for path in ["README.md", "RESULTS.md", "results/report_iqaluit.html"]:
        text = (ROOT / path).read_text().lower()
        for limitation in [
            "azimuth",
            "10 m wind",
            "replacement",
            "five-year mean",
            "unlimited fuel",
            "simulation-only",
        ]:
            assert limitation in text


def test_f09_metadata_binds_actual_protocol_and_inputs() -> None:
    results = json.loads((ROOT / "results/evaluation_results.json").read_text())
    metadata = results["run_metadata"]
    assert (
        metadata["protocol_sha256"]
        == hashlib.sha256((ROOT / "docs/PREREGISTRATION.md").read_bytes()).hexdigest()
    )
    assert (
        metadata["constraints_sha256"]
        == hashlib.sha256((ROOT / "constraints.txt").read_bytes()).hexdigest()
    )
    assert len(metadata["cache_sha256"]) == 20
    assert metadata["code_sha256"] and metadata["dependencies"] and metadata["search_constraints"]
    code_hash = hashlib.sha256()
    for path in sorted((ROOT / "src").rglob("*.py")):
        code_hash.update(str(path.relative_to(ROOT)).encode())
        code_hash.update(path.read_bytes())
    assert metadata["code_sha256"] == code_hash.hexdigest()
    for name, expected_hash in metadata["cache_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected_hash
    assert "pre-result chronology is unverified" in (ROOT / "docs/PREREGISTRATION.md").read_text()
    assert (ROOT / "docs/PROTOCOL_DEVIATIONS.md").exists()


def test_f10_cost_score_distinguishes_sub_baseline_savings() -> None:
    equal = composite_score(0, 0.5, 100, 100)
    cheaper = composite_score(0, 0.5, 80, 100)
    cheapest = composite_score(0, 0.5, 50, 100)
    assert equal < cheaper < cheapest < 1


@pytest.mark.parametrize("damage", ["gap", "year", "order"])
def test_f11_reject_incomplete_or_wrong_calendar(damage: str) -> None:
    df = pd.read_parquet(ROOT / "data/weather/iqaluit/2018.parquet")
    if damage == "gap":
        df = df.drop(index=100).reset_index(drop=True)
    elif damage == "year":
        df.loc[0, "timestamp"] = pd.Timestamp("2019-01-01", tz="UTC")
    else:
        df = df.iloc[::-1].reset_index(drop=True)
    with pytest.raises(ValueError, match="calendar"):
        align_weather_hours(df)


def test_f12_public_author_exception_and_payload_exclusions() -> None:
    text = (ROOT / "docs/LICENSING.md").read_text()
    assert "The author is credited by name in the citation file and the technical report." in text
    ignore = (ROOT / ".gitignore").read_text()
    assert ".review/" in ignore and "state/*.bundle" in ignore
    assert (ROOT / "scripts/audit_release.py").exists()


def test_storage_full_ledger_detects_tampering() -> None:
    from northern_microgrid.dispatch import assert_energy_conservation

    design = SystemDesign(PvConfig(0, 45), WindConfig(0), BatteryConfig(0, 0), DieselConfig(100))
    dispatch = simulate_hourly(
        np.full(2, 5.0), np.zeros(2), np.full(2, 25.0), np.zeros(2), np.zeros(2), design
    )
    assert_energy_conservation(dispatch)
    dispatch.curtailed_kw[0] += 10
    with pytest.raises(ValueError, match="Full system"):
        assert_energy_conservation(dispatch)


def test_protocol_and_data_hashes_reject_tampering(tmp_path: Path) -> None:
    from northern_microgrid.provenance import run_metadata, verify_data_manifest
    from northern_microgrid.results_doc import write_results_markdown
    from northern_microgrid.sizing import SizingConstraints

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/PREREGISTRATION.md").write_text("actual protocol")
    (tmp_path / "docs/PREREGISTRATION.sha256").write_text("wrong digest")
    with pytest.raises(ValueError, match="Protocol"):
        run_metadata(tmp_path, [], SizingConstraints())
    (tmp_path / "results").mkdir()
    (tmp_path / "results/evaluation_results.json").write_text("{}")
    with pytest.raises(ValueError, match="Protocol"):
        write_results_markdown(tmp_path)
    weather = tmp_path / "data/weather"
    weather.mkdir(parents=True)
    (weather / "bad.parquet").write_bytes(b"bad")
    (weather / "manifest.json").write_text(
        json.dumps(
            {"files": [{"path": "data/weather/bad.parquet", "sha256": "invalid", "rows": 8760}]}
        )
    )
    with pytest.raises(ValueError, match="manifest mismatch"):
        verify_data_manifest(tmp_path)
    verify_data_manifest(ROOT)


def test_download_records_calendar_and_metadata(tmp_path: Path) -> None:
    from unittest.mock import patch

    from northern_microgrid.weather import fetch_weather_year, load_weather_year

    raw = pd.read_parquet(ROOT / "data/weather/iqaluit/2018.parquet")
    with (
        patch("northern_microgrid.weather.fetch_weather_chunk", return_value=raw),
        patch("northern_microgrid.weather.time.sleep"),
    ):
        path = fetch_weather_year(63.75, -68.52, 2018, tmp_path, "iqaluit")
    assert len(load_weather_year(path)) == 8760
    assert path.with_suffix(".metadata.json").exists()
    assert fetch_weather_year(63.75, -68.52, 2018, tmp_path, "iqaluit") == path
    with pytest.raises(ValueError, match="site/year metadata"):
        fetch_weather_year(0, 0, 2018, tmp_path, "iqaluit")
    metadata_path = path.with_suffix(".metadata.json")
    metadata = json.loads(metadata_path.read_text())
    metadata["site_id"] = "whitehorse"
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="site metadata"):
        load_weather_year(path)
    metadata["site_id"] = "iqaluit"
    metadata["latitude"] = 0
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="coordinates"):
        load_weather_year(path)
    metadata["latitude"] = 63.75
    metadata["year"] = 2019
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="year metadata"):
        load_weather_year(path)
    metadata["year"] = 2018
    metadata["sha256"] = "wrong"
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="hash mismatch"):
        load_weather_year(path)


def test_shipped_metadata_required_and_bound() -> None:
    from northern_microgrid.weather import _cache_metadata, load_weather_year

    assert _cache_metadata(ROOT / "data/weather/iqaluit/2018.parquet")["year"] == 2018
    assert len(load_weather_year(ROOT / "data/weather/iqaluit/2020.parquet")) == 8760
    with pytest.raises(ValueError, match="absent from source manifest"):
        _cache_metadata(ROOT / "data/weather/iqaluit/2030.parquet")


def test_sensitivity_stresses_change_costs_in_expected_direction() -> None:
    from northern_microgrid.sensitivity import run_sensitivity

    load = np.full(48, 10.0)
    weather = pd.DataFrame(
        {
            "ghi_wh_m2": np.full(48, 100.0),
            "temp_c": np.full(48, -20.0),
            "wind_ms": np.zeros(48),
            "precip_mm_hr": np.full(48, 5.0),
        }
    )
    design = SystemDesign(
        PvConfig(100, 45),
        WindConfig(0),
        BatteryConfig(20, 100),
        DieselConfig(20, min_load_fraction=0),
    )
    rows = run_sensitivity(load, weather, design)
    base = rows["base"]["npc_cad"]
    assert rows["fuel_low"]["npc_cad"] < base < rows["fuel_high"]["npc_cad"]
    assert rows["capex_high"]["npc_cad"] > base
    assert rows["replacements"]["npc_cad"] > base
    assert rows["snow_high"]["npc_cad"] >= base
    assert rows["battery_no_temp_penalty"]["npc_cad"] <= base
    assert (
        rows["fuel_low"]["diesel_baseline_npc_cad"] < rows["fuel_high"]["diesel_baseline_npc_cad"]
    )
