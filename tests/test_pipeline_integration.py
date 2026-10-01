"""Integration tests for pipeline (mocked weather)."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from northern_microgrid.pipeline import run_pipeline
from northern_microgrid.sizing import SizingConstraints


def _fake_weather(n: int = 8760) -> pd.DataFrame:
    hours = np.arange(n)
    ghi = np.maximum(0, 400 * np.sin(np.pi * (hours % 24 - 6) / 12))
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2018-01-01", periods=n, freq="h", tz="UTC"),
            "ghi_wh_m2": ghi,
            "temp_c": np.full(n, -10.0),
            "wind_ms": np.full(n, 5.0),
            "precip_mm_hr": np.zeros(n),
            "par_wh_m2": ghi * 0.5,
        }
    )


@patch("northern_microgrid.pipeline.fetch_weather_year")
def test_pipeline_single_site(mock_fetch, tmp_path: Path) -> None:
    weather_dir = tmp_path / "data" / "weather" / "iqaluit"
    weather_dir.mkdir(parents=True)
    fake = _fake_weather()
    for year in [2018]:
        fake.to_parquet(weather_dir / f"{year}.parquet", index=False)

    def _side_effect(lat, lon, year, wdir, site_id, force=False):
        p = wdir / site_id / f"{year}.parquet"
        if not p.exists():
            fake.to_parquet(p, index=False)
        return p

    mock_fetch.side_effect = _side_effect

    constraints = SizingConstraints(
        pv_kw_range=(0.0, 40.0, 20.0),
        wind_kw_range=(0.0, 0.0, 10.0),
        battery_kwh_range=(0.0, 100.0, 50.0),
    )

    results = run_pipeline(
        tmp_path,
        site_ids=["iqaluit"],
        weather_years=[2018],
        fetch_weather=True,
        constraints=constraints,
    )
    assert "iqaluit" in results["sites"]
    assert (tmp_path / "results" / "evaluation_results.json").exists()
