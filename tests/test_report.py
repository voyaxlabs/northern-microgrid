"""Tests for HTML report generation."""

from pathlib import Path

from northern_microgrid.report import render_site_report


def test_render_report(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    render_site_report(
        site_name="Test Site",
        province="Test Province",
        archetype="remote_camp",
        case_data={
            "metrics": {
                "renewable_fraction": 0.5,
                "diesel_litres": 10000.0,
                "unmet_fraction": 0.005,
            },
            "lifecycle": {"npc_cad": 500000.0},
            "design": {
                "pv": {"capacity_kw": 50.0},
                "wind": {"capacity_kw": 20.0},
                "battery": {"power_kw": 25.0, "energy_kwh": 100.0},
                "diesel": {"capacity_kw": 90.0},
            },
        },
        baseline_data={
            "diesel_only": {
                "npc_cad": 600000.0,
                "diesel_litres": 20000.0,
                "renewable_fraction": 0.0,
                "unmet_fraction": 0.0,
            },
            "optimized": {
                "npc_cad": 500000.0,
                "diesel_litres": 10000.0,
                "renewable_fraction": 0.5,
                "unmet_fraction": 0.005,
            },
        },
        uncertainty_bands=[
            {"metric": "npc", "point": 500000, "lower": 480000, "upper": 520000},
        ],
        figure_path=None,
        output_path=out,
    )
    content = out.read_text(encoding="utf-8")
    assert "<h1>" in content
    assert "Test Site" in content
    assert "role=\"main\"" in content
    assert "\u2014" not in content
