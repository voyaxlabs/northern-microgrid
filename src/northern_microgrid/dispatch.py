"""Hourly dispatch simulation for hybrid microgrids."""

from __future__ import annotations

import numpy as np

from northern_microgrid.generation import pv_power_kw, wind_power_kw
from northern_microgrid.types import (
    BatteryConfig,
    DieselConfig,
    HourlyDispatchResult,
    SimulationMetrics,
    SystemDesign,
)

NASA_FILL_VALUE = -999.0


def charge_efficiency(temp_c: float, config: BatteryConfig) -> float:
    """One-way charge efficiency with cold/hot derating."""
    base = config.charge_efficiency
    cold_penalty = max(0.0, config.ref_temp_c - temp_c) * abs(config.temp_coeff_pct_per_c) / 100.0
    hot_penalty = max(0.0, temp_c - config.ref_temp_c) * abs(config.temp_coeff_pct_per_c) / 100.0
    factor = 1.0 - cold_penalty - hot_penalty
    return base * max(0.7, min(1.0, factor))


def discharge_efficiency(temp_c: float, config: BatteryConfig) -> float:
    """One-way discharge efficiency with cold/hot derating."""
    base = config.discharge_efficiency
    cold_penalty = max(0.0, config.ref_temp_c - temp_c) * abs(config.temp_coeff_pct_per_c) / 100.0
    hot_penalty = max(0.0, temp_c - config.ref_temp_c) * abs(config.temp_coeff_pct_per_c) / 100.0
    factor = 1.0 - cold_penalty - hot_penalty
    return base * max(0.7, min(1.0, factor))


def simulate_hourly(
    load_kw: np.ndarray,
    ghi_wh_m2: np.ndarray,
    temp_c: np.ndarray,
    wind_ms: np.ndarray,
    precip_mm_hr: np.ndarray,
    design: SystemDesign,
) -> HourlyDispatchResult:
    """Run an 8760-hour dispatch simulation with priority: PV, wind, battery, diesel."""
    n = len(load_kw)
    pv_gen = pv_power_kw(ghi_wh_m2, temp_c, precip_mm_hr, design.pv)
    wind_gen = wind_power_kw(wind_ms, design.wind)

    batt_cfg = design.battery
    diesel_cfg = design.diesel

    soc = np.zeros(n + 1, dtype=np.float64)
    soc_renewable = np.zeros(n + 1, dtype=np.float64)
    soc[0] = (batt_cfg.min_soc + batt_cfg.max_soc) / 2.0 * batt_cfg.energy_kwh
    soc_renewable[0] = 0.0

    charge = np.zeros(n, dtype=np.float64)
    discharge = np.zeros(n, dtype=np.float64)
    diesel = np.zeros(n, dtype=np.float64)
    diesel_dump = np.zeros(n, dtype=np.float64)
    unmet = np.zeros(n, dtype=np.float64)
    curtailed = np.zeros(n, dtype=np.float64)
    pv_to_load = np.zeros(n, dtype=np.float64)
    wind_to_load = np.zeros(n, dtype=np.float64)
    batt_to_load = np.zeros(n, dtype=np.float64)
    renewable_to_load = np.zeros(n, dtype=np.float64)

    e_min = batt_cfg.min_soc * batt_cfg.energy_kwh
    e_max = batt_cfg.max_soc * batt_cfg.energy_kwh

    for t in range(n):
        renewable = pv_gen[t] + wind_gen[t]
        load_t = load_kw[t]
        net = renewable - load_t

        if net >= 0:
            direct = load_t
            pv_to_load[t] = min(pv_gen[t], direct)
            wind_to_load[t] = min(wind_gen[t], direct - pv_to_load[t])
            renewable_to_load[t] = direct
            surplus = net
            headroom = e_max - soc[t]
            ch_eff = charge_efficiency(float(temp_c[t]), batt_cfg)
            max_charge = min(batt_cfg.power_kw, headroom / ch_eff) if headroom > 0 else 0.0
            ch = min(surplus, max_charge)
            charge[t] = ch
            energy_in = ch * ch_eff
            soc[t + 1] = soc[t] + energy_in
            soc_renewable[t + 1] = soc_renewable[t] + energy_in
            surplus -= ch
            curtailed[t] = max(0.0, surplus)
        else:
            deficit = load_t - renewable
            pv_to_load[t] = pv_gen[t]
            wind_to_load[t] = wind_gen[t]
            renewable_to_load[t] = renewable
            available = min(
                batt_cfg.power_kw,
                (soc[t] - e_min) * discharge_efficiency(float(temp_c[t]), batt_cfg),
            )
            dis = min(deficit, available)
            discharge[t] = dis
            batt_to_load[t] = dis
            dis_eff = discharge_efficiency(float(temp_c[t]), batt_cfg)
            energy_out = dis / dis_eff if dis_eff > 0 else 0.0
            ren_frac = soc_renewable[t] / soc[t] if soc[t] > 0 else 0.0
            renewable_to_load[t] += dis * ren_frac
            soc[t + 1] = soc[t] - energy_out
            soc_renewable[t + 1] = max(0.0, soc_renewable[t] - energy_out * ren_frac)
            deficit -= dis

            if deficit > 0:
                min_diesel = diesel_cfg.min_load_fraction * diesel_cfg.capacity_kw
                diesel_out = min(deficit, diesel_cfg.capacity_kw)
                if diesel_out > 0 and diesel_out < min_diesel:
                    diesel_out = min(min_diesel, diesel_cfg.capacity_kw)
                diesel[t] = diesel_out
                dumped = max(0.0, diesel_out - deficit)
                diesel_dump[t] = dumped
                deficit -= diesel_out
                unmet[t] = max(0.0, deficit)

        soc[t + 1] = float(max(e_min, min(e_max, soc[t + 1])))
        if soc[t + 1] > 0:
            soc_renewable[t + 1] = float(max(0.0, min(soc[t + 1], soc_renewable[t + 1])))
        else:
            soc_renewable[t + 1] = 0.0

    soc_frac = soc[:-1] / batt_cfg.energy_kwh if batt_cfg.energy_kwh > 0 else np.zeros(n)

    return HourlyDispatchResult(
        load_kw=load_kw.tolist(),
        pv_gen_kw=pv_gen.tolist(),
        wind_gen_kw=wind_gen.tolist(),
        battery_charge_kw=charge.tolist(),
        battery_discharge_kw=discharge.tolist(),
        battery_soc=soc_frac.tolist(),
        diesel_kw=diesel.tolist(),
        diesel_dump_kw=diesel_dump.tolist(),
        unmet_kw=unmet.tolist(),
        curtailed_kw=curtailed.tolist(),
        pv_to_load_kw=pv_to_load.tolist(),
        wind_to_load_kw=wind_to_load.tolist(),
        battery_to_load_kw=batt_to_load.tolist(),
        renewable_to_load_kw=renewable_to_load.tolist(),
        battery_energy_kwh=batt_cfg.energy_kwh,
        initial_soc_kwh=float(soc[0]),
        terminal_soc_kwh=float(soc[-1]),
        terminal_renewable_soc_kwh=float(soc_renewable[-1]),
    )


def assert_energy_conservation(
    dispatch: HourlyDispatchResult,
    tolerance_kwh: float = 1.0,
) -> None:
    """Verify load balance and the generator/storage ledger (one-hour steps)."""
    load = np.array(dispatch.load_kw)
    pv = np.array(dispatch.pv_to_load_kw)
    wind = np.array(dispatch.wind_to_load_kw)
    batt = np.array(dispatch.battery_to_load_kw)
    diesel = np.array(dispatch.diesel_kw) - np.array(dispatch.diesel_dump_kw)
    unmet = np.array(dispatch.unmet_kw)
    supply = pv + wind + batt + diesel + unmet
    imbalance = float(np.abs(supply - load).sum())
    if imbalance > tolerance_kwh:
        raise ValueError(f"Energy conservation failed: {imbalance:.2f} kWh imbalance")

    stored = np.diff(np.array(dispatch.battery_soc) * dispatch.battery_energy_kwh)
    stored = np.append(
        stored, dispatch.terminal_soc_kwh - (dispatch.battery_soc[-1] * dispatch.battery_energy_kwh)
    )
    charge = np.array(dispatch.battery_charge_kw)
    discharge = np.array(dispatch.battery_discharge_kw)
    losses = charge - discharge - stored
    raw = np.array(dispatch.pv_gen_kw) + np.array(dispatch.wind_gen_kw)
    ledger = (
        raw
        + np.array(dispatch.diesel_kw)
        + unmet
        - load
        - np.array(dispatch.curtailed_kw)
        - np.array(dispatch.diesel_dump_kw)
        - losses
        - stored
    )
    if np.abs(ledger).sum() > tolerance_kwh or np.any(losses < -1e-7):
        raise ValueError("Full system energy conservation failed")


def aggregate_metrics(
    dispatch: HourlyDispatchResult,
    diesel_cfg: DieselConfig,
) -> SimulationMetrics:
    """Compute annual metrics from hourly dispatch."""
    load = np.array(dispatch.load_kw)
    diesel = np.array(dispatch.diesel_kw)
    diesel_dump = np.array(dispatch.diesel_dump_kw)
    pv = np.array(dispatch.pv_gen_kw)
    wind = np.array(dispatch.wind_gen_kw)
    unmet = np.array(dispatch.unmet_kw)
    curtailed = np.array(dispatch.curtailed_kw)
    renewable_to_load = np.array(dispatch.renewable_to_load_kw)
    charge = np.array(dispatch.battery_charge_kw)
    discharge = np.array(dispatch.battery_discharge_kw)

    total_load = float(load.sum())
    unmet_kwh = float(unmet.sum())
    diesel_kwh = float(diesel.sum())
    diesel_dump_kwh = float(diesel_dump.sum())
    diesel_litres = diesel_kwh * diesel_cfg.fuel_l_per_kwh
    pv_kwh = float(pv.sum())
    wind_kwh = float(wind.sum())
    renewable_gen = pv_kwh + wind_kwh
    served = total_load - unmet_kwh
    ren_delivered = float(renewable_to_load.sum())
    ren_frac_delivered = ren_delivered / served if served > 0 else 0.0
    gross_ren_frac = renewable_gen / served if served > 0 else 0.0

    storage_loss = float(
        charge.sum() - discharge.sum() - (dispatch.terminal_soc_kwh - dispatch.initial_soc_kwh)
    )

    return SimulationMetrics(
        total_load_kwh=total_load,
        unmet_load_kwh=unmet_kwh,
        unmet_fraction=unmet_kwh / total_load if total_load > 0 else 0.0,
        diesel_kwh=diesel_kwh,
        diesel_litres=diesel_litres,
        diesel_dump_kwh=diesel_dump_kwh,
        pv_generation_kwh=pv_kwh,
        wind_generation_kwh=wind_kwh,
        curtailed_kwh=float(curtailed.sum()),
        gross_renewable_fraction=gross_ren_frac,
        renewable_fraction=ren_frac_delivered,
        renewable_delivered_kwh=ren_delivered,
        battery_storage_loss_kwh=storage_loss,
        initial_soc_kwh=dispatch.initial_soc_kwh,
        terminal_soc_kwh=dispatch.terminal_soc_kwh,
        terminal_renewable_soc_kwh=dispatch.terminal_renewable_soc_kwh,
        initial_unknown_to_load_kwh=float(
            discharge.sum()
            - (
                renewable_to_load.sum()
                - np.array(dispatch.pv_to_load_kw).sum()
                - np.array(dispatch.wind_to_load_kw).sum()
            )
        ),
        co2_kg=diesel_litres * diesel_cfg.co2_kg_per_l,
    )


def simulate_year(
    load_kw: np.ndarray,
    weather_df: object,
    design: SystemDesign,
) -> tuple[HourlyDispatchResult, SimulationMetrics]:
    """Convenience wrapper accepting a weather DataFrame."""
    import pandas as pd

    if not isinstance(weather_df, pd.DataFrame):
        raise TypeError("weather_df must be a pandas DataFrame")
    ghi = weather_df["ghi_wh_m2"].to_numpy(dtype=np.float64)
    temp = weather_df["temp_c"].to_numpy(dtype=np.float64)
    wind = weather_df["wind_ms"].to_numpy(dtype=np.float64)
    precip = weather_df["precip_mm_hr"].to_numpy(dtype=np.float64)

    if len(ghi) != len(load_kw):
        raise ValueError(f"Weather length {len(ghi)} != load length {len(load_kw)}")

    dispatch = simulate_hourly(load_kw, ghi, temp, wind, precip, design)
    assert_energy_conservation(dispatch)
    metrics = aggregate_metrics(dispatch, design.diesel)
    if metrics.renewable_fraction > 1.0 + 1e-6:
        raise ValueError(f"Renewable delivered fraction exceeds 1.0: {metrics.renewable_fraction}")
    return dispatch, metrics
