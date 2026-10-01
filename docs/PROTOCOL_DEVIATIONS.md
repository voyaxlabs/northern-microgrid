# Evaluation protocol departures, 2026-10-01

The preserved protocol is a benchmark specification, not independently timestamped preregistration. Its original text is kept in the Git baseline and the local review evidence. The current corrected protocol is content-hashed; a hash establishes integrity, not chronology.

| Item | Earlier statement | Current implementation and claim |
|---|---|---|
| Timing | Frozen before results | No earlier commitment/registration receipt; pre-result chronology unverified |
| Renewable metric | Gross PV/wind / served load | Direct renewable plus source-tracked battery delivery; gross separately reported |
| Battery boundary | Unspecified | Each year midpoint unknown-source SOC, terminal unconstrained; boundary ledger and initial contribution reported |
| Camp peak | 85 kW peak | 85 kW input cap; realized peak 43.44 kW; generator 110% of realized peak |
| Colville context | Wind/PV validation band | Poster describes PV; distinct measured site; no validation claim |
| H3 / secondary experiment | Research station literature validation | Deferred; supported archetype is not a matched measurement experiment; H3 untested |
| Cost provenance | Industry/public references | Stipulated CAD scenario constants; extraction/FX/premium unavailable |
| H1 | 15% cost reduction | Computed for evaluated remote_camp sites with reliability gate; two of four default sites meet it |
| H2 | Width >10% | Computed on evaluated Arctic sites only, mean-bootstrap widths; default hypothesis not met |
| Cost-saving stop | Do not claim savings where worse | Generator reports each site's positive/negative savings; no execution abort |
| Reliability stop | Report >1% as failure | Optimization filter and generated all-year maximum check; no execution abort |
| Memory stop | Abort above 12 GB | Not enforced, peak memory not measured; no memory-performance claim |
| Weather stop | Stop on missing data | No-fetch requires caches; downloads propagate errors; strict raw UTC calendar/hash validation |
| Composite score | Perfect minimum-NPC value 1 | Ideal zero-cost, fully renewable reliable endpoint 1; cost score reference/(reference+cost), equal cost 0.5 |
| Sensitivities | Secondary validation only | One-at-a-time fixed-design cost/replacement/snow/efficiency stresses, no re-optimization |

Source content hash, checkout revision, actual protocol digest, constraints, package versions, search grid and input cache hashes are written into `run_metadata`. The checkout revision alone may be the parent of uncommitted generated outputs; the source content digest identifies the executed code. Runtime/dependency metadata are receipts, not guaranteed performance or calibration.
