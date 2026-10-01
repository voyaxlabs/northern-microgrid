# northern-microgrid

Which PV/battery capacities reduce diesel use and stipulated costs for a synthetic remote camp? This company-owned computational demonstration compares four Canadian northern weather scenarios with hourly dispatch and a bounded capacity grid. It is simulation-only: no client project, measured-site validation, professional engineering approval or deployment is established.

## Case-study contribution

The contribution is the reproducible four-site scenario bundle, source-tracked storage ledger, fixed-design sensitivity checks and JSON/Markdown/HTML figures. There is no new optimization algorithm or categorical absence claim. [Prior-art revision and feature map](docs/PRIOR_ART.md) acknowledges SAMA's CLI/GUI, SAMBA's LP/MILP workflow and MicroGridsPy's NASA POWER/stochastic/multi-year features.

## Reproduce

Python 3.11 and 3.12 are the tested targets. The shared constraints use version markers where their tested numerical stacks differ. Install the pinned build backend first so isolated builds do not fetch an unconstrained backend.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -c constraints.txt hatchling editables build
pip install --no-build-isolation -c constraints.txt -e ".[dev]"
northern-microgrid run --root .
```

The one-command run checks the input manifest, searches all four sites, evaluates 2018-2022, computes sensitivity stresses, and regenerates JSON, RESULTS.md, four HTML reports and eight figures. `--no-fetch` uses shipped caches only. Full regeneration is also compared in CI; timing/revision/environment receipts are excluded, scientific values and input/code/config hashes use relative tolerance 1e-9 and absolute tolerance 1e-6.

## Scenario evidence

[Current results](RESULTS.md) are generated from code. Under the default fixed economics H1 (at least 15% NPC savings plus reliability) is met at two of four sites, H2 (Arctic NPC interval width above 10%) is not met, and H3 (external validation) is untested. Costs and load shapes are stipulated assumptions, not public-source numerical extractions or procurement quotes. [Protocol departures](docs/PROTOCOL_DEVIATIONS.md) identify unverified chronology and deferred checks. Peak memory is not measured.

| Site | Weather context | Sample report |
|---|---|---|
| Iqaluit | Nunavut | [HTML](results/report_iqaluit.html) |
| Inuvik | Northwest Territories | [HTML](results/report_inuvik.html) |
| Whitehorse | Yukon | [HTML](results/report_whitehorse.html) |
| Dease Lake | Northern BC | [HTML](results/report_dease_lake.html) |

## Limits beside the headline

- Simulation-only: grid-optimal within the searched capacities, fixed dispatch and fixed diesel sizing; no field calibration or external validation.
- PV uses a fixed GHI tilt factor and ambient rather than cell temperature; azimuth is ignored. 10 m wind is used without adjustment to the configured 30 m hub height.
- Snow loss is uncalibrated and capped at 5% in the default scenario. Battery efficiency uses ambient temperature without heating loads, thermal dynamics, cold charging restrictions or capacity degradation.
- Economics repeat one year's fuel and O&M for 25 discounted years; replacement, fuel escalation, salvage and component degradation are omitted. All cost, load and coefficient values are stipulated scenario assumptions, not extracted quotes.
- Bootstrap intervals estimate the five-year mean of fixed-design annual outcomes (1000 resamples, seed 42), not a future-year prediction interval or lifecycle-cost uncertainty. The optimization year is reused; consecutive-year independence and interval coverage are unchecked. Cost/load/model uncertainty and climate trends are excluded.
- Diesel is sized at 110% of realized peak with unlimited fuel and no outages. Low unmet load is not redundancy, electrical stability, black-start or contingency evidence.
- The 80%-of-optimized baseline depends on the proposed design; it is not an independently selected competitor. Loads are synthetic, with fixed UTC offsets and no DST.
- Each year starts at midpoint SOC of unknown source and ends unconstrained. Initial energy is not credited as renewable; initial/terminal SOC and unknown-source delivery are quantified below. No warm-up or cyclic-year condition is imposed.
- NASA POWER resolution is 0.5 x 0.625 degrees for meteorology and 1 x 1 degree for solar; site microclimate and long-term climate changes are not modelled.

## Data, licences and documentation

NASA POWER hourly caches are the only shipped external dataset. [DATA_MANIFEST.md](docs/DATA_MANIFEST.md) describes exact rows, hashes, units, request coordinates, raw leap calendars and unavailable retrieval history. Loads, cost constants and coefficients are original synthetic scenario assumptions.

[Definitive licence scope](docs/LICENSING.md): Apache-2.0 code; CC BY 4.0 written documentation and generated outputs; CC BY 4.0 NASA POWER weather with attribution/change notices. [Technical report](docs/technical-report.md), [preserved evaluation protocol](docs/PREREGISTRATION.md), [round-three fix evidence](docs/milestones/PUBLICATION_FIX_REPORT_R3_2026-10-01.md), and [citation metadata](CITATION.cff) document the claim boundaries. Historical milestone claims are superseded. Release archives must contain the Git payload only, never a complete developer directory.
