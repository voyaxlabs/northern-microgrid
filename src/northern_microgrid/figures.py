"""Figure generation for evaluation results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

from northern_microgrid.dispatch import simulate_year
from northern_microgrid.types import SystemDesign


def monthly_energy_balance(
    load_kw: np.ndarray,
    weather_df: pd.DataFrame,
    design: SystemDesign,
    output_path: Path,
    site_name: str,
) -> Path:
    """Generate monthly energy balance stacked bar chart."""
    dispatch, _ = simulate_year(load_kw, weather_df, design)

    n_months = 12
    months = np.arange(1, n_months + 1)
    renewable_monthly = np.zeros(n_months)
    unknown_monthly = np.zeros(n_months)
    diesel_monthly = np.zeros(n_months)
    diesel_dump_monthly = np.zeros(n_months)
    curtailed_monthly = np.zeros(n_months)
    load_monthly = np.zeros(n_months)

    hours_per_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
    offset = 0
    for m, nh in enumerate(hours_per_month):
        sl = slice(offset, offset + nh)
        renewable_monthly[m] = sum(dispatch.renewable_to_load_kw[sl])
        unknown_monthly[m] = (
            sum(dispatch.battery_to_load_kw[sl])
            + sum(dispatch.pv_to_load_kw[sl])
            + sum(dispatch.wind_to_load_kw[sl])
            - renewable_monthly[m]
        )
        diesel_monthly[m] = sum(dispatch.diesel_kw[sl]) - sum(dispatch.diesel_dump_kw[sl])
        diesel_dump_monthly[m] = sum(dispatch.diesel_dump_kw[sl])
        curtailed_monthly[m] = sum(dispatch.curtailed_kw[sl])
        load_monthly[m] = sum(dispatch.load_kw[sl])
        offset += nh

    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.6
    ax.bar(months, renewable_monthly, width, label="Renewable to load", color="#f39c12")
    ax.bar(
        months,
        unknown_monthly,
        width,
        bottom=renewable_monthly,
        label="Initial unknown-source storage",
        color="#8e44ad",
    )
    bottom = renewable_monthly + unknown_monthly
    ax.bar(months, diesel_monthly, width, bottom=bottom, label="Diesel to load", color="#95a5a6")
    bottom = bottom + diesel_monthly
    ax.bar(
        months,
        diesel_dump_monthly,
        width,
        bottom=bottom,
        label="Diesel dump (min load)",
        color="#bdc3c7",
    )
    ax.plot(months, load_monthly, "k--", linewidth=2, label="Load", marker="o", markersize=4)
    ax.plot(
        months,
        curtailed_monthly,
        "r:",
        linewidth=1.5,
        label="Curtailed renewable",
        marker="x",
        markersize=3,
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Energy (kWh)")
    ax.set_title(f"Monthly Energy Balance - {site_name}")
    ax.set_xticks(months)
    ax.set_xticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def baseline_comparison_chart(
    baseline_data: dict[str, dict[str, float]],
    output_path: Path,
    metric: str = "npc_cad",
    title: str = "Baseline Comparison",
) -> Path:
    """Bar chart comparing baselines on one metric."""
    names = [n for n in baseline_data if n != "load_statistics"]
    values = [baseline_data[n][metric] for n in names]
    labels = [n.replace("_", " ").title() for n in names]

    fig, ax = plt.subplots(figsize=(8, 5))
    colours = ["#95a5a6", "#bdc3c7", "#7f8c8d", "#1a5276"]
    ax.bar(labels, values, color=colours[: len(labels)])
    ax.set_ylabel(metric.replace("_", " ").title())
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
