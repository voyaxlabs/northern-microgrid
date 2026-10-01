"""Tests for sizing baselines and optimization."""

import numpy as np
import pandas as pd

from northern_microgrid.sizing import (
    SizingConstraints,
    diesel_only_design,
    optimize_design,
    rule_of_thumb_design,
)


def _sunny_weather(n: int = 8760) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ghi_wh_m2": np.full(n, 400.0),
            "temp_c": np.full(n, -5.0),
            "wind_ms": np.full(n, 4.0),
            "precip_mm_hr": np.zeros(n),
        }
    )


def test_diesel_only_has_no_pv() -> None:
    design = diesel_only_design(peak_kw=50.0)
    assert design.pv.capacity_kw == 0.0
    assert design.diesel.capacity_kw > 0.0


def test_rule_of_thumb_has_pv() -> None:
    design = rule_of_thumb_design(peak_kw=50.0, daily_kwh=100.0)
    assert design.pv.capacity_kw > 0.0
    assert design.battery.energy_kwh > 0.0


def test_optimize_finds_design() -> None:
    load = np.full(8760, 20.0)
    weather = _sunny_weather()
    constraints = SizingConstraints(
        pv_kw_range=(0.0, 50.0, 10.0),
        wind_kw_range=(0.0, 0.0, 10.0),
        battery_kwh_range=(0.0, 100.0, 25.0),
    )
    result = optimize_design(load, weather, peak_kw=30.0, constraints=constraints)
    assert result.evaluations > 0
    assert result.npc_cad > 0.0
