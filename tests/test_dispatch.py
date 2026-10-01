"""Tests for hourly dispatch simulation."""

import numpy as np
import pandas as pd

from northern_microgrid.dispatch import aggregate_metrics, simulate_hourly, simulate_year
from northern_microgrid.types import (
    BatteryConfig,
    DieselConfig,
    EconomicParams,
    PvConfig,
    SystemDesign,
    WindConfig,
)


def _make_weather(n: int = 8760) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ghi_wh_m2": np.full(n, 200.0),
            "temp_c": np.full(n, -10.0),
            "wind_ms": np.full(n, 5.0),
            "precip_mm_hr": np.zeros(n),
        }
    )


def _diesel_only_design() -> SystemDesign:
    return SystemDesign(
        pv=PvConfig(capacity_kw=0.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=0.0),
        battery=BatteryConfig(power_kw=0.0, energy_kwh=0.0),
        diesel=DieselConfig(capacity_kw=100.0),
        economics=EconomicParams(),
    )


def test_diesel_serves_load() -> None:
    load = np.full(24, 50.0)
    weather = _make_weather(24)
    design = _diesel_only_design()
    dispatch, metrics = simulate_year(load, weather, design)
    assert metrics.unmet_fraction < 0.01
    assert metrics.diesel_kwh > 0.0


def test_pv_reduces_diesel() -> None:
    load = np.full(8760, 30.0)
    weather = _make_weather()
    weather["ghi_wh_m2"] = 500.0
    diesel_design = _diesel_only_design()
    _, diesel_metrics = simulate_year(load, weather, diesel_design)

    hybrid = SystemDesign(
        pv=PvConfig(capacity_kw=100.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=0.0),
        battery=BatteryConfig(power_kw=50.0, energy_kwh=200.0),
        diesel=DieselConfig(capacity_kw=100.0),
        economics=EconomicParams(),
    )
    _, hybrid_metrics = simulate_year(load, weather, hybrid)
    assert hybrid_metrics.diesel_litres < diesel_metrics.diesel_litres


def test_aggregate_metrics_keys() -> None:
    load = np.full(24, 10.0)
    ghi = np.full(24, 300.0)
    temp = np.full(24, -5.0)
    wind = np.full(24, 6.0)
    precip = np.zeros(24)
    design = SystemDesign(
        pv=PvConfig(capacity_kw=20.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=10.0),
        battery=BatteryConfig(power_kw=5.0, energy_kwh=20.0),
        diesel=DieselConfig(capacity_kw=50.0),
        economics=EconomicParams(),
    )
    dispatch = simulate_hourly(load, ghi, temp, wind, precip, design)
    metrics = aggregate_metrics(dispatch, design.diesel)
    assert metrics.total_load_kwh == 240.0
    assert 0.0 <= metrics.renewable_fraction <= 1.0
    assert metrics.gross_renewable_fraction >= metrics.renewable_fraction
