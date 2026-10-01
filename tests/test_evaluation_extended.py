"""Extended evaluation tests."""

from pathlib import Path

import numpy as np
import pandas as pd

from northern_microgrid.evaluation import (
    optimize_for_site,
    run_baseline_comparison,
    run_case_study,
    serialize_results,
)
from northern_microgrid.sites import get_site
from northern_microgrid.sizing import diesel_only_design, fixed_renewable_design


def _weather_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2018-01-01", periods=8760, freq="h", tz="UTC"),
            "ghi_wh_m2": np.full(8760, 350.0),
            "temp_c": np.full(8760, -8.0),
            "wind_ms": np.full(8760, 5.0),
            "precip_mm_hr": np.zeros(8760),
        }
    )


def test_run_case_study(tmp_path: Path) -> None:
    weather = _weather_df()
    wp = tmp_path / "2018.parquet"
    weather.to_parquet(wp, index=False)
    site = get_site("whitehorse")
    design = diesel_only_design(peak_kw=100.0)
    case = run_case_study(site, 2018, wp, "remote_camp", design)
    assert case.metrics.total_load_kwh > 0


def test_baseline_comparison(tmp_path: Path) -> None:
    weather = _weather_df()
    wp = tmp_path / "2018.parquet"
    weather.to_parquet(wp, index=False)
    site = get_site("whitehorse")
    opt = fixed_renewable_design(85.0, 50.0, 10.0, 100.0)
    results = run_baseline_comparison(site, wp, "remote_camp", opt, 85.0, 480.0)
    assert "diesel_only" in results
    assert "optimized" in results


def test_serialize_results(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    serialize_results({"key": "value"}, out)
    assert out.exists()


def test_optimize_for_site(tmp_path: Path) -> None:
    from northern_microgrid.sizing import SizingConstraints

    weather = _weather_df()
    wp = tmp_path / "2018.parquet"
    weather.to_parquet(wp, index=False)
    site = get_site("dease_lake")
    constraints = SizingConstraints(
        pv_kw_range=(0.0, 30.0, 15.0),
        wind_kw_range=(0.0, 0.0, 10.0),
        battery_kwh_range=(0.0, 50.0, 25.0),
    )
    design = optimize_for_site(site, wp, "remote_camp", constraints)
    assert design.pv.capacity_kw >= 0
