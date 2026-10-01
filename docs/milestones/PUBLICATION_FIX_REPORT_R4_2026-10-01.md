# Publication fix, round 4: 2026-10-01

This writer's report addresses only blocker 13 of the local convergent re-review of `a942ecb`. Findings 1-11 and the round-three scientific assumptions remain unchanged. The independent review stays local and excluded from publication. This report is verification evidence, not independent publication approval.

## Acquisition and validation

`pipeline.py` now identifies absent site-years explicitly requested by the run. The initial inventory check defers only those paths when acquisition is enabled, while still rejecting every present-but-modified manifest file before fetching. The real NASA year fetcher then acquires missing files. A second, strict inventory check requires every listed file to exist and match its original SHA-256 and raw row count. All requested weather is loaded and checked for physical values, complete ordered UTC calendars and site/year/coordinate metadata before any optimization or simulation, including non-optimization years.

`--no-fetch` permits no missing-path deferral or acquisition. Missing inventory outside the requested sites is also rejected. Neither the manifest nor the weather fetcher was changed. Downloads with changed upstream values or different serialized bytes fail closed; acquisition does not silently create a new publication input. `docs/DATA_MANIFEST.md` states this policy beside the existing acquisition command.

## Regression evidence

`tests/test_publication_r4.py` exercises the public CLI with the exact arguments `run --root .` and one absent manifest-listed cache, Iqaluit 2018. A fake NASA chunk source supplies the original weather; the real year fetcher assembles all 13 chunks, writes Parquet and metadata, and restores the original bytes/hash. The pipeline completes all four sites and five years with a small test grid. Network access is not used.

The same success regression on an isolated archive of `a942ecb` fails with `FileNotFoundError` before acquisition: [before receipt](../../state/r4-evidence/before.txt). Additional CLI regressions reject modified inventory before fetching, missing caches under `--no-fetch`, missing unrequested inventory, and acquired non-optimization-year caches with wrong hashes, row counts, calendars, weather values, site IDs, coordinates or years. Rejection tests assert that optimization never starts.

## Final verification

Full isolated-environment suites pass on Python 3.11 and 3.12: **99 passed** on each, with **93.7455%** combined statement and branch coverage (1099/1151 statements; 205/240 branches). Source and input content in the suite checkout match the clean regeneration checkout. Scientific outputs used for the suites remain the round-three values with the acquisition-only source receipt updated; final regeneration comparison below verifies those values again. [3.11 suite](../../state/r4-evidence/tests311.txt), [3.12 suite](../../state/r4-evidence/tests312.txt), [coverage totals](../../state/r4-evidence/coverage311.json).

Ruff with caches disabled, Mypy with a fresh cache, configured Pyright, both dependency checks, scorer validation and sdist/wheel builds pass: [quality receipt](../../state/r4-evidence/checks.txt). The existing configured Pyright exception is unchanged. Fresh environments use the pinned constraints and the existing round-three locally reconstructed wheelhouse without network downloads. This verifies isolated constrained installation, not new upstream artifact authenticity: [3.11 install](../../state/r4-evidence/install311.txt), [3.12 install](../../state/r4-evidence/install312.txt).

The exact default **`northern-microgrid run --root .`** passes from an initially clean Git checkout, revision `c5debcdad9ed73295af140a43cfedae145c15aa7`. It uses all four sites, five weather years and the full default grid: **19,404 evaluations**, with no optimizer mock, selected-site shortcut or weather retrieval needed. Pipeline runtime is **682.384 seconds**; total command wall time, including font-cache initialization, is **700.659 seconds**. [Command receipt](../../state/r4-evidence/regeneration.txt), [comparison receipt](../../state/r4-evidence/regeneration.json).

All **975 experiment scalars, including 949 numeric values, match round three exactly**. The eight PNGs and four HTML reports are byte-identical; RESULTS changes only its runtime headline/table. Input, protocol and configuration hashes are unchanged. The acquisition-only source edit necessarily changes the code-content hash: the comparison independently calculates and verifies that new hash, then uses the unchanged committed comparator with only the expected old code-hash receipt replaced. Timing, revision and environment exclusions are unchanged; tolerances remain rtol=1e-9 and atol=1e-6. Generated JSON and RESULTS are refreshed solely to bind the executed source and run.

## Publication delivery

Staging in the original checkout is blocked by the sandbox's inability to create `.git/index.lock`: [blocking receipt](../../state/r4-evidence/commit-block.txt). The original index, branches and development history are preserved. The fallback is **`state/r4.bundle`**, with **`main` and `publication-r4` pointing to the same clean publication tip**, extending only the clean round-three publication ancestry. Author and committer use **Amirhossein (Amir) Daneshpajouh <52765136+Daneshpajouh@users.noreply.github.com>**, without attribution trailers.

The publication history, tracked payload, Git release archive, built sdist and wheel receive the unchanged bounded path/attribution/punctuation/key/token scan, including decoded PNG/Parquet metadata and weather string columns: [release receipt](../../state/r4-evidence/release.txt). The final bundle is verified by cloning it into a fresh clean checkout, comparing the complete payload/tree, checking commit identities and rescanning its final history/archive. The ignored sibling `state/r4.bundle.sha256` records the final commit, checksum and clone/scan result. This is a bounded scan, not a new dedicated secret-scanner run or a proof of absence.

No push was performed. Local reviews and bundle files are excluded from the committed publication payload.
