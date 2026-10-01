# Licence scope and attribution

Copyright 2026 VoyaX Labs. This path-based grant is definitive; package metadata describes the code licence.

| Paths | Licence and attribution |
|---|---|
| `src/`, `tests/`, `scripts/`, build/CI configuration, dependency files | [Apache-2.0](../LICENSE), VoyaX Labs |
| `README.md`, `RESULTS.md`, `REPORT.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CITATION.cff`, `docs/` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), VoyaX Labs and credited author |
| `results/` (JSON, HTML, PNG), `state/r3-evidence/` verification receipts | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), VoyaX Labs; NASA POWER is the weather source used to derive the figures/results |
| `data/weather/` (Parquet and metadata) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), NASA POWER Project; our metadata and column renaming are changes, described in [DATA_MANIFEST.md](DATA_MANIFEST.md) |

Public author credit is intentionally retained in scientific metadata and the requested GitHub noreply commit identity. It is the intended exception to excluding private personal records. No company-only identity claim is made.

The NASA [registry entry](https://registry.opendata.aws/nasa-power/) declares CC BY 4.0. Weather redistribution includes attribution, licence and changes; no endorsement is implied. Literature facts are cited with source links in RESULTS; no paper PDFs, article figures, restricted monitored loads, client records or third-party source code are shipped. Costs, analytic loads and efficiency coefficients are original stipulated scenario assumptions. NREL ATB and northern papers provide context, not a documented numerical extraction or currency conversion.

Archives must be made from the explicit Git payload, excluding `.review/`, environments, caches, bytecode, coverage databases and local bundles. See `scripts/audit_release.py`. Original development history contains a withdrawn local path; only the separately prepared clean publication history is suitable for a no-paths-in-history release. No original history is rewritten.
