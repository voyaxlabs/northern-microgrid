"""One-command evaluation pipeline."""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from northern_microgrid import __version__
from northern_microgrid.evaluation import (
    bootstrap_uncertainty,
    run_baseline_comparison,
    run_case_study,
    serialize_results,
)
from northern_microgrid.figures import baseline_comparison_chart, monthly_energy_balance
from northern_microgrid.load_profiles import (
    ARCHETYPE_DEFAULTS,
    generate_hourly_load,
    load_statistics,
)
from northern_microgrid.provenance import run_metadata, verify_data_manifest
from northern_microgrid.report import render_site_report
from northern_microgrid.sensitivity import run_sensitivity
from northern_microgrid.sites import CANADIAN_SITES
from northern_microgrid.sizing import SizingConstraints, optimize_design
from northern_microgrid.types import DataPaths, LoadArchetype, SystemDesign
from northern_microgrid.weather import fetch_weather_year, load_weather_year

DEFAULT_WEATHER_YEARS = [2018, 2019, 2020, 2021, 2022]
DEFAULT_ARCHETYPE: LoadArchetype = "remote_camp"


def _design_to_dict(design: SystemDesign) -> dict[str, Any]:
    return asdict(design)


def run_pipeline(
    project_root: Path,
    site_ids: list[str] | None = None,
    weather_years: list[int] | None = None,
    archetype: LoadArchetype = DEFAULT_ARCHETYPE,
    fetch_weather: bool = True,
    constraints: SizingConstraints | None = None,
) -> dict[str, Any]:
    """Run the full evaluation pipeline for all sites."""
    paths = DataPaths.from_root(project_root)
    paths.weather.mkdir(parents=True, exist_ok=True)
    paths.results.mkdir(parents=True, exist_ok=True)
    paths.figures.mkdir(parents=True, exist_ok=True)

    sites = site_ids or list(CANADIAN_SITES.keys())
    years = weather_years or DEFAULT_WEATHER_YEARS
    constraints = constraints or SizingConstraints()

    pipeline_start = time.perf_counter()
    missing = {
        paths.weather / site_id / f"{year}.parquet"
        for site_id in sites
        for year in years
        if fetch_weather and not (paths.weather / site_id / f"{year}.parquet").exists()
    }
    # Reject modified inventory before acquisition; defer only requested absent caches.
    verify_data_manifest(project_root, allow_missing=missing)
    for site_id in sites:
        site = CANADIAN_SITES[site_id]
        for year in years:
            if paths.weather / site_id / f"{year}.parquet" in missing:
                fetch_weather_year(site.latitude, site.longitude, year, paths.weather, site_id)
    # Downloads must satisfy the unchanged manifest and weather validation before simulation.
    verify_data_manifest(project_root)
    for site_id in sites:
        for year in years:
            load_weather_year(paths.weather / site_id / f"{year}.parquet")

    used_weather: list[Path] = []
    timing: dict[str, float] = {}
    all_results: dict[str, Any] = {
        "version": __version__,
        "archetype": archetype,
        "weather_years": years,
        "sites": {},
    }

    for site_id in sites:
        site = CANADIAN_SITES[site_id]
        site_start = time.perf_counter()
        site_results: dict[str, Any] = {"site": asdict(site), "years": {}}

        # Fetch weather for all years
        weather_paths: dict[int, Path] = {}
        fetch_start = time.perf_counter()
        for year in years:
            if fetch_weather:
                wp = fetch_weather_year(
                    site.latitude,
                    site.longitude,
                    year,
                    paths.weather,
                    site_id,
                )
            else:
                wp = paths.weather / site_id / f"{year}.parquet"
                if not wp.exists():
                    raise FileNotFoundError(f"Weather data missing: {wp}")
            weather_paths[year] = wp
            used_weather.append(wp)
        timing[f"{site_id}_weather_fetch_s"] = time.perf_counter() - fetch_start

        # Optimize on first year
        opt_year = years[0]
        load = generate_hourly_load(archetype, utc_offset_hours=site.utc_offset_hours)
        peak_kw = float(load.max())
        load_stats = load_statistics(load)
        weather_opt = load_weather_year(weather_paths[opt_year])

        opt_start = time.perf_counter()
        sizing = optimize_design(load, weather_opt, peak_kw, constraints=constraints)
        timing[f"{site_id}_optimization_s"] = time.perf_counter() - opt_start

        # Evaluate all years with optimized design
        year_metrics: dict[str, Any] = {}
        diesel_values: list[float] = []
        ren_values: list[float] = []
        npc_values: list[float] = []

        for year in years:
            case = run_case_study(site, year, weather_paths[year], archetype, sizing.design)
            year_metrics[str(year)] = {
                "metrics": asdict(case.metrics),
                "lifecycle": asdict(case.lifecycle),
            }
            diesel_values.append(case.metrics.diesel_litres)
            ren_values.append(case.metrics.renewable_fraction)
            npc_values.append(case.lifecycle.npc_cad)

        uncertainty = [
            bootstrap_uncertainty(diesel_values, "annual_diesel_litres"),
            bootstrap_uncertainty([r * 100 for r in ren_values], "renewable_fraction_pct"),
            bootstrap_uncertainty(npc_values, "npc_cad"),
        ]

        # Baselines on optimization year
        daily_kwh = ARCHETYPE_DEFAULTS[archetype][0]
        baseline_data = run_baseline_comparison(
            site,
            weather_paths[opt_year],
            archetype,
            sizing.design,
            peak_kw,
            daily_kwh,
        )

        sensitivity = run_sensitivity(load, weather_opt, sizing.design)

        # Figures
        fig_path = paths.figures / f"{site_id}_monthly_balance.png"
        monthly_energy_balance(load, weather_opt, sizing.design, fig_path, site.name)

        baseline_fig = paths.figures / f"{site_id}_baseline_npc.png"
        baseline_comparison_chart(
            baseline_data,
            baseline_fig,
            metric="npc_cad",
            title=f"NPC Comparison - {site.name}",
        )

        # HTML report
        report_path = paths.results / f"report_{site_id}.html"
        uncertainty_dicts: list[dict[str, float | str]] = [
            {
                "metric": u.metric,
                "point": u.point_estimate,
                "lower": u.lower_95,
                "upper": u.upper_95,
            }
            for u in uncertainty
        ]
        render_site_report(
            site_name=site.name,
            province=site.province_territory,
            archetype=archetype,
            case_data={
                "metrics": year_metrics[str(opt_year)]["metrics"],
                "lifecycle": year_metrics[str(opt_year)]["lifecycle"],
                "design": _design_to_dict(sizing.design),
                "weather_year": opt_year,
                "weather_year_count": len(years),
                "load_statistics": load_stats,
                "sensitivity": sensitivity,
            },
            baseline_data=baseline_data,
            uncertainty_bands=uncertainty_dicts,
            figure_path=f"figures/{fig_id}.png"
            if (fig_id := f"{site_id}_monthly_balance")
            else None,
            output_path=report_path,
            version=__version__,
        )

        site_results["sensitivity"] = sensitivity
        site_results["load_statistics"] = load_stats
        site_results["optimized_design"] = _design_to_dict(sizing.design)
        site_results["sizing_evaluations"] = sizing.evaluations
        site_results["year_metrics"] = year_metrics
        site_results["uncertainty"] = [asdict(u) for u in uncertainty]
        site_results["baselines"] = baseline_data
        site_results["report_html"] = str(report_path.relative_to(project_root))
        timing[f"{site_id}_total_s"] = time.perf_counter() - site_start
        all_results["sites"][site_id] = site_results

    timing["pipeline_total_s"] = time.perf_counter() - pipeline_start
    all_results["timing"] = timing

    all_results["run_metadata"] = run_metadata(project_root, used_weather, constraints)
    results_path = paths.results / "evaluation_results.json"
    serialize_results(all_results, results_path)

    from northern_microgrid.results_doc import write_results_markdown

    write_results_markdown(project_root)
    return all_results
