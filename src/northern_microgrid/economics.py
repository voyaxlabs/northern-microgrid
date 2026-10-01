"""Lifecycle cost and emissions calculations."""

from __future__ import annotations

from northern_microgrid.types import (
    LifecycleResult,
    SimulationMetrics,
    SystemDesign,
)


def system_capex(design: SystemDesign) -> float:
    """Total capital cost in CAD."""
    econ = design.economics
    capex = (
        design.pv.capacity_kw * econ.pv_capex_cad_per_kw
        + design.wind.capacity_kw * econ.wind_capex_cad_per_kw
        + design.battery.power_kw * econ.battery_power_capex_cad_per_kw
        + design.battery.energy_kwh * econ.battery_energy_capex_cad_per_kwh
        + design.diesel.capacity_kw * econ.diesel_capex_cad_per_kw
    )
    return capex


def annual_opex(design: SystemDesign, metrics: SimulationMetrics) -> float:
    """Annual operating cost in CAD (constant-year simplified scenario)."""
    econ = design.economics
    energy_mwh = metrics.total_load_kwh / 1000.0
    fuel_cost = metrics.diesel_litres * design.diesel.fuel_cost_cad_per_l
    return econ.fixed_om_cad_per_year + econ.variable_om_cad_per_mwh * energy_mwh + fuel_cost


def net_present_cost(
    design: SystemDesign,
    metrics: SimulationMetrics,
) -> float:
    """Compute net present cost over project lifetime (constant-year O&M)."""
    econ = design.economics
    capex = system_capex(design)
    opex = annual_opex(design, metrics)
    npc = capex
    for year in range(1, econ.project_lifetime_years + 1):
        npc += opex / (1.0 + econ.discount_rate) ** year
    return npc


def discounted_delivered_energy_kwh(
    design: SystemDesign,
    metrics: SimulationMetrics,
) -> float:
    """Present-value of delivered energy (SAM-style LCOE denominator)."""
    econ = design.economics
    served = metrics.total_load_kwh - metrics.unmet_load_kwh
    total = 0.0
    for year in range(1, econ.project_lifetime_years + 1):
        total += served / (1.0 + econ.discount_rate) ** year
    return total


def levelized_cost(
    design: SystemDesign,
    metrics: SimulationMetrics,
) -> float:
    """Discounted LCOE in CAD/kWh (NPC divided by discounted delivered energy)."""
    denom = discounted_delivered_energy_kwh(design, metrics)
    if denom <= 0:
        return float("inf")
    return net_present_cost(design, metrics) / denom


def lifecycle_summary(
    design: SystemDesign,
    metrics: SimulationMetrics,
) -> LifecycleResult:
    """Full lifecycle summary."""
    return LifecycleResult(
        npc_cad=net_present_cost(design, metrics),
        lcoe_cad_per_kwh=levelized_cost(design, metrics),
        annual_diesel_litres=metrics.diesel_litres,
        annual_co2_kg=metrics.co2_kg,
        capex_cad=system_capex(design),
    )
