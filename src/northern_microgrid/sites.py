"""Canonical Canadian northern case-study locations."""

from northern_microgrid.types import SiteLocation

CANADIAN_SITES: dict[str, SiteLocation] = {
    "iqaluit": SiteLocation(
        name="Iqaluit",
        latitude=63.75,
        longitude=-68.52,
        province_territory="Nunavut",
        elevation_m=34.0,
        utc_offset_hours=-5,
    ),
    "inuvik": SiteLocation(
        name="Inuvik",
        latitude=68.36,
        longitude=-133.72,
        province_territory="Northwest Territories",
        elevation_m=15.0,
        utc_offset_hours=-7,
    ),
    "whitehorse": SiteLocation(
        name="Whitehorse",
        latitude=60.72,
        longitude=-135.05,
        province_territory="Yukon",
        elevation_m=703.0,
        utc_offset_hours=-7,
    ),
    "dease_lake": SiteLocation(
        name="Dease Lake",
        latitude=58.44,
        longitude=-130.03,
        province_territory="British Columbia",
        elevation_m=816.0,
        utc_offset_hours=-7,
    ),
}


def get_site(site_id: str) -> SiteLocation:
    """Return a site by canonical identifier."""
    key = site_id.lower().replace("-", "_").replace(" ", "_")
    if key not in CANADIAN_SITES:
        valid = ", ".join(sorted(CANADIAN_SITES))
        raise ValueError(f"Unknown site '{site_id}'. Valid sites: {valid}")
    return CANADIAN_SITES[key]
