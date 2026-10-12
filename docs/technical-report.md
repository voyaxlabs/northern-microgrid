# Northern Microgrid Sizing: Technical Report

**Author:** Amirhossein Daneshpajouh, VoyaX Labs  
**Date:** October 2026  
**Version:** 0.1.0

## Abstract

We present an open-source tool for sizing off-grid photovoltaic, wind, battery and diesel hybrid systems at Canadian northern and remote sites. The package simulates 8760-hour dispatch with temperature-dependent PV performance, a snow-cover derating model, cold-penalized battery one-way efficiencies, and multi-year weather uncertainty from NASA POWER. We evaluate four sites (Iqaluit, Inuvik, Whitehorse, Dease Lake) against diesel-only and rule-of-thumb baselines. In simulation, optimized designs reduce net present cost by 11.0-18.4% versus diesel-only under a constant-year simplified economic scenario while maintaining zero unmet load for a synthetic remote camp archetype.

## 1. Introduction

Remote and Arctic communities in Canada depend heavily on diesel generation. Hybrid renewable microgrids can reduce fuel use and emissions, but sizing requires site-specific weather data, load scenarios, and economic assumptions. Commercial tools such as HOMER Pro are widely used but closed source. Open alternatives (SAMA, SAMBA, MicroGridsPy) provide CLI workflows, optimization, and multi-year or stochastic analysis in other configurations, this repository supplies a specific synthetic case study, with no claim that it is absent elsewhere.

This work contributes:

1. A typed Python package with hourly simulation, energy ledger, and grid-search sizing
2. A four-site Canadian northern case study on NASA POWER weather (2018-2022)
3. Bootstrap uncertainty intervals across weather years for a fixed design
4. Contextual literature comparison to Colville Lake and KLRS (not automated validation)

## 2. Related work

**SAMA** (Sadat, Takahashi and Pearce, 2023) provides open-source microgrid sizing/dispatch with CLI, GUI, reports and degradation modelling. **SAMBA** uses LP/MILP sizing with a one-command CLI and structured result artifacts. **MicroGridsPy** (ECOS 2024) integrates NASA POWER and rural load archetypes with stochastic optimization.

**Colville Lake** (Turcotte, 2019 NRCan poster) documents Canada's first high-penetration Arctic renewable microgrid with monitored PV-storage-diesel data: approximately 17% PV contribution and more than 31,000 L diesel savings for a 160 kW peak load system. **KLRS** (Sambor, Penn and Jacobson, 2023, Energy Nexus 10, 100200, DOI 10.1016/j.nexus.2023.100200) reports 67% of load served by PV and battery at a Yukon research station with 48 kW PV and 27 kW battery power rating.

## 3. Method

### 3.1 Weather data

Hourly data from NASA POWER (CC BY 4.0): global horizontal irradiance, 2 m temperature, 10 m wind speed, precipitation. Data are fetched in 30-day chunks and cached as parquet. Leap-day hours are removed before alignment to 8760 hours. Sentinel (-999) and out-of-range values are rejected.

### 3.2 Load and timezone policy

Load profiles are synthetic hourly shapes with fixed UTC offsets per site (Iqaluit UTC-5; others UTC-7). Morning/evening peaks are aligned to local standard time. No daylight saving time modelling.

### 3.3 PV model

POA irradiance approximated from GHI with tilt factor. Snow cover accumulates when T < 0 C and precip > 0; melts when T > 2 C or GHI > 150 Wh/m2 (max 5% PV reduction).

### 3.4 Battery and dispatch

Round-trip efficiency 0.92 implemented as symmetric one-way efficiencies (sqrt(0.92) each). Cold and hot temperatures reduce one-way efficiency. Dispatch priority: PV, wind, battery discharge, diesel, unmet load. Diesel minimum load surplus is recorded as dump energy. Renewable fraction reported as energy delivered to load from PV, wind, and renewable-charged battery discharge.

### 3.5 Sizing optimization

Grid search minimizes net present cost subject to unmet load <= 1%.

### 3.6 Economics

Constant-year simplified scenario: 25-year project life, 6% discount rate, undiscounted annual O&M repeated. LCOE uses discounted delivered energy in the denominator (SAM-style). CAPEX constants are stipulated CAD scenario assumptions; no extraction, FX conversion or remote-premium derivation is retained.

## 4. Data

See `docs/DATA_MANIFEST.md`. Load archetypes are synthetic scenarios with target daily energy and peak caps; realized peaks are reported in RESULTS.md.

## 5. Experiments

Four sites, `remote_camp` archetype, optimization on 2018 weather, evaluation on 2018-2022. Baselines: diesel-only, rule-of-thumb, fixed-renewable (80% of optimized).

## 6. Results

See `RESULTS.md` (generated from evaluation JSON). Headline renewable metric is delivered fraction, not gross generation divided by load.

## 7. Limitations

- Simulation-only: grid-optimal within the searched capacities, fixed dispatch and fixed diesel sizing; no field calibration or external validation.
- PV uses a fixed GHI tilt factor and ambient rather than cell temperature; azimuth is ignored. 10 m wind is used without adjustment to the configured 30 m hub height.
- Snow loss is uncalibrated and capped at 5% in the default scenario. Battery efficiency uses ambient temperature without heating loads, thermal dynamics, cold charging restrictions or capacity degradation.
- Economics repeat one year's fuel and O&M for 25 discounted years; replacement, fuel escalation, salvage and component degradation are omitted. All cost, load and coefficient values are stipulated scenario assumptions, not extracted quotes.
- Bootstrap intervals estimate the five-year mean of fixed-design annual outcomes (1000 resamples, seed 42), not a future-year prediction interval or lifecycle-cost uncertainty. The optimization year is reused; consecutive-year independence and interval coverage are unchecked. Cost/load/model uncertainty and climate trends are excluded.
- Diesel is sized at 110% of realized peak with unlimited fuel and no outages. Low unmet load is not redundancy, electrical stability, black-start or contingency evidence.
- The 80%-of-optimized baseline depends on the proposed design; it is not an independently selected competitor. Loads are synthetic, with fixed UTC offsets and no DST.
- Each year starts at midpoint SOC of unknown source and ends unconstrained. Initial energy is not credited as renewable; initial/terminal SOC and unknown-source delivery are quantified below. No warm-up or cyclic-year condition is imposed.
- NASA POWER resolution is 0.5 x 0.625 degrees for meteorology and 1 x 1 degree for solar; site microclimate and long-term climate changes are not modelled.

H1 is met at two of four default sites; H2 is not met and H3 is untested. Fixed-design sensitivity results are generated in RESULTS.md. Public author attribution is retained under [LICENSING.md](LICENSING.md).

## 8. References

1. Sadat, Takahashi and Pearce (2023). SAMA primary tool paper. https://doi.org/10.1016/j.enconman.2023.117686
2. Turcotte, D. (2019). Colville Lake microgrid performance. NRCan CanmetENERGY poster.
3. Sambor, D.J., Penn, I. and Jacobson, M.Z. (2023). Energy Nexus 10, 100200. https://doi.org/10.1016/j.nexus.2023.100200
4. NASA POWER Project. https://power.larc.nasa.gov/ (CC BY 4.0)
5. NREL ATB 2024. https://catalog.data.gov/dataset/2024-annual-technology-baseline-atb-cost-and-performance-data-for-electricity-generation-t (CC BY 4.0)
6. [Revision-pinned capability map](PRIOR_ART.md). Numeric load/cost/efficiency constants are scenario assumptions, not extracted source data.
