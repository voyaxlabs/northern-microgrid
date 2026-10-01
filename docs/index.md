# northern-microgrid documentation

Open-source sizing for off-grid PV, wind, battery and diesel systems at Canadian northern and remote sites.

## Quick start

```bash
git clone https://github.com/voyaxlabs/northern-microgrid.git
cd northern-microgrid
python -m venv .venv && source .venv/bin/activate
pip install -c constraints.txt hatchling editables build
pip install --no-build-isolation -c constraints.txt -e ".[dev]"
northern-microgrid run --root .
```

## Concepts

- **Sites:** Iqaluit, Inuvik, Whitehorse, Dease Lake
- **Weather:** NASA POWER hourly data, cached as parquet (CC BY 4.0)
- **Load archetypes:** synthetic remote residential, camp, and research-station scenarios
- **Dispatch:** PV, wind, battery, diesel priority stack with energy ledger
- **Sizing:** grid search minimizing NPC with reliability constraint

## API

```python
from northern_microgrid.sites import get_site
from northern_microgrid.load_profiles import generate_hourly_load
from northern_microgrid.weather import load_weather_year
from northern_microgrid.sizing import optimize_design

site = get_site("iqaluit")
load = generate_hourly_load("remote_camp", utc_offset_hours=site.utc_offset_hours)
weather = load_weather_year(path_to_parquet)
result = optimize_design(load, weather, peak_kw=float(load.max()))
```

## Results

See [RESULTS.md](../RESULTS.md) and [technical report](technical-report.md).

## Licence

Apache-2.0 (code). Written documentation and generated outputs CC BY 4.0; see [definitive scope](LICENSING.md). Weather caches: CC BY 4.0 (NASA POWER).
