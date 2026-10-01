"""Tests for weather validation and leap-day handling."""

import pandas as pd
import pytest

from northern_microgrid.weather import (
    align_weather_hours,
    drop_leap_day_hours,
    validate_weather_frame,
)


def _valid_df(n: int = 8760) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2019-01-01", periods=n, freq="h", tz="UTC"),
            "ghi_wh_m2": [100.0] * n,
            "temp_c": [-5.0] * n,
            "wind_ms": [5.0] * n,
            "precip_mm_hr": [0.0] * n,
        }
    )


def test_drop_leap_day_removes_feb29() -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2020-01-01", periods=8784, freq="h", tz="UTC"),
            "ghi_wh_m2": [100.0] * 8784,
            "temp_c": [-5.0] * 8784,
            "wind_ms": [5.0] * 8784,
            "precip_mm_hr": [0.0] * 8784,
        }
    )
    trimmed = drop_leap_day_hours(df)
    assert len(trimmed) == 8760


def test_align_weather_rejects_sentinel() -> None:
    df = _valid_df(8760)
    df.loc[0, "temp_c"] = -999.0
    with pytest.raises(ValueError, match="fill value"):
        validate_weather_frame(df)


def test_align_weather_rejects_duplicates() -> None:
    df = _valid_df(100)
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        validate_weather_frame(df)


def test_align_weather_hours_leap_year() -> None:
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2020-01-01", periods=8784, freq="h", tz="UTC"),
            "ghi_wh_m2": [100.0] * 8784,
            "temp_c": [-5.0] * 8784,
            "wind_ms": [5.0] * 8784,
            "precip_mm_hr": [0.0] * 8784,
        }
    )
    aligned = align_weather_hours(df, 8760)
    assert len(aligned) == 8760
