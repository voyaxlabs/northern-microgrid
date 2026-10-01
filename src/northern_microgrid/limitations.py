"""Shared, explicit scope statement for generated summaries."""

LIMITATIONS = [
    "Simulation-only: grid-optimal within the searched capacities, fixed dispatch and "
    "fixed diesel sizing; no field calibration or external validation.",
    "PV uses a fixed GHI tilt factor and ambient rather than cell temperature; azimuth is "
    "ignored. 10 m wind is used without adjustment to the configured 30 m hub height.",
    "Snow loss is uncalibrated and capped at 5% in the default scenario. Battery efficiency "
    "uses ambient temperature without heating loads, thermal dynamics, cold charging "
    "restrictions or capacity degradation.",
    "Economics repeat one year's fuel and O&M for 25 discounted years; replacement, "
    "fuel escalation, salvage and component degradation are omitted. All cost, load and "
    "coefficient values are stipulated scenario assumptions, not extracted quotes.",
    "Bootstrap intervals estimate the five-year mean of fixed-design annual outcomes "
    "(1000 resamples, seed 42), not a future-year prediction interval or lifecycle-cost "
    "uncertainty. The optimization year is reused; consecutive-year independence and "
    "interval coverage are unchecked. Cost/load/model uncertainty and climate trends are excluded.",
    "Diesel is sized at 110% of realized peak with unlimited fuel and no outages. Low unmet "
    "load is not redundancy, electrical stability, black-start or contingency evidence.",
    "The 80%-of-optimized baseline depends on the proposed design; it is not an "
    "independently selected competitor. Loads are synthetic, with fixed UTC offsets and no DST.",
    "Each year starts at midpoint SOC of unknown source and ends unconstrained. "
    "Stored sources are proportionally mixed. Initial "
    "energy is not credited as renewable; initial/terminal SOC and unknown-source delivery "
    "are quantified below. No warm-up or cyclic-year condition is imposed.",
    "NASA POWER resolution is 0.5 x 0.625 degrees for meteorology and 1 x 1 degree for solar; "
    "site microclimate and long-term climate changes are not modelled.",
]
