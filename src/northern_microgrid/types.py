"""Typed configuration and result structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

LoadArchetype = Literal["remote_residential", "remote_camp", "research_station"]


@dataclass(frozen=True)
class SiteLocation:
    """Geographic site with display metadata."""

    name: str
    latitude: float
    longitude: float
    province_territory: str
    elevation_m: float = 0.0
    utc_offset_hours: int = -7
    """Fixed standard-time offset from UTC for load peak alignment."""


@dataclass(frozen=True)
class PvConfig:
    """Photovoltaic array parameters."""

    capacity_kw: float
    tilt_deg: float
    azimuth_deg: float = 180.0
    derate: float = 0.86
    temp_coeff_pct_per_c: float = -0.35
    ref_temp_c: float = 25.0
    snow_loss_fraction: float = 0.05


@dataclass(frozen=True)
class WindConfig:
    """Wind turbine parameters."""

    capacity_kw: float
    hub_height_m: float = 30.0
    cut_in_ms: float = 3.0
    rated_ms: float = 12.0
    cut_out_ms: float = 25.0
    availability: float = 0.95


@dataclass(frozen=True)
class BatteryConfig:
    """Battery energy storage parameters."""

    power_kw: float
    energy_kwh: float
    round_trip_efficiency: float = 0.92
    min_soc: float = 0.15
    max_soc: float = 0.95
    temp_coeff_pct_per_c: float = 0.5
    ref_temp_c: float = 25.0

    @property
    def charge_efficiency(self) -> float:
        return float(self.round_trip_efficiency**0.5)

    @property
    def discharge_efficiency(self) -> float:
        return float(self.round_trip_efficiency**0.5)


@dataclass(frozen=True)
class DieselConfig:
    """Backup diesel generator parameters."""

    capacity_kw: float
    min_load_fraction: float = 0.4
    fuel_l_per_kwh: float = 0.28
    fuel_cost_cad_per_l: float = 2.10
    co2_kg_per_l: float = 2.68


@dataclass(frozen=True)
class EconomicParams:
    """Lifecycle economic assumptions."""

    project_lifetime_years: int = 25
    discount_rate: float = 0.06
    pv_capex_cad_per_kw: float = 2200.0
    wind_capex_cad_per_kw: float = 2800.0
    battery_power_capex_cad_per_kw: float = 400.0
    battery_energy_capex_cad_per_kwh: float = 350.0
    diesel_capex_cad_per_kw: float = 800.0
    fixed_om_cad_per_year: float = 5000.0
    variable_om_cad_per_mwh: float = 5.0


@dataclass(frozen=True)
class SystemDesign:
    """Complete hybrid system design."""

    pv: PvConfig
    wind: WindConfig
    battery: BatteryConfig
    diesel: DieselConfig
    economics: EconomicParams = field(default_factory=EconomicParams)


@dataclass
class HourlyDispatchResult:
    """Single-year hourly simulation outputs."""

    load_kw: list[float]
    pv_gen_kw: list[float]
    wind_gen_kw: list[float]
    battery_charge_kw: list[float]
    battery_discharge_kw: list[float]
    battery_soc: list[float]
    diesel_kw: list[float]
    diesel_dump_kw: list[float]
    unmet_kw: list[float]
    curtailed_kw: list[float]
    pv_to_load_kw: list[float]
    wind_to_load_kw: list[float]
    battery_to_load_kw: list[float]
    renewable_to_load_kw: list[float]
    initial_soc_kwh: float
    terminal_soc_kwh: float
    battery_energy_kwh: float = 0.0
    terminal_renewable_soc_kwh: float = 0.0


@dataclass
class SimulationMetrics:
    """Aggregated annual simulation metrics."""

    total_load_kwh: float
    unmet_load_kwh: float
    unmet_fraction: float
    diesel_kwh: float
    diesel_litres: float
    diesel_dump_kwh: float
    pv_generation_kwh: float
    wind_generation_kwh: float
    curtailed_kwh: float
    gross_renewable_fraction: float
    renewable_fraction: float
    renewable_delivered_kwh: float
    battery_storage_loss_kwh: float
    initial_soc_kwh: float
    terminal_soc_kwh: float
    co2_kg: float
    terminal_renewable_soc_kwh: float = 0.0
    initial_unknown_to_load_kwh: float = 0.0


@dataclass
class LifecycleResult:
    """Lifecycle cost and emissions summary."""

    npc_cad: float
    lcoe_cad_per_kwh: float
    annual_diesel_litres: float
    annual_co2_kg: float
    capex_cad: float


@dataclass
class CaseStudyResult:
    """Full case study output for one site and weather year."""

    site: SiteLocation
    weather_year: int
    design: SystemDesign
    metrics: SimulationMetrics
    lifecycle: LifecycleResult
    load_archetype: LoadArchetype


@dataclass
class UncertaintyBand:
    """Bootstrap or multi-year uncertainty interval."""

    metric: str
    point_estimate: float
    lower_95: float
    upper_95: float
    n_samples: int


@dataclass(frozen=True)
class DataPaths:
    """Resolved data directory paths."""

    root: Path
    weather: Path
    results: Path
    figures: Path

    @classmethod
    def from_root(cls, root: Path) -> DataPaths:
        return cls(
            root=root,
            weather=root / "data" / "weather",
            results=root / "results",
            figures=root / "results" / "figures",
        )
