# Data manifest

This file records every external dataset used or redistributed by northern-microgrid.

## Shipped weather caches

| Item | Value |
|---|---|
| Source | [NASA POWER](https://power.larc.nasa.gov/) hourly API |
| Licence | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Registry | [AWS Open Data](https://registry.opendata.aws/nasa-power/) |
| Weather coverage | 2018-2022, four sites, UTC timestamps |
| Acquisition timestamps / dataset release | Not retained; unavailable, not inferred from weather years |
| Parameters | ALLSKY_SFC_SW_DWN, T2M, WS10M, PRECTOTCORR, ALLSKY_SFC_PAR_TOT |
| Transformations | Shipped: JSON to Parquet and renamed columns, complete raw UTC calendars. Simulation-time only: remove Feb 29, then 8760 hours; no padding or sorting on load |
| Units | GHI and PAR in Wh/m2 per hour; temperature in C; wind at 10 m in m/s; precip in mm/hr |
| Location | `data/weather/<site_id>/<year>.parquet` |
| Rows per file | 8760; 2020 files retain 8784 including February 29 |

### Site coordinates

| Site ID | Latitude | Longitude | UTC offset (load alignment) |
|---|---:|---:|---|
| iqaluit | 63.75 | -68.52 | -5 |
| inuvik | 68.36 | -133.72 | -7 |
| whitehorse | 60.72 | -135.05 | -7 |
| dease_lake | 58.44 | -130.03 | -7 |

## Cited but not redistributed

| Source | Licence | Use in repository |
|---|---|---|
| NRCan solar resource maps | Open Government Licence - Canada | Bibliography only |
| ECCC climate normals | Government of Canada open data | M0 reference only |
| Northern load literature | Citation context only | No measured profiles or extracted coefficients |
| KLRS paper (Energy Nexus 2023) | CC BY-NC-ND | Literature metrics only; no article data shipped |
| NREL ATB 2024 | CC BY 4.0 | Context only; numeric constants are stipulated, with no extraction/FX/premium evidence |

## Synthetic load profiles

Load archetypes in `src/northern_microgrid/load_profiles.py` are original analytic hourly shapes with stipulated energy/peak targets. They are not measured profiles from government databases.

## Licence boundary

See the definitive [path-based grant](LICENSING.md). Code Apache-2.0; documentation/outputs CC BY 4.0; weather CC BY 4.0 with NASA POWER credit.

## Regenerating caches

```bash
northern-microgrid run --root .  # fetches missing years from NASA POWER
```

Use `--no-fetch` to require existing caches only.

The run first rejects present caches that differ from the inventory, then acquires
only missing site-years requested by the run. Before simulation, the complete
inventory and requested caches must pass the recorded SHA-256/raw-row policy,
weather-value, ordered-calendar and site/year/coordinate checks. Downloads do not
update or bypass the shipped manifest: changed upstream data or different Parquet
bytes are rejected. `--no-fetch` never acquires a missing file.

## Machine-checkable inventory

[data/weather/manifest.json](../data/weather/manifest.json) records each of the 20 files, actual raw rows, SHA-256, coordinates, weather year, unavailable acquisition/release fields, and API request parameters (community RE, time-standard UTC). The pipeline validates hashes and complete ordered hourly calendars before simulation. Known acquisition dates for future downloads are recorded in per-cache metadata sidecars; original retrieval history cannot be recovered from the cache values.

| File | Raw rows | SHA-256 |
|---|---:|---|
| `data/weather/dease_lake/2018.parquet` | 8760 | `ef65ea45f6294a5307204aa021cb28136bddbb2ba4fc826b397443de9538d129` |
| `data/weather/dease_lake/2019.parquet` | 8760 | `568d73f10082760c65809dce3860c263ea66a2e81c6532a732ba024706a89774` |
| `data/weather/dease_lake/2020.parquet` | 8784 | `2dbadf9b9171694fb6dbdd10fbfcbf267cd8d44b327657e44ad71018ae7bfda3` |
| `data/weather/dease_lake/2021.parquet` | 8760 | `5898031cbfe84da1ae4ca34a440ff6c443147d25e0f637facca9431bc1952c2d` |
| `data/weather/dease_lake/2022.parquet` | 8760 | `cdc3cf75184388cb2c56bfcf29bf09528ecf016735c22138f6f9ee5476421786` |
| `data/weather/inuvik/2018.parquet` | 8760 | `4a00f17276c2cb5d3f513a271984d3586d1ac00319abacbfe8fe142ae1bdfc0b` |
| `data/weather/inuvik/2019.parquet` | 8760 | `cf570c13a968dc0b14931f21c3f0ac400b2fa7e0935de112bff42f357b0cc1ef` |
| `data/weather/inuvik/2020.parquet` | 8784 | `fa49daeeba7893653b11f9120941dc39a3679d584d83200c5be1d7db9f9c0339` |
| `data/weather/inuvik/2021.parquet` | 8760 | `e8d67b707baaffd533410f84fb53a5b1214b0751caf7794585c7938ca487090e` |
| `data/weather/inuvik/2022.parquet` | 8760 | `8f0ea931f9c302b4fc3c320a131221c8cf0b6dfd13966f5ad2d191f7373aebee` |
| `data/weather/iqaluit/2018.parquet` | 8760 | `b5c307e11342016a983a10378b1b07aeb754c724d46ec8ce4d6ee9a88478c31a` |
| `data/weather/iqaluit/2019.parquet` | 8760 | `410c5306cd94eee8d3d972e2280a84db643d7b3d0dc48218211a22e0ba448252` |
| `data/weather/iqaluit/2020.parquet` | 8784 | `ece0b94347b9c3dbb0ea72fd74284bdafb345849a936467bc913625c26fa2237` |
| `data/weather/iqaluit/2021.parquet` | 8760 | `ec724cc8b8cad55dcf2a667d2ddac09097f3de17102db735d23a27f990c1184e` |
| `data/weather/iqaluit/2022.parquet` | 8760 | `f6522c6695980bce4dcdb30a10c6d858d006d7208853fb8d9d1c0d6c0fc3dc1b` |
| `data/weather/whitehorse/2018.parquet` | 8760 | `72171770b5a96bdb3ebaf5119b5a2828fc68fdcd0003e45d02ac3828f191c973` |
| `data/weather/whitehorse/2019.parquet` | 8760 | `b37110f3deef591c46f5088881242c45aff366c3d222f1be4c6b3ab05590a409` |
| `data/weather/whitehorse/2020.parquet` | 8784 | `74eebc3ab9f41ff48f08ce013efeddc204d9a81322c2f789991d236dafaf9877` |
| `data/weather/whitehorse/2021.parquet` | 8760 | `9de3a61d518fb68cd233e0deb58bb6bead939d816de53b688add4ec4b675f4dc` |
| `data/weather/whitehorse/2022.parquet` | 8760 | `e02f69406bd29d101b7fcab6289538a62f8afc80db9986366a60784cef92b34e` |
