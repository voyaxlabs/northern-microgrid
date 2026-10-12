# Licence scope and attribution

Copyright 2026 VoyaX Labs. This path-based grant is definitive; package metadata describes the code licence.

| Paths | Licence and attribution |
|---|---|
| `src/`, `tests/`, `scripts/`, build/CI configuration, dependency files | [Apache-2.0](../LICENSE), VoyaX Labs |
| `README.md`, `RESULTS.md`, `REPORT.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CITATION.cff`, `docs/` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), VoyaX Labs and credited author |
| `results/` (JSON, HTML, PNG) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), VoyaX Labs; NASA POWER is the weather source used to derive the figures/results |
| `data/weather/` (Parquet and metadata) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), NASA POWER Project; our metadata and column renaming are changes, described in [DATA_MANIFEST.md](DATA_MANIFEST.md) |

The author is credited by name in the citation file and the technical report.

The NASA [registry entry](https://registry.opendata.aws/nasa-power/) declares CC BY 4.0. Weather redistribution includes attribution, licence and changes; no endorsement is implied. Literature facts are cited with source links in RESULTS; no paper PDFs, article figures, restricted monitored loads, client records or third-party source code are shipped. Costs, analytic loads and efficiency coefficients are original stipulated scenario assumptions. NREL ATB and northern papers provide context, not a documented numerical extraction or currency conversion.

Release archives are built from the Git repository only. See scripts/audit_release.py.
