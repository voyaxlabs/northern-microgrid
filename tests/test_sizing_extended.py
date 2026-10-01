"""Extended sizing tests."""

import numpy as np
import pandas as pd

from northern_microgrid.sizing import fixed_renewable_design


def test_fixed_renewable_design() -> None:
    design = fixed_renewable_design(50.0, 30.0, 10.0, 80.0)
    assert design.pv.capacity_kw == 30.0
    assert design.battery.energy_kwh == 80.0


def test_dispatch_length_mismatch() -> None:
    from northern_microgrid.dispatch import simulate_year
    from northern_microgrid.sizing import diesel_only_design

    load = np.full(100, 10.0)
    weather = pd.DataFrame(
        {
            "ghi_wh_m2": np.full(50, 200.0),
            "temp_c": np.full(50, -5.0),
            "wind_ms": np.full(50, 5.0),
            "precip_mm_hr": np.zeros(50),
        }
    )
    import pytest

    with pytest.raises(ValueError, match="Weather length"):
        simulate_year(load, weather, diesel_only_design(20.0))
