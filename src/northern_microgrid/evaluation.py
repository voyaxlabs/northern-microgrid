"""Evaluation, baselines, uncertainty and scoring utilities."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np

from northern_microgrid.dispatch import simulate_year
from northern_microgrid.economics import lifecycle_summary
from northern_microgrid.load_profiles import generate_hourly_load, load_statistics
from northern_microgrid.sizing import (
    SizingConstraints,
    diesel_only_design,
    fixed_renewable_design,
    optimize_design,
    rule_of_thumb_design,
)
from northern_microgrid.types import (
    CaseStudyResult,
    LoadArchetype,
    SiteLocation,
    SystemDesign,
    UncertaintyBand,
)
from northern_microgrid.weather import load_weather_year


def reliability_score(unmet_fraction: float) -> float:
    """Score reliability: 1.0 = no unmet load, 0.0 = all unmet."""
    return max(0.0, 1.0 - unmet_fraction)


def composite_score(
    unmet_fraction: float,
    renewable_fraction: float,
    npc_cad: float,
    reference_npc: float,
) -> float:
    """Composite score combining reliability, renewables and cost.

    Perfect system (no unmet, max renewable, min cost) approaches 1.0.
    Cost benefit = reference / (reference + cost); equal cost gives 0.5.
    Zero-cost ideal gives 1.0. Empty system scores 0.0.
    """
    rel = reliability_score(unmet_fraction)
    if not math.isfinite(npc_cad) or npc_cad < 0 or reference_npc <= 0:
        cost_score = 0.0
    else:
        cost_score = max(0.0, reference_npc / (reference_npc + npc_cad))
    ren = min(1.0, renewable_fraction)
    return (rel + cost_score + ren) / 3.0


def score_perfect_system() -> float:
    """Sanity test: perfect system should score 1.0."""
    return composite_score(0.0, 1.0, 0.0, 100.0)


def score_empty_system() -> float:
    """Sanity test: worst case should score 0.0."""
    return composite_score(1.0, 0.0, float("inf"), 100.0)


def bootstrap_uncertainty(
    values: list[float],
    metric_name: str,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> UncertaintyBand:
    """Bootstrap 95% confidence interval for a metric across weather years."""
    rng = np.random.default_rng(seed)
    arr = np.array(values, dtype=np.float64)
    n = len(arr)
    if n == 0:
        raise ValueError("Cannot bootstrap empty values")
    if n == 1:
        v = float(arr[0])
        return UncertaintyBand(metric_name, v, v, v, 1)

    boot_means = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means[i] = sample.mean()

    return UncertaintyBand(
        metric=metric_name,
        point_estimate=float(arr.mean()),
        lower_95=float(np.percentile(boot_means, 2.5)),
        upper_95=float(np.percentile(boot_means, 97.5)),
        n_samples=n,
    )


def run_case_study(
    site: SiteLocation,
    weather_year: int,
    weather_path: Path,
    archetype: LoadArchetype,
    design: SystemDesign,
) -> CaseStudyResult:
    """Run a single site-year case study."""
    weather = load_weather_year(weather_path)
    load = generate_hourly_load(archetype, utc_offset_hours=site.utc_offset_hours)
    _, metrics = simulate_year(load, weather, design)
    lifecycle = lifecycle_summary(design, metrics)
    return CaseStudyResult(
        site=site,
        weather_year=weather_year,
        design=design,
        metrics=metrics,
        lifecycle=lifecycle,
        load_archetype=archetype,
    )


def run_baseline_comparison(
    site: SiteLocation,
    weather_path: Path,
    archetype: LoadArchetype,
    optimized: SystemDesign,
    peak_kw: float,
    daily_kwh: float,
    tilt_deg: float = 45.0,
) -> dict[str, dict[str, float]]:
    """Compare optimized design against baselines on one weather year."""
    weather = load_weather_year(weather_path)
    load = generate_hourly_load(archetype, utc_offset_hours=site.utc_offset_hours)
    load_stats = load_statistics(load)

    baselines: dict[str, SystemDesign] = {
        "diesel_only": diesel_only_design(peak_kw),
        "rule_of_thumb": rule_of_thumb_design(peak_kw, daily_kwh, tilt_deg),
        "fixed_renewable": fixed_renewable_design(
            peak_kw,
            pv_kw=optimized.pv.capacity_kw * 0.8,
            wind_kw=optimized.wind.capacity_kw,
            battery_kwh=optimized.battery.energy_kwh * 0.8,
            tilt_deg=tilt_deg,
        ),
        "optimized": optimized,
    }

    diesel_only_design_obj = baselines["diesel_only"]
    _, diesel_only_metrics = simulate_year(load, weather, diesel_only_design_obj)
    reference_npc = lifecycle_summary(diesel_only_design_obj, diesel_only_metrics).npc_cad

    results: dict[str, dict[str, float]] = {}
    for name, design in baselines.items():
        _, metrics = simulate_year(load, weather, design)
        lc = lifecycle_summary(design, metrics)
        results[name] = {
            "unmet_fraction": metrics.unmet_fraction,
            "renewable_fraction": metrics.renewable_fraction,
            "gross_renewable_fraction": metrics.gross_renewable_fraction,
            "diesel_litres": metrics.diesel_litres,
            "diesel_dump_kwh": metrics.diesel_dump_kwh,
            "npc_cad": lc.npc_cad,
            "lcoe_cad_per_kwh": lc.lcoe_cad_per_kwh,
            "co2_kg": metrics.co2_kg,
            "composite_score": composite_score(
                metrics.unmet_fraction,
                metrics.renewable_fraction,
                lc.npc_cad,
                reference_npc,
            ),
        }
    results["load_statistics"] = load_stats
    return results


def optimize_for_site(
    site: SiteLocation,
    weather_path: Path,
    archetype: LoadArchetype,
    constraints: SizingConstraints | None = None,
) -> SystemDesign:
    """Run sizing optimization for a site."""
    weather = load_weather_year(weather_path)
    load = generate_hourly_load(archetype, utc_offset_hours=site.utc_offset_hours)
    peak = float(load.max())
    result = optimize_design(load, weather, peak, constraints=constraints)
    return result.design


def serialize_results(data: object, path: Path) -> None:
    """Write evaluation results to JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)

    def default(obj: object) -> object:
        if hasattr(obj, "__dataclass_fields__"):
            from dataclasses import is_dataclass

            if is_dataclass(obj) and not isinstance(obj, type):
                return asdict(obj)
        raise TypeError(f"Not serializable: {type(obj)}")

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=default)
