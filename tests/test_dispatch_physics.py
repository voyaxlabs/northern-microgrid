"""Tests for dispatch physics fixes (publication review findings 1-2)."""

import numpy as np

from northern_microgrid.dispatch import (
    aggregate_metrics,
    assert_energy_conservation,
    charge_efficiency,
    simulate_hourly,
)
from northern_microgrid.types import (
    BatteryConfig,
    DieselConfig,
    EconomicParams,
    PvConfig,
    SystemDesign,
    WindConfig,
)


def _hybrid_design() -> SystemDesign:
    return SystemDesign(
        pv=PvConfig(capacity_kw=100.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=0.0),
        battery=BatteryConfig(power_kw=50.0, energy_kwh=200.0, round_trip_efficiency=0.92),
        diesel=DieselConfig(capacity_kw=80.0, min_load_fraction=0.4),
        economics=EconomicParams(),
    )


def test_cold_reduces_battery_efficiency() -> None:
    cfg = BatteryConfig(power_kw=50.0, energy_kwh=200.0)
    warm = charge_efficiency(25.0, cfg)
    cold = charge_efficiency(-20.0, cfg)
    assert cold < warm


def test_round_trip_efficiency_is_product_of_one_way() -> None:
    cfg = BatteryConfig(power_kw=50.0, energy_kwh=200.0, round_trip_efficiency=0.92)
    assert abs(cfg.charge_efficiency * cfg.discharge_efficiency - 0.92) < 1e-9


def test_energy_conservation_hourly() -> None:
    n = 168
    load = np.full(n, 40.0)
    ghi = np.full(n, 300.0)
    temp = np.full(n, -15.0)
    wind = np.zeros(n)
    precip = np.zeros(n)
    dispatch = simulate_hourly(load, ghi, temp, wind, precip, _hybrid_design())
    assert_energy_conservation(dispatch)


def test_renewable_delivered_not_gross() -> None:
    n = 8760
    load = np.full(n, 30.0)
    ghi = np.concatenate([np.full(4380, 0.0), np.full(4380, 500.0)])
    temp = np.full(n, -10.0)
    wind = np.zeros(n)
    precip = np.zeros(n)
    dispatch = simulate_hourly(load, ghi, temp, wind, precip, _hybrid_design())
    metrics = aggregate_metrics(dispatch, _hybrid_design().diesel)
    assert metrics.renewable_fraction <= 1.0
    assert metrics.gross_renewable_fraction >= metrics.renewable_fraction


def test_diesel_dump_tracked_when_min_load_exceeds_deficit() -> None:
    n = 24
    load = np.full(n, 5.0)
    ghi = np.zeros(n)
    temp = np.full(n, -10.0)
    wind = np.zeros(n)
    precip = np.zeros(n)
    design = SystemDesign(
        pv=PvConfig(capacity_kw=0.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=0.0),
        battery=BatteryConfig(power_kw=0.0, energy_kwh=0.0),
        diesel=DieselConfig(capacity_kw=50.0, min_load_fraction=0.4),
        economics=EconomicParams(),
    )
    dispatch = simulate_hourly(load, ghi, temp, wind, precip, design)
    metrics = aggregate_metrics(dispatch, design.diesel)
    assert metrics.diesel_dump_kwh > 0.0
