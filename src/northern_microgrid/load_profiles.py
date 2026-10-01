"""Synthetic load profile archetypes for remote northern sites.

Profiles are original analytic shapes with stipulated targets; see
docs/DATA_MANIFEST.md and docs/technical-report.md for provenance.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from northern_microgrid.types import LoadArchetype

HOURS_PER_YEAR = 8760


def _xeni_gwetin_normalized() -> np.ndarray:
    """Original analytic residential shape; constants are stipulated."""
    hours = np.arange(24, dtype=np.float64)
    base = 0.04 + 0.12 * np.exp(-0.5 * ((hours - 7.0) / 2.0) ** 2)
    base += 0.18 * np.exp(-0.5 * ((hours - 19.0) / 2.5) ** 2)
    base += 0.03 * np.exp(-0.5 * ((hours - 12.0) / 1.5) ** 2)
    return np.asarray(base / base.sum(), dtype=np.float64)


def _camp_normalized() -> np.ndarray:
    """Remote exploration camp profile with workshop and lighting loads."""
    hours = np.arange(24, dtype=np.float64)
    base = 0.035 + 0.10 * (1.0 - np.cos(2 * math.pi * (hours - 6) / 24))
    base += 0.08 * np.exp(-0.5 * ((hours - 8.0) / 2.0) ** 2)
    base += 0.06 * np.exp(-0.5 * ((hours - 20.0) / 2.0) ** 2)
    return np.asarray(base / base.sum(), dtype=np.float64)


def _research_station_normalized() -> np.ndarray:
    """Research station with field-season uplift (May-September)."""
    hours = np.arange(24, dtype=np.float64)
    base = 0.03 + 0.08 * np.exp(-0.5 * ((hours - 9.0) / 3.0) ** 2)
    base += 0.06 * np.exp(-0.5 * ((hours - 15.0) / 2.0) ** 2)
    base += 0.05 * np.exp(-0.5 * ((hours - 20.0) / 2.5) ** 2)
    return np.asarray(base / base.sum(), dtype=np.float64)


_ARCHETYPE_SHAPES: dict[str, np.ndarray] = {
    "remote_residential": _xeni_gwetin_normalized(),
    "remote_camp": _camp_normalized(),
    "research_station": _research_station_normalized(),
}

ARCHETYPE_DEFAULTS: dict[str, tuple[float, float]] = {
    # (target_daily_kwh, peak_kw_cap)
    "remote_residential": (7.2, 2.6),
    "remote_camp": (480.0, 85.0),
    "research_station": (180.0, 27.0),
}


def seasonal_multiplier(hour_of_year: int, archetype: str) -> float:
    """Northern seasonal load multiplier."""
    day = hour_of_year // 24
    doy = int(day * 365.25 / 365) % 365
    winter = 1.0 + 0.25 * math.cos(2 * math.pi * (doy - 15) / 365.0)
    if archetype == "research_station":
        month = doy // 30
        field_season = 4 <= month <= 8
        return winter * (1.35 if field_season else 0.85)
    return winter


def local_hour_of_day(utc_hour_index: int, utc_offset_hours: int) -> int:
    """Map a UTC hour index to local hour-of-day (0-23)."""
    return (utc_hour_index + utc_offset_hours) % 24


def generate_hourly_load(
    archetype: LoadArchetype,
    daily_kwh: float | None = None,
    peak_kw: float | None = None,
    n_hours: int = HOURS_PER_YEAR,
    utc_offset_hours: int = -7,
) -> np.ndarray:
    """Generate an 8760-hour load profile aligned to UTC weather timestamps."""
    if archetype not in _ARCHETYPE_SHAPES:
        raise ValueError(f"Unknown archetype: {archetype}")

    defaults = ARCHETYPE_DEFAULTS[archetype]
    daily = daily_kwh if daily_kwh is not None else defaults[0]
    peak_cap = peak_kw if peak_kw is not None else defaults[1]
    shape = _ARCHETYPE_SHAPES[archetype]

    loads = np.empty(n_hours, dtype=np.float64)
    for h in range(n_hours):
        local_hod = local_hour_of_day(h, utc_offset_hours)
        loads[h] = shape[local_hod] * daily * seasonal_multiplier(h, archetype)

    current_peak = float(loads.max())
    if current_peak > peak_cap:
        loads *= peak_cap / current_peak
    return loads


def load_statistics(load_kw: np.ndarray) -> dict[str, float]:
    """Return realized load statistics for reporting."""
    return {
        "annual_kwh": float(load_kw.sum()),
        "mean_daily_kwh": float(load_kw.sum() / 365.0),
        "peak_kw": float(load_kw.max()),
    }


def load_archetype_metadata(archetype: LoadArchetype) -> dict[str, str | float]:
    """Return citation metadata for a load archetype."""
    citations = {
        "remote_residential": (
            "Original analytic residential profile; stipulated 7.2 kWh/day "
            "(not extracted measured data)"
        ),
        "remote_camp": (
            "Original synthetic camp profile with stipulated targets; "
            "not a shipped measured profile"
        ),
        "research_station": (
            "Original synthetic station profile; contextual citation: Sambor, Penn and Jacobson "
            "(Energy Nexus 10, 2023, DOI 10.1016/j.nexus.2023.100200)"
        ),
    }
    daily, peak_cap = ARCHETYPE_DEFAULTS[archetype]
    return {
        "archetype": archetype,
        "citation": citations[archetype],
        "target_daily_kwh": daily,
        "peak_kw_cap": peak_cap,
        "profile_type": "synthetic",
    }
