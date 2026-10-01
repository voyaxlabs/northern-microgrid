"""Tests for weather hour alignment."""

import pandas as pd
import pytest

from northern_microgrid.weather import align_weather_hours


def test_truncate_leap_year() -> None:
    df = pd.DataFrame(
        {
            "ghi_wh_m2": [100.0] * 8784,
            "temp_c": 0.0,
            "wind_ms": 5.0,
            "precip_mm_hr": 0.0,
            "timestamp": pd.date_range("2020-01-01", periods=8784, freq="h", tz="UTC"),
        }
    )
    aligned = align_weather_hours(df, 8760)
    assert len(aligned) == 8760


def test_reject_short_year() -> None:
    df = pd.DataFrame({"ghi_wh_m2": range(100), "temp_c": 0.0, "wind_ms": 5.0, "precip_mm_hr": 0.0})
    with pytest.raises(ValueError, match="calendar"):
        align_weather_hours(df, 200)
