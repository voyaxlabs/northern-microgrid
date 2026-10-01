# Preserved evaluation protocol: Northern Microgrid Sizing Benchmark

**Corrected specification:** 2026-10-01  
**Project:** northern-microgrid v0.1.0  
**Author:** Amirhossein Daneshpajouh, VoyaX Labs

This is a preserved evaluation protocol; pre-result chronology is unverified. The earlier specification and final results share the original commit. Corrections and deferred checks are documented in [PROTOCOL_DEVIATIONS.md](PROTOCOL_DEVIATIONS.md). SHA-256 records current content integrity only.

## Research question

How much diesel fuel and lifecycle cost can optimized PV-wind-battery-diesel hybrid sizing save compared to diesel-only and rule-of-thumb sizing, across four Canadian northern sites, when weather uncertainty is propagated across five weather years?

## Hypotheses

1. Optimized hybrid sizing reduces net present cost (NPC) by at least 15% versus diesel-only at remote camp scale, while maintaining unmet load below 1%.
2. Multi-year weather uncertainty produces NPC 95% confidence intervals wider than 10% of the point estimate at Arctic sites (Iqaluit, Inuvik).
3. Optimized designs achieve renewable energy fractions within published validation bands for comparable northern microgrids (Colville Lake: contextual PV contribution; KLRS: 50-75% year-round solar fraction for research station archetype).

## Data

### Sites (specified)

| ID | Location | Lat | Lon | Province/Territory |
|---|---|---|---|---|
| iqaluit | Iqaluit | 63.75 | -68.52 | Nunavut |
| inuvik | Inuvik | 68.36 | -133.72 | Northwest Territories |
| whitehorse | Whitehorse | 60.72 | -135.05 | Yukon |
| dease_lake | Dease Lake | 58.44 | -130.03 | British Columbia |

### Weather years (fixed)

2018, 2019, 2020, 2021, 2022. Sourced from NASA POWER hourly API (CC BY 4.0).

Optimization uses 2018 weather. Evaluation reports metrics across all five years with bootstrap 95% confidence intervals (n=1000 resamples).

### Load archetype (primary)

`remote_camp`: 480 kWh/day, 85 kW peak cap (realized 43.44 kW in the default synthetic shape).

Secondary sensitivity: `research_station` archetype for KLRS validation comparison only.

## Methods

### Simulation

- 8760-hour chronological dispatch per weather year
- Priority: PV, wind, battery discharge, diesel, unmet load
- PV: GHI-based with tilt factor, temperature coefficient (-0.35%/C), snow cover model
- Wind: cubic power curve (cut-in 3 m/s, rated 12 m/s, cut-out 25 m/s)
- Battery: round-trip efficiency 92%, SOC limits 15-95%, temperature derating
- Diesel: minimum load 40% of rated capacity

### Sizing optimization

Grid search over:
- PV: 0-200 kW in 10 kW steps
- Wind: 0-100 kW in 10 kW steps
- Battery: 0-500 kWh in 25 kWh steps (power = 0.5 x energy)

Objective: minimize NPC subject to unmet load fraction <= 1%.

### Baselines (fixed)

1. **diesel_only:** Generator sized to 110% of peak load; no renewables.
2. **rule_of_thumb:** PV = 1.2 x daily_kwh / 3 h sun; battery = 3 days autonomy; diesel backup at 110% peak.
3. **fixed_renewable:** 80% of optimized PV and battery capacities (no re-optimization).
4. **optimized:** Grid search result (proposed method).

### Economics (fixed parameters)

| Parameter | Value | Source |
|---|---|---|
| Project lifetime | 25 years | Stipulated scenario assumption |
| Discount rate | 6% | Stipulated scenario assumption |
| PV CAPEX | $2,200/kW | Stipulated scenario assumption |
| Wind CAPEX | $2,800/kW | Stipulated scenario assumption |
| Battery power CAPEX | $400/kW | Stipulated scenario assumption |
| Battery energy CAPEX | $350/kWh | Stipulated scenario assumption |
| Diesel CAPEX | $800/kW | Stipulated scenario assumption |
| Diesel fuel | $2.10/L | Stipulated scenario assumption |
| CO2 factor | 2.68 kg/L diesel | Stipulated scenario assumption |

## Metrics (primary)

| Metric | Definition |
|---|---|
| NPC (CAD) | Net present cost over 25 years |
| LCOE (CAD/kWh) | Levelized cost of energy |
| Annual diesel (L) | Total diesel fuel consumption |
| Renewable fraction | Direct PV/wind plus renewable-source battery discharge / served load |
| Unmet load fraction | Unmet kWh / total load |
| CO2 (kg/year) | Diesel litres x 2.68 |

## Uncertainty

Bootstrap 95% confidence intervals across five weather years for: annual diesel, renewable fraction, NPC. Resample with replacement, n=1000, seed=42.

## Deferred validation checks

Compare optimized `research_station` archetype results against published KLRS and Colville Lake metrics (order-of-magnitude, not exact match due to different weather years and data resolution).

## Scoring sanity tests

- Perfect system (0% unmet, 100% renewable, zero NPC ideal): composite score = 1.0
- Empty system (100% unmet, 0% renewable): composite score = 0.0

## Stop rules

1. If optimized design fails to beat diesel-only NPC at any site: report and do not claim cost savings.
2. If unmet load exceeds 1% for optimized design at any site: report as reliability failure.
3. Historical 12 GB memory abort proposal is not implemented; no measured-memory claim.
4. If NASA POWER fetch fails for any site-year: stop and report missing data.

## Reproduction command

```bash
pip install -c constraints.txt hatchling editables build
pip install --no-build-isolation -c constraints.txt -e ".[dev]"
northern-microgrid run --root .
```

## Exclusions

- No structural, electrical code or roadworthiness analysis
- No client data or proprietary load profiles
- No HOMER Pro comparison (licence barrier; SAMA cited as open alternative)
