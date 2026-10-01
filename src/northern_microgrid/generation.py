"""PV and wind generation models with temperature and snow effects."""

from __future__ import annotations

import math

import numpy as np

from northern_microgrid.types import PvConfig, WindConfig
from northern_microgrid.weather import snow_cover_fraction


def pv_power_kw(
    ghi_wh_m2: np.ndarray,
    temp_c: np.ndarray,
    precip_mm_hr: np.ndarray,
    config: PvConfig,
) -> np.ndarray:
    """Compute hourly PV AC output in kW from irradiance and temperature.

    Uses a simplified transposition model: GHI scaled by tilt factor, then
    temperature derating and snow cover losses applied.
    """
    tilt_rad = math.radians(config.tilt_deg)
    # Approximate POA factor for south-facing tilt at high latitude
    poa_factor = 0.85 + 0.15 * math.sin(tilt_rad)
    poa_wh_m2 = ghi_wh_m2 * poa_factor

    snow_frac = snow_cover_fraction(temp_c, precip_mm_hr, ghi_wh_m2)
    snow_loss = 1.0 - snow_frac * config.snow_loss_fraction

    temp_factor = 1.0 + config.temp_coeff_pct_per_c / 100.0 * (
        temp_c - config.ref_temp_c
    )

    # Standard test conditions: 1000 W/m2 -> nameplate
    normalized = poa_wh_m2 / 1000.0
    power = config.capacity_kw * normalized * config.derate * temp_factor * snow_loss
    return np.clip(power, 0.0, config.capacity_kw)


def wind_power_kw(wind_ms: np.ndarray, config: WindConfig) -> np.ndarray:
    """Compute hourly wind turbine output using a piecewise power curve."""
    rated = config.capacity_kw
    cut_in = config.cut_in_ms
    rated_speed = config.rated_ms
    cut_out = config.cut_out_ms
    avail = config.availability

    power = np.zeros_like(wind_ms, dtype=np.float64)
    for i, ws in enumerate(wind_ms):
        if ws < cut_in or ws >= cut_out:
            p = 0.0
        elif ws < rated_speed:
            # Cubic region between cut-in and rated
            frac = (ws - cut_in) / (rated_speed - cut_in)
            p = rated * frac**3
        else:
            p = rated
        power[i] = p * avail
    return power
