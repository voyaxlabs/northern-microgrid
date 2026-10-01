"""Generate scenario claims from actual evaluation JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from northern_microgrid.limitations import LIMITATIONS


def _ci_width_pct(lower: float, upper: float, mean: float) -> float:
    return (upper - lower) / mean * 100 if mean else 0.0


def generate_results_markdown(results: dict[str, Any], prereg_sha: str) -> str:
    """Report measured scenario outcomes; literature and constants are labelled separately."""
    year = str(results["weather_years"][0])
    sites = results["sites"]
    timing = results.get("timing", {})
    year_count = len(results["weather_years"])
    constraint = (
        results.get("run_metadata", {})
        .get("search_constraints", {})
        .get("max_unmet_fraction", 0.01)
    )
    lines = [
        "# Results",
        "",
        "Simulation-only scenario results from "
        "`results/evaluation_results.json`. Grid-optimal under the recorded search, "
        "dispatch and fixed diesel sizing; no external validation.",
        "",
        "```bash",
        "pip install -c constraints.txt hatchling editables build",
        'pip install --no-build-isolation -c constraints.txt -e ".[dev]"',
        "northern-microgrid run --root .",
        "```",
        "",
        f"**Preserved protocol SHA-256:** `{prereg_sha}` (chronology unverified)",
        f"**Pipeline runtime (this run):** {timing.get('pipeline_total_s', 0):.1f} s",
        "",
        "## Configuration",
        "",
        f"- Synthetic load archetype: `{results['archetype']}`",
        f"- Weather years: {', '.join(map(str, results['weather_years']))}",
        f"- Optimization year: {year}; evaluation reuses this year.",
        "- Renewable delivery includes direct PV/wind and renewable-source battery discharge.",
        "- Costs, loads and coefficients are stipulated assumptions, not downloaded measurements.",
        "- Input/code/dependency hashes and search configuration: "
        "[run metadata](results/evaluation_results.json); "
        "[protocol deviations](docs/PROTOCOL_DEVIATIONS.md).",
        "",
        f"## Headline results ({year} weather)",
        "",
        "| Site | PV kW | Battery kWh | Renewable delivered % | Gross gen % | "
        "Diesel L/yr | NPC CAD | vs diesel-only |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    savings: dict[str, float] = {}
    h1_met: list[str] = []
    widths: dict[str, float] = {}
    max_unmet = max(
        v["metrics"]["unmet_fraction"] for s in sites.values() for v in s["year_metrics"].values()
    )
    for sid, site in sites.items():
        d = site["optimized_design"]
        m = site["year_metrics"][year]["metrics"]
        lc = site["year_metrics"][year]["lifecycle"]
        baseline = site["baselines"]["diesel_only"]["npc_cad"]
        saving = 100 * (1 - lc["npc_cad"] / baseline)
        savings[sid] = saving
        if (
            saving >= 15
            and max(v["metrics"]["unmet_fraction"] for v in site["year_metrics"].values())
            < 0.01
        ):
            h1_met.append(site["site"]["name"])
        wording = "lower" if saving >= 0 else "higher"
        lines.append(
            f"| {site['site']['name']} | {d['pv']['capacity_kw']:.0f} "
            f"| {d['battery']['energy_kwh']:.0f} | {m['renewable_fraction'] * 100:.1f} "
            f"| {m['gross_renewable_fraction'] * 100:.1f} | {m['diesel_litres']:.0f} "
            f"| {lc['npc_cad']:.0f} | {abs(saving):.1f}% {wording} |"
        )
    status = "met" if max_unmet <= constraint else "FAILED"
    lines += [
        "",
        f"Reliability constraint <= {constraint * 100:.3f}%: {status}; "
        f"maximum unmet across all evaluated site-years: {max_unmet * 100:.3f}%.",
        "",
        "## Load and baseline statistics",
        "",
        "| Site | Annual kWh | Mean daily kWh | Realized peak kW | Diesel-only NPC CAD |",
        "|---|---:|---:|---:|---:|",
    ]
    for site in sites.values():
        stats = site.get("load_statistics", {})
        lines.append(
            f"| {site['site']['name']} | {stats.get('annual_kwh', 0):.0f} "
            f"| {stats.get('mean_daily_kwh', 0):.1f} | {stats.get('peak_kw', 0):.2f} "
            f"| {site['baselines']['diesel_only']['npc_cad']:.0f} |"
        )
    lines += [
        "",
        f"## NPC bootstrap intervals (95%, mean of {year_count} evaluated weather years)",
        "",
        "| Site | Mean CAD | Lower CAD | Upper CAD | Width % | Years |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for sid, site in sites.items():
        for b in site["uncertainty"]:
            if b["metric"] == "npc_cad":
                width = _ci_width_pct(b["lower_95"], b["upper_95"], b["point_estimate"])
                widths[sid] = width
                lines.append(
                    f"| {site['site']['name']} | {b['point_estimate']:.0f} "
                    f"| {b['lower_95']:.0f} | {b['upper_95']:.0f} "
                    f"| {width:.2f} | {b['n_samples']} |"
                )
    lines += ["", "## Hypothesis outcomes", ""]
    if results["archetype"] == "remote_camp":
        lines.append(
            f"- H1 (>=15% NPC savings and <1% unmet in every evaluated year): met at "
            f"{len(h1_met)} of {len(sites)} evaluated sites: "
            f"{', '.join(h1_met) or 'none'}."
        )
        lines.append(
            "  Savings by site: "
            + "; ".join(
                f"{sites[sid]['site']['name']}: {value:.1f}%" for sid, value in savings.items()
            )
            + "."
        )
    else:
        lines.append("- H1: untested for this archetype; the hypothesis specifies remote_camp.")
    arctic = [sid for sid in ["iqaluit", "inuvik"] if sid in widths]
    if arctic and len(results["weather_years"]) > 1 and results["archetype"] == "remote_camp":
        h2 = "met" if all(widths[sid] > 10 for sid in arctic) else "not met"
        lines.append(
            f"- H2 (>10% NPC CI width at evaluated Arctic sites): {h2}; "
            + "; ".join(f"{sites[sid]['site']['name']}: {widths[sid]:.2f}%" for sid in arctic)
            + "."
        )
    else:
        lines.append(
            "- H2: untested; requires remote_camp, Arctic sites and multiple weather years."
        )
    lines += [
        "- H3: untested; no matched measured load/weather validation experiment.",
        "",
        "Selected wind: "
        + "; ".join(
            f"{s['site']['name']}: {s['optimized_design']['wind']['capacity_kw']:.1f} kW"
            for s in sites.values()
        )
        + ".",
        "",
        "## Storage boundary ledger",
        "",
        "Every year starts with unknown-source energy at midpoint SOC. Conversion loss = "
        "charge - discharge - (terminal - initial SOC); boundary energy is not free renewable.",
        "",
        "| Site/year | Initial kWh | Terminal kWh | Unknown initial to load kWh | Loss kWh |",
        "|---|---:|---:|---:|---:|",
    ]
    for site in sites.values():
        for y, data in site["year_metrics"].items():
            m = data["metrics"]
            lines.append(
                f"| {site['site']['name']}/{y} | {m['initial_soc_kwh']:.2f} "
                f"| {m['terminal_soc_kwh']:.2f} "
                f"| {m.get('initial_unknown_to_load_kwh', 0):.2f} "
                f"| {m['battery_storage_loss_kwh']:.2f} |"
            )
    lines += [
        "",
        "## Fixed-design sensitivity (optimization year)",
        "",
        "One assumption changes at a time; capacities are not re-optimized. Fuel +/-25%; "
        "all component CAPEX +25%; battery replacement year 12 and diesel year 15; "
        "snow cap 20%; ideal battery efficiency with no temperature penalty and no heating "
        "energy. These are stipulated stresses, not confidence bounds.",
        "",
        "| Site | Stress | NPC CAD | Savings vs equally stressed diesel % |",
        "|---|---|---:|---:|",
    ]
    for site in sites.values():
        for name, row in site.get("sensitivity", {}).items():
            lines.append(
                f"| {site['site']['name']} | {name} | {row['npc_cad']:.0f} "
                f"| {row['savings_pct']:.2f} |"
            )
    lines += [
        "",
        "## Literature context (sourced, not computed or validation)",
        "",
        "[Colville Lake poster](https://microgrid-symposiums.org/wp-content/uploads/"
        "2019/08/03_DaveTURCOTTE.pdf): about 17% annual PV contribution and over "
        "31,000 L diesel savings. [KLRS paper](https://web.stanford.edu/group/efmh/"
        "jacobson/Articles/Others/23-YukonMicrogrid.pdf): 67% annual PV-plus-storage "
        "contribution, 48 kW PV, about 27 kW battery power. Different sites/loads; "
        "these facts do not validate this scenario.",
        "",
        "## Runtime (seconds, this run)",
        "",
        "| Step | " + " | ".join(s["site"]["name"] for s in sites.values()) + " |",
        "|---|" + "---:|" * len(sites),
    ]
    for label, key in [
        ("Cached weather check", "weather_fetch_s"),
        ("Optimization", "optimization_s"),
        ("Site total", "total_s"),
    ]:
        lines.append(
            f"| {label} | "
            + " | ".join(f"{timing.get(f'{sid}_{key}', 0):.1f}" for sid in sites)
            + " |"
        )
    lines += ["", "## Limitations", ""] + [
        "- " + text.replace("five-year mean", f"{year_count}-year mean")
        if year_count != 5 else "- " + text
        for text in LIMITATIONS
    ]
    lines += [
        "",
        "## Reports and licence",
        "",
        "HTML reports: "
        + ", ".join(f"[{s['site']['name']}](results/report_{sid}.html)" for sid, s in sites.items())
        + ".",
        "Figures: `results/figures/`. [Licence scope](docs/LICENSING.md): CC BY 4.0 "
        "for this document and outputs; code Apache-2.0.",
        "",
    ]
    return "\n".join(lines)


def write_results_markdown(project_root: Path) -> Path:
    """Verify the actual protocol digest before writing claims."""
    from northern_microgrid.provenance import sha256

    results = json.loads((project_root / "results/evaluation_results.json").read_text())
    protocol = project_root / "docs/PREREGISTRATION.md"
    digest = project_root / "docs/PREREGISTRATION.sha256"
    actual = sha256(protocol) if protocol.exists() else "unavailable"
    if digest.exists() and digest.read_text().strip() != actual:
        raise ValueError("Protocol SHA-256 mismatch")
    out = project_root / "RESULTS.md"
    out.write_text(generate_results_markdown(results, actual), encoding="utf-8")
    return out
