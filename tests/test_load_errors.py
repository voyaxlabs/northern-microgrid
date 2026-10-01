"""Error path tests."""

import pytest

from northern_microgrid.load_profiles import generate_hourly_load


def test_unknown_archetype() -> None:
    with pytest.raises(ValueError, match="Unknown archetype"):
        generate_hourly_load("invalid")  # type: ignore[arg-type]
