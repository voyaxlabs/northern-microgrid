"""Tests for figure generation."""

from pathlib import Path

import numpy as np
import pandas as pd

from northern_microgrid.figures import baseline_comparison_chart, monthly_energy_balance
from northern_microgrid.sizing import diesel_only_design


def test_monthly_balance_figure(tmp_path: Path) -> None:
    load = np.full(8760, 20.0)
    weather = pd.DataFrame(
        {
            "ghi_wh_m2": np.full(8760, 300.0),
            "temp_c": np.full(8760, -5.0),
            "wind_ms": np.full(8760, 5.0),
            "precip_mm_hr": np.zeros(8760),
        }
    )
    design = diesel_only_design(peak_kw=50.0)
    out = tmp_path / "balance.png"
    monthly_energy_balance(load, weather, design, out, "Test")
    assert out.exists()
    assert out.stat().st_size > 0


def test_baseline_chart(tmp_path: Path) -> None:
    data = {
        "diesel_only": {"npc_cad": 100.0},
        "optimized": {"npc_cad": 80.0},
    }
    out = tmp_path / "baseline.png"
    baseline_comparison_chart(data, out)
    assert out.exists()
