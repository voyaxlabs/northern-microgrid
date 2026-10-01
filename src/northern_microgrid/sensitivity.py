"""Fixed-design, one-at-a-time scenario sensitivities; no re-optimization."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from northern_microgrid.dispatch import simulate_year
from northern_microgrid.economics import lifecycle_summary, system_capex
from northern_microgrid.sizing import diesel_only_design
from northern_microgrid.types import SystemDesign


def sensitivity_cases() -> dict[str, float]:
    """Stipulated stress factors, not uncertainty distributions."""
    return {
        "base": 1.0,
        "fuel_low": 0.75,
        "fuel_high": 1.25,
        "capex_high": 1.25,
        "replacements": 1.0,
        "snow_high": 0.20,
        "battery_no_temp_penalty": 0.0,
    }


def run_sensitivity(
    load: np.ndarray, weather: pd.DataFrame, design: SystemDesign
) -> dict[str, dict[str, float]]:
    """Recompute dispatch/NPC for each fixed design and a consistently stressed baseline.

    Replacement stress buys battery power+energy in year 12 and a diesel unit in year 15.
    No-temp-penalty is an idealized efficiency bound with zero heating energy, not a design.
    """
    rows: dict[str, dict[str, float]] = {}
    baseline = diesel_only_design(float(load.max()), design.economics)
    for name, factor in sensitivity_cases().items():
        pair: list[float] = []
        renewable = 0.0
        for original in [design, baseline]:
            modified = original
            if name.startswith("fuel_"):
                modified = replace(
                    original,
                    diesel=replace(
                        original.diesel,
                        fuel_cost_cad_per_l=original.diesel.fuel_cost_cad_per_l * factor,
                    ),
                )
            elif name == "capex_high":
                econ = original.economics
                modified = replace(
                    original,
                    economics=replace(
                        econ,
                        pv_capex_cad_per_kw=econ.pv_capex_cad_per_kw * factor,
                        wind_capex_cad_per_kw=econ.wind_capex_cad_per_kw * factor,
                        battery_power_capex_cad_per_kw=econ.battery_power_capex_cad_per_kw * factor,
                        battery_energy_capex_cad_per_kwh=econ.battery_energy_capex_cad_per_kwh
                        * factor,
                        diesel_capex_cad_per_kw=econ.diesel_capex_cad_per_kw * factor,
                    ),
                )
            elif name == "snow_high":
                modified = replace(original, pv=replace(original.pv, snow_loss_fraction=factor))
            elif name == "battery_no_temp_penalty":
                modified = replace(
                    original, battery=replace(original.battery, temp_coeff_pct_per_c=factor)
                )
            _, metrics = simulate_year(load, weather, modified)
            npc = lifecycle_summary(modified, metrics).npc_cad
            if name == "replacements":
                econ = modified.economics
                battery_cost = (
                    modified.battery.power_kw * econ.battery_power_capex_cad_per_kw
                    + modified.battery.energy_kwh * econ.battery_energy_capex_cad_per_kwh
                )
                diesel_cost = system_capex(
                    diesel_only_design(modified.diesel.capacity_kw / 1.1, econ)
                )
                npc += battery_cost / (1 + econ.discount_rate) ** 12
                npc += diesel_cost / (1 + econ.discount_rate) ** 15
            pair.append(npc)
            if original is design:
                renewable = metrics.renewable_fraction
        rows[name] = {
            "npc_cad": pair[0],
            "diesel_baseline_npc_cad": pair[1],
            "savings_pct": 100 * (1 - pair[0] / pair[1]),
            "renewable_fraction": renewable,
        }
    return rows
