"""Tests for PV and wind generation models."""

import numpy as np

from northern_microgrid.generation import pv_power_kw, wind_power_kw
from northern_microgrid.types import PvConfig, WindConfig
from northern_microgrid.weather import snow_cover_fraction


def test_pv_zero_at_night() -> None:
    ghi = np.array([0.0, 0.0, 500.0])
    temp = np.array([-10.0, -10.0, -10.0])
    precip = np.zeros(3)
    cfg = PvConfig(capacity_kw=10.0, tilt_deg=45.0)
    power = pv_power_kw(ghi, temp, precip, cfg)
    assert power[0] == 0.0
    assert power[1] == 0.0
    assert power[2] > 0.0


def test_pv_cold_increases_output() -> None:
    ghi = np.array([800.0, 800.0])
    temp = np.array([25.0, -20.0])
    precip = np.zeros(2)
    cfg = PvConfig(capacity_kw=10.0, tilt_deg=45.0)
    power = pv_power_kw(ghi, temp, precip, cfg)
    assert power[1] > power[0]


def test_wind_cut_in() -> None:
    wind = np.array([0.0, 5.0, 15.0, 30.0])
    cfg = WindConfig(capacity_kw=50.0)
    power = wind_power_kw(wind, cfg)
    assert power[0] == 0.0
    assert power[1] > 0.0
    assert power[2] == 50.0 * 0.95  # rated with availability
    assert power[3] == 0.0


def test_snow_cover_accumulates() -> None:
    temp = np.array([-5.0, -5.0, -5.0, 5.0])
    precip = np.array([2.0, 2.0, 0.0, 0.0])
    ghi = np.array([0.0, 0.0, 0.0, 200.0])
    cover = snow_cover_fraction(temp, precip, ghi)
    assert cover[1] > cover[0]
    assert cover[3] < cover[2]
