"""Tests for site registry."""

import pytest

from northern_microgrid.sites import CANADIAN_SITES, get_site


def test_four_sites() -> None:
    assert len(CANADIAN_SITES) == 4


def test_get_site_iqaluit() -> None:
    site = get_site("iqaluit")
    assert site.name == "Iqaluit"
    assert site.province_territory == "Nunavut"


def test_get_site_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown site"):
        get_site("toronto")
