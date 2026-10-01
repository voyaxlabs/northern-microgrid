"""Tests for load profile generation."""

from northern_microgrid.load_profiles import generate_hourly_load, load_archetype_metadata


def test_remote_residential_length() -> None:
    load = generate_hourly_load("remote_residential")
    assert len(load) == 8760


def test_remote_residential_daily_energy() -> None:
    load = generate_hourly_load("remote_residential")
    daily_mean = float(load.sum()) / 365.0
    assert 5.0 < daily_mean < 10.0


def test_peak_constraint() -> None:
    load = generate_hourly_load("remote_residential", peak_kw=2.0)
    assert float(load.max()) <= 2.0 + 0.01


def test_camp_profile_positive() -> None:
    load = generate_hourly_load("remote_camp")
    assert float(load.min()) >= 0.0
    assert float(load.sum()) > 0.0


def test_metadata_has_citation() -> None:
    meta = load_archetype_metadata("remote_residential")
    assert "citation" in meta
    assert "stipulated" in str(meta["citation"])


def test_seasonal_variation() -> None:
    load = generate_hourly_load("remote_camp")
    winter = load[:2160].mean()
    summer = load[4500:6700].mean()
    assert winter != summer
