# Results

Simulation-only scenario results from `results/evaluation_results.json`. Grid-optimal under the recorded search, dispatch and fixed diesel sizing; no external validation.

```bash
pip install -c constraints.txt hatchling editables build
pip install --no-build-isolation -c constraints.txt -e ".[dev]"
northern-microgrid run --root .
```

**Preserved protocol SHA-256:** `7bdd8d637841c2e15c80053c29ebe067995ecb77143c81036e3190b71f5dfc99` (chronology unverified)
**Pipeline runtime (this run):** 677.7 s

## Configuration

- Synthetic load archetype: `remote_camp`
- Weather years: 2018, 2019, 2020, 2021, 2022
- Optimization year: 2018; evaluation reuses this year.
- Renewable delivery includes direct PV/wind and renewable-source battery discharge.
- Costs, loads and coefficients are stipulated assumptions, not downloaded measurements.
- Input/code/dependency hashes and search configuration: [run metadata](results/evaluation_results.json); [protocol deviations](docs/PROTOCOL_DEVIATIONS.md).

## Headline results (2018 weather)

| Site | PV kW | Battery kWh | Renewable delivered % | Gross gen % | Diesel L/yr | NPC CAD | vs diesel-only |
|---|---:|---:|---:|---:|---:|---:|---|
| Iqaluit | 140 | 250 | 43.9 | 63.3 | 34087 | 1473915 | 11.0% lower |
| Inuvik | 140 | 225 | 44.0 | 62.2 | 33631 | 1447921 | 12.6% lower |
| Whitehorse | 140 | 225 | 50.3 | 71.1 | 30481 | 1363357 | 17.7% lower |
| Dease Lake | 150 | 250 | 53.4 | 80.6 | 28739 | 1352328 | 18.4% lower |

Reliability constraint <= 1.000%: met; maximum unmet across all evaluated site-years: 0.000%.

## Load and baseline statistics

| Site | Annual kWh | Mean daily kWh | Realized peak kW | Diesel-only NPC CAD |
|---|---:|---:|---:|---:|
| Iqaluit | 175200 | 480.0 | 43.44 | 1656481 |
| Inuvik | 175200 | 480.0 | 43.44 | 1656481 |
| Whitehorse | 175200 | 480.0 | 43.44 | 1656481 |
| Dease Lake | 175200 | 480.0 | 43.44 | 1656481 |

## NPC bootstrap intervals (95%, mean of 5 evaluated weather years)

| Site | Mean CAD | Lower CAD | Upper CAD | Width % | Years |
|---|---:|---:|---:|---:|---:|
| Iqaluit | 1443628 | 1431707 | 1459539 | 1.93 | 5 |
| Inuvik | 1447634 | 1439400 | 1455803 | 1.13 | 5 |
| Whitehorse | 1374525 | 1362389 | 1386200 | 1.73 | 5 |
| Dease Lake | 1358653 | 1352456 | 1368484 | 1.18 | 5 |

## Hypothesis outcomes

- H1 (>=15% NPC savings and <1% unmet in every evaluated year): met at 2 of 4 evaluated sites: Whitehorse, Dease Lake.
  Savings by site: Iqaluit: 11.0%; Inuvik: 12.6%; Whitehorse: 17.7%; Dease Lake: 18.4%.
- H2 (>10% NPC CI width at evaluated Arctic sites): not met; Iqaluit: 1.93%; Inuvik: 1.13%.
- H3: untested; no matched measured load/weather validation experiment.

Selected wind: Iqaluit: 0.0 kW; Inuvik: 0.0 kW; Whitehorse: 0.0 kW; Dease Lake: 0.0 kW.

## Storage boundary ledger

Every year starts with unknown-source energy at midpoint SOC. Conversion loss = charge - discharge - (terminal - initial SOC); boundary energy is not free renewable.

| Site/year | Initial kWh | Terminal kWh | Unknown initial to load kWh | Loss kWh |
|---|---:|---:|---:|---:|
| Iqaluit/2018 | 137.50 | 37.50 | 94.53 | 13009.29 |
| Iqaluit/2019 | 137.50 | 37.50 | 96.80 | 12412.34 |
| Iqaluit/2020 | 137.50 | 37.50 | 95.67 | 13289.18 |
| Iqaluit/2021 | 137.50 | 37.50 | 97.77 | 13705.36 |
| Iqaluit/2022 | 137.50 | 37.50 | 98.90 | 13371.00 |
| Inuvik/2018 | 123.75 | 33.75 | 90.57 | 8188.06 |
| Inuvik/2019 | 123.75 | 33.75 | 96.80 | 6817.63 |
| Inuvik/2020 | 123.75 | 33.75 | 87.84 | 7381.53 |
| Inuvik/2021 | 123.75 | 33.75 | 86.82 | 7730.56 |
| Inuvik/2022 | 123.75 | 33.75 | 85.13 | 8169.84 |
| Whitehorse/2018 | 123.75 | 33.75 | 90.29 | 9218.56 |
| Whitehorse/2019 | 123.75 | 33.75 | 97.29 | 8698.44 |
| Whitehorse/2020 | 123.75 | 33.75 | 97.26 | 9036.10 |
| Whitehorse/2021 | 123.75 | 33.75 | 93.90 | 8597.58 |
| Whitehorse/2022 | 123.75 | 33.75 | 94.65 | 8765.87 |
| Dease Lake/2018 | 137.50 | 37.50 | 97.72 | 11250.80 |
| Dease Lake/2019 | 137.50 | 37.50 | 108.55 | 10771.52 |
| Dease Lake/2020 | 137.50 | 37.50 | 109.52 | 11650.26 |
| Dease Lake/2021 | 137.50 | 37.50 | 105.40 | 10421.79 |
| Dease Lake/2022 | 137.50 | 37.50 | 105.34 | 10980.89 |

## Fixed-design sensitivity (optimization year)

One assumption changes at a time; capacities are not re-optimized. Fuel +/-25%; all component CAPEX +25%; battery replacement year 12 and diesel year 15; snow cap 20%; ideal battery efficiency with no temperature penalty and no heating energy. These are stipulated stresses, not confidence bounds.

| Site | Stress | NPC CAD | Savings vs equally stressed diesel % |
|---|---|---:|---:|
| Iqaluit | base | 1473915 | 11.02 |
| Iqaluit | fuel_low | 1245146 | 2.01 |
| Iqaluit | fuel_high | 1702683 | 16.63 |
| Iqaluit | capex_high | 1594846 | 4.27 |
| Iqaluit | replacements | 1558198 | 6.83 |
| Iqaluit | snow_high | 1475012 | 10.96 |
| Iqaluit | battery_no_temp_penalty | 1424550 | 14.00 |
| Inuvik | base | 1447921 | 12.59 |
| Inuvik | fuel_low | 1222213 | 3.82 |
| Inuvik | fuel_high | 1673628 | 18.05 |
| Inuvik | capex_high | 1565415 | 6.04 |
| Inuvik | replacements | 1525371 | 8.79 |
| Inuvik | snow_high | 1448689 | 12.54 |
| Inuvik | battery_no_temp_penalty | 1414192 | 14.63 |
| Whitehorse | base | 1363357 | 17.70 |
| Whitehorse | fuel_low | 1158791 | 8.81 |
| Whitehorse | fuel_high | 1567924 | 23.23 |
| Whitehorse | capex_high | 1480851 | 11.12 |
| Whitehorse | replacements | 1440807 | 13.85 |
| Whitehorse | snow_high | 1365167 | 17.59 |
| Whitehorse | battery_no_temp_penalty | 1327885 | 19.84 |
| Dease Lake | base | 1352328 | 18.36 |
| Dease Lake | fuel_low | 1159456 | 8.75 |
| Dease Lake | fuel_high | 1545200 | 24.34 |
| Dease Lake | capex_high | 1478759 | 11.24 |
| Dease Lake | replacements | 1436612 | 14.10 |
| Dease Lake | snow_high | 1354375 | 18.24 |
| Dease Lake | battery_no_temp_penalty | 1308721 | 20.99 |

## Literature context (sourced, not computed or validation)

[Colville Lake poster](https://microgrid-symposiums.org/wp-content/uploads/2019/08/03_DaveTURCOTTE.pdf): about 17% annual PV contribution and over 31,000 L diesel savings. [KLRS paper](https://web.stanford.edu/group/efmh/jacobson/Articles/Others/23-YukonMicrogrid.pdf): 67% annual PV-plus-storage contribution, 48 kW PV, about 27 kW battery power. Different sites/loads; these facts do not validate this scenario.

## Runtime (seconds, this run)

| Step | Iqaluit | Inuvik | Whitehorse | Dease Lake |
|---|---:|---:|---:|---:|
| Cached weather check | 0.1 | 0.1 | 0.1 | 0.1 |
| Optimization | 167.1 | 167.8 | 169.2 | 168.7 |
| Site total | 168.4 | 169.0 | 170.4 | 169.9 |

## Limitations

- Simulation-only: grid-optimal within the searched capacities, fixed dispatch and fixed diesel sizing; no field calibration or external validation.
- PV uses a fixed GHI tilt factor and ambient rather than cell temperature; azimuth is ignored. 10 m wind is used without adjustment to the configured 30 m hub height.
- Snow loss is uncalibrated and capped at 5% in the default scenario. Battery efficiency uses ambient temperature without heating loads, thermal dynamics, cold charging restrictions or capacity degradation.
- Economics repeat one year's fuel and O&M for 25 discounted years; replacement, fuel escalation, salvage and component degradation are omitted. All cost, load and coefficient values are stipulated scenario assumptions, not extracted quotes.
- Bootstrap intervals estimate the five-year mean of fixed-design annual outcomes (1000 resamples, seed 42), not a future-year prediction interval or lifecycle-cost uncertainty. The optimization year is reused; consecutive-year independence and interval coverage are unchecked. Cost/load/model uncertainty and climate trends are excluded.
- Diesel is sized at 110% of realized peak with unlimited fuel and no outages. Low unmet load is not redundancy, electrical stability, black-start or contingency evidence.
- The 80%-of-optimized baseline depends on the proposed design; it is not an independently selected competitor. Loads are synthetic, with fixed UTC offsets and no DST.
- Each year starts at midpoint SOC of unknown source and ends unconstrained. Stored sources are proportionally mixed. Initial energy is not credited as renewable; initial/terminal SOC and unknown-source delivery are quantified below. No warm-up or cyclic-year condition is imposed.
- NASA POWER resolution is 0.5 x 0.625 degrees for meteorology and 1 x 1 degree for solar; site microclimate and long-term climate changes are not modelled.

## Reports and licence

HTML reports: [Iqaluit](results/report_iqaluit.html), [Inuvik](results/report_inuvik.html), [Whitehorse](results/report_whitehorse.html), [Dease Lake](results/report_dease_lake.html).
Figures: `results/figures/`. [Licence scope](docs/LICENSING.md): CC BY 4.0 for this document and outputs; code Apache-2.0.
