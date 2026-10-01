"""Tests for lifecycle economics."""

from northern_microgrid.economics import (
    discounted_delivered_energy_kwh,
    levelized_cost,
    net_present_cost,
    system_capex,
)
from northern_microgrid.types import (
    BatteryConfig,
    DieselConfig,
    EconomicParams,
    PvConfig,
    SimulationMetrics,
    SystemDesign,
    WindConfig,
)


def _sample_metrics() -> SimulationMetrics:
    return SimulationMetrics(
        total_load_kwh=175200.0,
        unmet_load_kwh=0.0,
        unmet_fraction=0.0,
        diesel_kwh=50000.0,
        diesel_litres=14000.0,
        diesel_dump_kwh=5000.0,
        pv_generation_kwh=100000.0,
        wind_generation_kwh=20000.0,
        curtailed_kwh=5000.0,
        gross_renewable_fraction=0.68,
        renewable_fraction=0.55,
        renewable_delivered_kwh=96360.0,
        battery_storage_loss_kwh=2000.0,
        initial_soc_kwh=87.5,
        terminal_soc_kwh=87.5,
        co2_kg=37520.0,
    )


def _sample_design() -> SystemDesign:
    return SystemDesign(
        pv=PvConfig(capacity_kw=100.0, tilt_deg=45.0),
        wind=WindConfig(capacity_kw=50.0),
        battery=BatteryConfig(power_kw=50.0, energy_kwh=200.0),
        diesel=DieselConfig(capacity_kw=100.0),
        economics=EconomicParams(),
    )


def test_capex_positive() -> None:
    capex = system_capex(_sample_design())
    assert capex > 0.0


def test_npc_includes_capex() -> None:
    design = _sample_design()
    metrics = _sample_metrics()
    npc = net_present_cost(design, metrics)
    assert npc >= system_capex(design)


def test_lcoe_uses_discounted_energy() -> None:
    design = _sample_design()
    metrics = _sample_metrics()
    lcoe = levelized_cost(design, metrics)
    undiscounted = net_present_cost(design, metrics) / (
        metrics.total_load_kwh * design.economics.project_lifetime_years
    )
    assert lcoe > undiscounted


def test_discounted_energy_positive() -> None:
    energy = discounted_delivered_energy_kwh(_sample_design(), _sample_metrics())
    assert energy > 0.0
