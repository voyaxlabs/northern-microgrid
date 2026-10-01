"""HTML report generation for project engineers."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, cast

from jinja2 import Environment, select_autoescape

from northern_microgrid.limitations import LIMITATIONS


def _escape(value: object) -> str:
    return html.escape(str(value))


REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en-CA">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Northern Microgrid Sizing Report - {{ site_name }}</title>
  <style>
    :root { --accent: #1a5276; --bg: #f8f9fa; --text: #212529; }
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; line-height: 1.5; color: var(--text);
           max-width: 900px; margin: 0 auto; padding: 1.5rem; background: var(--bg); }
    header { background: var(--accent); color: #fff; padding: 1.5rem; border-radius: 8px;
              margin-bottom: 1.5rem; }
    h1 { margin: 0 0 0.25rem; font-size: 1.5rem; }
    h2 { color: var(--accent); border-bottom: 2px solid var(--accent); padding-bottom: 0.25rem; }
    main { background: #fff; padding: 1.5rem; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
    th, td { border: 1px solid #dee2e6; padding: 0.5rem 0.75rem; text-align: left; }
    th { background: #e9ecef; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                   gap: 1rem; margin: 1rem 0; }
    .metric-card { background: #e9ecef; padding: 1rem; border-radius: 6px; text-align: center; }
    .metric-card .value { font-size: 1.5rem; font-weight: bold; color: var(--accent); }
    .metric-card .label { font-size: 0.85rem; color: #6c757d; }
    .figure { text-align: center; margin: 1rem 0; }
    .figure img { max-width: 100%; height: auto; border: 1px solid #dee2e6; border-radius: 4px; }
    footer { margin-top: 1.5rem; font-size: 0.85rem; color: #6c757d; }
    a:focus-visible, button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  </style>
</head>
<body>
  <header role="banner">
    <h1>Northern Microgrid Sizing Report</h1>
    <p>{{ site_name }}, {{ province }} - {{ archetype | replace('_', ' ') | title }}</p>
  </header>
  <main role="main">
    <section aria-labelledby="summary-heading">
      <h2 id="summary-heading">Simulation-only scenario summary</h2>
      <p>Weather year: {{ weather_year }}. Synthetic load: {{ "%.0f"|format(annual_kwh) }} kWh/year;
      realized peak {{ "%.2f"|format(peak_kw) }} kW. No matched measured-site validation.</p>
      <div class="metric-grid">
        <div class="metric-card">
          <div class="value">{{ "%.1f"|format(renewable_pct) }}%</div>
          <div class="label">Renewable Delivered to Load</div>
        </div>
        <div class="metric-card">
          <div class="value">{{ "%.0f"|format(diesel_litres) }} L</div>
          <div class="label">Annual Diesel</div>
        </div>
        <div class="metric-card">
          <div class="value">${{ "%.0f"|format(npc_cad) }}</div>
          <div class="label">Net Present Cost</div>
        </div>
        <div class="metric-card">
          <div class="value">{{ "%.3f"|format(unmet_pct) }}%</div>
          <div class="label">Unmet Load</div>
        </div>
      </div>
    </section>

    <section aria-labelledby="design-heading">
      <h2 id="design-heading">Simulation Design (not validated for deployment)</h2>
      <table>
        <caption class="sr-only">System component sizing</caption>
        <thead>
          <tr><th scope="col">Component</th><th scope="col">Capacity</th></tr>
        </thead>
        <tbody>
          <tr><td>Photovoltaic</td><td>{{ pv_kw }} kW</td></tr>
          <tr><td>Wind turbine</td><td>{{ wind_kw }} kW</td></tr>
          <tr><td>Battery power</td><td>{{ batt_power_kw }} kW</td></tr>
          <tr><td>Battery energy</td><td>{{ batt_energy_kwh }} kWh</td></tr>
          <tr><td>Diesel backup</td><td>{{ "%.2f"|format(diesel_kw) }} kW</td></tr>
        </tbody>
      </table>
    </section>

    <section aria-labelledby="baseline-heading">
      <h2 id="baseline-heading">Baseline Comparison</h2>
      <table>
        <caption class="sr-only">Comparison against baseline methods</caption>
        <thead>
          <tr>
            <th scope="col">Method</th>
            <th scope="col">NPC (CAD)</th>
            <th scope="col">Diesel (L/yr)</th>
            <th scope="col">Renewable %</th>
            <th scope="col">Unmet %</th>
          </tr>
        </thead>
        <tbody>
          {% for row in baseline_rows %}
          <tr>
            <td>{{ row.name }}</td>
            <td>${{ "%.0f"|format(row.npc) }}</td>
            <td>{{ "%.0f"|format(row.diesel) }}</td>
            <td>{{ "%.1f"|format(row.renewable) }}</td>
            <td>{{ "%.3f"|format(row.unmet) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>

    {% if figure_path %}
    <section aria-labelledby="figure-heading">
      <h2 id="figure-heading">Monthly Energy Balance</h2>
      <figure class="figure">
        <img src="{{ figure_path }}" alt="Monthly energy balance chart for {{ site_name }}">
      </figure>
    </section>
    {% endif %}

    <section aria-labelledby="uncertainty-heading">
      <h2 id="uncertainty-heading">Multi-Year Uncertainty</h2>
      <table>
        <caption class="sr-only">95 percent confidence intervals across weather years</caption>
        <thead>
          <tr><th scope="col">Metric</th><th scope="col">Estimate</th>
              <th scope="col">95% CI Lower</th><th scope="col">95% CI Upper</th></tr>
        </thead>
        <tbody>
          {% for band in uncertainty_bands %}
          <tr>
            <td>{{ band.metric }}</td>
            <td>{{ "%.2f"|format(band.point) }}</td>
            <td>{{ "%.2f"|format(band.lower) }}</td>
            <td>{{ "%.2f"|format(band.upper) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>

    <section>
      <h2>Storage boundary energy</h2>
      <p>Unknown-source initial SOC {{ "%.2f"|format(initial_soc) }} kWh;
      terminal {{ "%.2f"|format(terminal_soc) }} kWh;
      initial unknown energy delivered {{ "%.2f"|format(unknown_delivery) }} kWh.
      Conversion losses {{ "%.2f"|format(storage_loss) }} kWh.</p>
      <h2>Fixed-design sensitivity</h2>
      <p>Stipulated one-at-a-time stresses, no re-optimization: fuel +/-25%, CAPEX +25%,
      battery replacement year 12/diesel year 15, snow cap 20%, and ideal efficiency without
      temperature penalty or heating energy. Baseline is stressed consistently.</p>
      <table><tr><th>Stress</th><th>NPC CAD</th><th>Savings %</th></tr>
      {% for name, row in sensitivity.items() %}<tr><td>{{ name }}</td>
      <td>{{ "%.0f"|format(row.npc_cad) }}</td><td>{{ "%.2f"|format(row.savings_pct) }}</td></tr>
      {% endfor %}</table>
    </section>
    <section aria-labelledby="limits-heading">
      <h2 id="limits-heading">Limitations</h2>
      <ul>{% for limit in limitations %}<li>{{ limit }}</li>{% endfor %}</ul>
      <p>Input hashes, dependencies and source revision: 
      <a href="evaluation_results.json">run metadata</a>.
      <a href="../docs/LICENSING.md">Licence scope</a>: CC BY 4.0 outputs
      and NASA POWER weather.</p>

    </section>
  </main>
  <footer role="contentinfo">
    <p>Generated by northern-microgrid v{{ version }}. Weather: NASA POWER (CC BY 4.0).</p>
  </footer>
</body>
</html>
"""


def render_site_report(
    site_name: str,
    province: str,
    archetype: str,
    case_data: dict[str, Any],
    baseline_data: dict[str, dict[str, float]],
    uncertainty_bands: list[dict[str, float | str]],
    figure_path: str | None,
    output_path: Path,
    version: str = "0.1.0",
) -> Path:
    """Render an HTML report for one site."""
    env = Environment(autoescape=select_autoescape(["html"]))
    template = env.from_string(REPORT_TEMPLATE)

    baseline_rows = [
        {
            "name": name.replace("_", " ").title(),
            "npc": vals["npc_cad"],
            "diesel": vals["diesel_litres"],
            "renewable": vals["renewable_fraction"] * 100,
            "unmet": vals["unmet_fraction"] * 100,
        }
        for name, vals in baseline_data.items()
        if name != "load_statistics" and "npc_cad" in vals
    ]

    optimized = case_data.get("metrics", {})
    design = case_data.get("design", {})

    html_content = template.render(
        site_name=_escape(site_name),
        province=_escape(province),
        archetype=archetype,
        renewable_pct=optimized.get("renewable_fraction", 0) * 100,
        diesel_litres=optimized.get("diesel_litres", 0),
        npc_cad=case_data.get("lifecycle", {}).get("npc_cad", 0),
        unmet_pct=optimized.get("unmet_fraction", 0) * 100,
        pv_kw=design.get("pv", {}).get("capacity_kw", 0),
        wind_kw=design.get("wind", {}).get("capacity_kw", 0),
        batt_power_kw=design.get("battery", {}).get("power_kw", 0),
        batt_energy_kwh=design.get("battery", {}).get("energy_kwh", 0),
        diesel_kw=design.get("diesel", {}).get("capacity_kw", 0),
        baseline_rows=baseline_rows,
        uncertainty_bands=uncertainty_bands,
        figure_path=figure_path,
        version=version,
        limitations=[
            limit.replace("five-year mean", f"{case_data.get('weather_year_count', 5)}-year mean")
            if case_data.get("weather_year_count", 5) != 5 else limit
            for limit in LIMITATIONS
        ],
        weather_year=case_data.get("weather_year", "not supplied"),
        annual_kwh=case_data.get("load_statistics", {}).get("annual_kwh", 0),
        peak_kw=case_data.get("load_statistics", {}).get("peak_kw", 0),
        sensitivity=case_data.get("sensitivity", {}),
        initial_soc=optimized.get("initial_soc_kwh", 0),
        terminal_soc=optimized.get("terminal_soc_kwh", 0),
        unknown_delivery=optimized.get("initial_unknown_to_load_kwh", 0),
        storage_loss=optimized.get("battery_storage_loss_kwh", 0),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


def load_json_results(path: Path) -> dict[str, Any]:
    """Load results JSON for report generation."""
    with path.open(encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))
