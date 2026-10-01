"""NASA POWER weather data fetch and streaming storage."""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import requests

POWER_BASE = "https://power.larc.nasa.gov/api/temporal/hourly/point"
POWER_PARAMS = "ALLSKY_SFC_SW_DWN,T2M,WS10M,PRECTOTCORR,ALLSKY_SFC_PAR_TOT"
MAX_URL_LENGTH = 2048
REQUEST_TIMEOUT_S = 120
CHUNK_DAYS = 30
RATE_LIMIT_SLEEP_S = 0.5
NASA_FILL_VALUE = -999.0
STANDARD_YEAR_HOURS = 8760

ALLOWED_POWER_HOSTS = frozenset({"power.larc.nasa.gov"})

WEATHER_COLUMNS = ("ghi_wh_m2", "temp_c", "wind_ms", "precip_mm_hr")


def validate_power_url(url: str) -> None:
    """Validate that a URL targets the NASA POWER API."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
    if parsed.hostname not in ALLOWED_POWER_HOSTS:
        raise ValueError(f"Disallowed host: {parsed.hostname}")


def _date_range_chunks(start: str, end: str, chunk_days: int = CHUNK_DAYS) -> list[tuple[str, str]]:
    """Split a date range into chunks for API requests."""
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    chunks: list[tuple[str, str]] = []
    cursor = start_ts
    while cursor <= end_ts:
        chunk_end = min(cursor + pd.Timedelta(days=chunk_days - 1), end_ts)
        chunks.append((cursor.strftime("%Y%m%d"), chunk_end.strftime("%Y%m%d")))
        cursor = chunk_end + pd.Timedelta(days=1)
    return chunks


def _build_power_url(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
) -> str:
    url = (
        f"{POWER_BASE}?parameters={POWER_PARAMS}"
        f"&community=RE&longitude={longitude}&latitude={latitude}"
        f"&start={start}&end={end}&format=JSON&time-standard=UTC"
    )
    if len(url) > MAX_URL_LENGTH:
        raise ValueError("POWER URL exceeds safe length limit")
    validate_power_url(url)
    return url


def _parse_power_response(payload: dict[str, Any]) -> pd.DataFrame:
    """Parse NASA POWER JSON response into a DataFrame."""
    params = payload["properties"]["parameter"]
    frames: list[pd.DataFrame] = []
    for param_name, series in params.items():
        rows = [{"timestamp": k, param_name: v} for k, v in series.items()]
        frames.append(pd.DataFrame(rows))
    if not frames:
        raise ValueError("Empty POWER response")
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="timestamp", how="outer")
    merged["timestamp"] = pd.to_datetime(merged["timestamp"], format="%Y%m%d%H", utc=True)
    merged = merged.sort_values("timestamp").reset_index(drop=True)
    merged = merged.rename(
        columns={
            "ALLSKY_SFC_SW_DWN": "ghi_wh_m2",
            "T2M": "temp_c",
            "WS10M": "wind_ms",
            "PRECTOTCORR": "precip_mm_hr",
            "ALLSKY_SFC_PAR_TOT": "par_wh_m2",
        }
    )
    return merged


def validate_weather_frame(df: pd.DataFrame) -> None:
    """Reject missing, duplicated, sentinel or out-of-range weather values."""
    if "timestamp" in df.columns:
        if df["timestamp"].duplicated().any():
            raise ValueError("Duplicate weather timestamps")
        if df["timestamp"].isna().any():
            raise ValueError("Missing weather timestamps")

    for col in WEATHER_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Missing weather column: {col}")
        series = df[col]
        if series.isna().any():
            raise ValueError(f"Null values in {col}")
        if np.any(series == NASA_FILL_VALUE):
            raise ValueError(f"NASA fill value in {col}")
        if not np.all(np.isfinite(series.to_numpy(dtype=np.float64))):
            raise ValueError(f"Non-finite values in {col}")

    if (df["ghi_wh_m2"] < 0).any() or (df["ghi_wh_m2"] > 1500).any():
        raise ValueError("ghi_wh_m2 out of physical range")
    if (df["temp_c"] < -80).any() or (df["temp_c"] > 60).any():
        raise ValueError("temp_c out of physical range")
    if (df["wind_ms"] < 0).any() or (df["wind_ms"] > 80).any():
        raise ValueError("wind_ms out of physical range")
    if (df["precip_mm_hr"] < 0).any():
        raise ValueError("precip_mm_hr negative")


def drop_leap_day_hours(df: pd.DataFrame) -> pd.DataFrame:
    """Remove Feb 29 hours from leap years to align with a 365-day calendar."""
    if "timestamp" not in df.columns:
        return df
    ts = pd.to_datetime(df["timestamp"], utc=True)
    mask = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    return df.loc[mask].reset_index(drop=True)


def validate_weather_calendar(df: pd.DataFrame, year: int | None = None) -> None:
    """Require a complete, ordered raw UTC calendar; never sort or impute on load."""
    if "timestamp" not in df or df.empty:
        raise ValueError("Missing weather calendar")
    ts = pd.DatetimeIndex(pd.to_datetime(df["timestamp"], utc=True))
    year = year if year is not None else int(ts[0].year)
    expected = pd.date_range(
        f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left", tz="UTC"
    )
    if not ts.equals(expected):
        raise ValueError(f"Weather calendar must equal the ordered UTC calendar for {year}")


def align_weather_hours(df: pd.DataFrame, n_hours: int = STANDARD_YEAR_HOURS) -> pd.DataFrame:
    """Validate the complete raw year, then remove February 29. No imputation."""
    validate_weather_frame(df)
    validate_weather_calendar(df)
    work = drop_leap_day_hours(df)
    if len(work) != n_hours:
        raise ValueError("Weather calendar length differs from requested simulation length")
    return work.reset_index(drop=True)


def fetch_weather_chunk(
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Fetch one chunk of hourly weather from NASA POWER."""
    url = _build_power_url(latitude, longitude, start, end)
    http = session or requests.Session()
    response = http.get(url, timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    payload = response.json()
    return _parse_power_response(payload)


def weather_cache_path(weather_dir: Path, site_id: str, year: int) -> Path:
    """Return the parquet cache path for a site-year."""
    safe_site = re.sub(r"[^a-z0-9_]", "_", site_id.lower())
    return weather_dir / safe_site / f"{year}.parquet"


def fetch_weather_year(
    latitude: float,
    longitude: float,
    year: int,
    weather_dir: Path,
    site_id: str,
    force: bool = False,
) -> Path:
    """Fetch and cache one year of weather, streaming chunks to parquet."""
    out_path = weather_cache_path(weather_dir, site_id, year)
    if out_path.exists() and not force:
        load_weather_year(out_path)
        metadata = _cache_metadata(out_path)
        if metadata and (
            metadata["latitude"] != latitude
            or metadata["longitude"] != longitude
            or metadata["year"] != year
        ):
            raise ValueError("Weather cache site/year metadata mismatch")
        return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    start = f"{year}0101"
    end = f"{year}1231"
    chunks = _date_range_chunks(start, end)

    session = requests.Session()
    part_paths: list[Path] = []
    for i, (chunk_start, chunk_end) in enumerate(chunks):
        part = out_path.parent / f"{year}_part{i:02d}.parquet"
        if not part.exists() or force:
            df = fetch_weather_chunk(latitude, longitude, chunk_start, chunk_end, session)
            df.to_parquet(part, index=False)
            time.sleep(RATE_LIMIT_SLEEP_S)
        part_paths.append(part)

    first = pd.read_parquet(part_paths[0])
    if len(part_paths) > 1:
        for part in part_paths[1:]:
            first = pd.concat([first, pd.read_parquet(part)], ignore_index=True)
    first = first.drop_duplicates(subset=["timestamp"]).sort_values("timestamp")
    validate_weather_frame(first)
    validate_weather_calendar(first, year)
    first.to_parquet(out_path, index=False)
    metadata = {
        "latitude": latitude,
        "longitude": longitude,
        "site_id": site_id,
        "year": year,
        "sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
        "parameters": POWER_PARAMS,
        "time_standard": "UTC",
        "acquired_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "source_release": "not retained by the chunk parser",
    }
    out_path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2))
    for part in part_paths:
        part.unlink(missing_ok=True)
    return out_path


def _cache_metadata(path: Path) -> dict[str, Any]:
    sidecar = path.with_suffix(".metadata.json")
    if sidecar.exists():
        return dict(json.loads(sidecar.read_text()))
    manifest_path = path.parent.parent / "manifest.json"
    if manifest_path.exists():
        for record in json.loads(manifest_path.read_text())["files"]:
            if record["site_id"] == path.parent.name and str(record["year"]) == path.stem:
                return dict(record)
        raise ValueError("Weather cache absent from source manifest")
    return {}


def load_weather_year(path: Path, n_hours: int = STANDARD_YEAR_HOURS) -> pd.DataFrame:
    """Load cached weather parquet, aligned to standard year length."""
    metadata = _cache_metadata(path)
    if metadata:
        if metadata["sha256"] != hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError("Weather cache hash mismatch")
        from northern_microgrid.sites import CANADIAN_SITES

        if metadata.get("site_id") != path.parent.name:
            raise ValueError("Weather cache site metadata mismatch")
        site = CANADIAN_SITES.get(path.parent.name)
        if site and (
            metadata["latitude"] != site.latitude or metadata["longitude"] != site.longitude
        ):
            raise ValueError("Weather cache coordinates mismatch")
        if str(metadata["year"]) != path.stem:
            raise ValueError("Weather cache year metadata mismatch")
    df = pd.read_parquet(path)
    validate_weather_calendar(df, int(path.stem) if path.stem.isdigit() else None)
    return align_weather_hours(df, n_hours)


def snow_cover_fraction(
    temp_c: np.ndarray,
    precip_mm_hr: np.ndarray,
    ghi_wh_m2: np.ndarray,
) -> np.ndarray:
    """Estimate hourly snow cover fraction on PV arrays."""
    n = len(temp_c)
    cover = np.zeros(n, dtype=np.float64)
    accumulation = 0.0
    for i in range(n):
        if temp_c[i] < 0.0 and precip_mm_hr[i] > 0.1:
            accumulation = min(1.0, accumulation + precip_mm_hr[i] * 0.05)
        if temp_c[i] > 2.0 or ghi_wh_m2[i] > 150.0:
            melt_rate = 0.15 if ghi_wh_m2[i] > 150.0 else 0.05
            accumulation = max(0.0, accumulation - melt_rate)
        cover[i] = accumulation
    return cover
