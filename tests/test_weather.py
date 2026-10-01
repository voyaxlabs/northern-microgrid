"""Tests for weather utilities."""

import pytest

from northern_microgrid.weather import validate_power_url


def test_valid_power_url() -> None:
    url = (
        "https://power.larc.nasa.gov/api/temporal/hourly/point"
        "?parameters=T2M&community=RE&longitude=-68&latitude=63"
        "&start=20230101&end=20230102&format=JSON"
    )
    validate_power_url(url)


def test_invalid_host() -> None:
    with pytest.raises(ValueError, match="Disallowed host"):
        validate_power_url("https://evil.example.com/api")


def test_invalid_scheme() -> None:
    with pytest.raises(ValueError, match="Invalid URL scheme"):
        validate_power_url("ftp://power.larc.nasa.gov/api")
