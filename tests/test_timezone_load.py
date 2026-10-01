"""Tests for UTC-aligned load generation."""

import numpy as np

from northern_microgrid.load_profiles import generate_hourly_load, local_hour_of_day


def test_utc_offset_changes_profile() -> None:
    base = generate_hourly_load("remote_camp", utc_offset_hours=0)
    shifted = generate_hourly_load("remote_camp", utc_offset_hours=-5)
    assert not np.allclose(base, shifted)


def test_local_hour_wraps() -> None:
    assert local_hour_of_day(0, -5) == 19
    assert local_hour_of_day(5, -5) == 0
