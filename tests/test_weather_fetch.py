"""Tests for weather fetch and parse (mocked)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from northern_microgrid.weather import (
    _parse_power_response,
    fetch_weather_year,
    weather_cache_path,
)

SAMPLE_PAYLOAD = {
    "properties": {
        "parameter": {
            "ALLSKY_SFC_SW_DWN": {"2023010100": 0.0, "2023010112": 250.0},
            "T2M": {"2023010100": -15.0, "2023010112": -10.0},
            "WS10M": {"2023010100": 5.0, "2023010112": 6.0},
            "PRECTOTCORR": {"2023010100": 0.0, "2023010112": 0.1},
            "ALLSKY_SFC_PAR_TOT": {"2023010100": 0.0, "2023010112": 100.0},
        }
    }
}


def test_parse_power_response() -> None:
    df = _parse_power_response(SAMPLE_PAYLOAD)
    assert "ghi_wh_m2" in df.columns
    assert len(df) == 2


def test_weather_cache_path() -> None:
    path = weather_cache_path(Path("/data"), "iqaluit", 2020)
    assert path.name == "2020.parquet"


@patch("northern_microgrid.weather.fetch_weather_chunk")
def test_fetch_weather_year(mock_chunk: MagicMock, tmp_path: Path) -> None:
    mock_chunk.return_value = _parse_power_response(SAMPLE_PAYLOAD)
    with pytest.raises(ValueError, match="calendar"):
        fetch_weather_year(63.75, -68.52, 2020, tmp_path, "iqaluit", force=True)
