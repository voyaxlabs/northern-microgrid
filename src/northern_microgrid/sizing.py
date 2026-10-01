"""System sizing via grid search over component capacities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from northern_microgrid.dispatch import simulate_year
from northern_microgrid.economics import lifecycle_summary
from northern_microgrid.types import (
    BatteryConfig,
    DieselConfig,
    EconomicParams,
    PvConfig,
    SystemDesign,
    WindConfig,
)


@dataclass
class SizingConstraints:
    """Constraints for the sizing search."""

    max_unmet_fraction: float = 0.01
    pv_kw_range: tuple[float, float, float] = (0.0, 200.0, 10.0)
    wind_kw_range: tuple[float, float, float] = (0.0, 100.0, 10.0)
    battery_kwh_range: tuple[float, float, float] = (0.0, 500.0, 25.0)
    battery_power_ratio: float = 0.5  # kW per kWh


@dataclass
class SizingResult:
    """Best design found by sizing search."""

    design: SystemDesign
    npc_cad: float
    unmet_fraction: float
    evaluations: int


def _frange(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    v = start
    while v <= stop:
        values.append(v)
        v += step
    return values


def diesel_only_design(peak_kw: float, econ: EconomicParams | None = None) -> SystemDesign:
    """Baseline: diesel generator sized to peak load."""
    econ = econ or EconomicParams()
    return SystemDesign(
        pv=PvConfig(capacity_kw=0.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=0.0),
        battery=BatteryConfig(power_kw=0.0, energy_kwh=0.0),
        diesel=DieselConfig(capacity_kw=peak_kw * 1.1),
        economics=econ,
    )


def rule_of_thumb_design(
    peak_kw: float,
    daily_kwh: float,
    tilt_deg: float = 45.0,
    econ: EconomicParams | None = None,
) -> SystemDesign:
    """Baseline: 3-day autonomy rule with PV sized to 1.2x daily energy / 3 h sun."""
    econ = econ or EconomicParams()
    pv_kw = max(0.0, daily_kwh * 1.2 / 3.0)
    batt_kwh = daily_kwh * 3.0
    batt_kw = batt_kwh * 0.5
    return SystemDesign(
        pv=PvConfig(capacity_kw=pv_kw, tilt_deg=tilt_deg),
        wind=WindConfig(capacity_kw=0.0),
        battery=BatteryConfig(power_kw=batt_kw, energy_kwh=batt_kwh),
        diesel=DieselConfig(capacity_kw=peak_kw * 1.1),
        economics=econ,
    )


def fixed_renewable_design(
    peak_kw: float,
    pv_kw: float,
    wind_kw: float,
    battery_kwh: float,
    tilt_deg: float = 45.0,
    econ: EconomicParams | None = None,
) -> SystemDesign:
    """Baseline with fixed renewable capacities (no optimization)."""
    econ = econ or EconomicParams()
    batt_kw = battery_kwh * 0.5
    return SystemDesign(
        pv=PvConfig(capacity_kw=pv_kw, tilt_deg=tilt_deg),
        wind=WindConfig(capacity_kw=wind_kw),
        battery=BatteryConfig(power_kw=batt_kw, energy_kwh=battery_kwh),
        diesel=DieselConfig(capacity_kw=peak_kw * 1.1),
        economics=econ,
    )


def optimize_design(
    load_kw: np.ndarray,
    weather_df: object,
    peak_kw: float,
    constraints: SizingConstraints | None = None,
    econ: EconomicParams | None = None,
    tilt_deg: float = 45.0,
) -> SizingResult:
    """Grid-search sizing minimizing NPC subject to reliability constraint."""
    constraints = constraints or SizingConstraints()
    econ = econ or EconomicParams()

    best: SizingResult | None = None
    evaluations = 0

    pv_values = _frange(*constraints.pv_kw_range)
    wind_values = _frange(*constraints.wind_kw_range)
    batt_values = _frange(*constraints.battery_kwh_range)

    for pv_kw in pv_values:
        for wind_kw in wind_values:
            for batt_kwh in batt_values:
                batt_kw = batt_kwh * constraints.battery_power_ratio
                design = SystemDesign(
                    pv=PvConfig(capacity_kw=pv_kw, tilt_deg=tilt_deg),
                    wind=WindConfig(capacity_kw=wind_kw),
                    battery=BatteryConfig(power_kw=batt_kw, energy_kwh=batt_kwh),
                    diesel=DieselConfig(capacity_kw=peak_kw * 1.1),
                    economics=econ,
                )
                _, metrics = simulate_year(load_kw, weather_df, design)
                evaluations += 1
                if metrics.unmet_fraction > constraints.max_unmet_fraction:
                    continue
                lc = lifecycle_summary(design, metrics)
                candidate = SizingResult(
                    design=design,
                    npc_cad=lc.npc_cad,
                    unmet_fraction=metrics.unmet_fraction,
                    evaluations=evaluations,
                )
                if best is None or candidate.npc_cad < best.npc_cad:
                    best = candidate

    if best is None:
        # Fall back to diesel-only if no design meets constraint
        design = diesel_only_design(peak_kw, econ)
        _, metrics = simulate_year(load_kw, weather_df, design)
        lc = lifecycle_summary(design, metrics)
        best = SizingResult(
            design=design,
            npc_cad=lc.npc_cad,
            unmet_fraction=metrics.unmet_fraction,
            evaluations=evaluations,
        )
    best.evaluations = evaluations
    return best
