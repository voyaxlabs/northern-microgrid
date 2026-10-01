"""Tests for evaluation and scoring."""


from northern_microgrid.evaluation import (
    bootstrap_uncertainty,
    composite_score,
    reliability_score,
    score_empty_system,
    score_perfect_system,
)


def test_perfect_score() -> None:
    assert score_perfect_system() == 1.0


def test_empty_score() -> None:
    assert score_empty_system() == 0.0


def test_reliability_perfect() -> None:
    assert reliability_score(0.0) == 1.0


def test_reliability_zero() -> None:
    assert reliability_score(1.0) == 0.0


def test_composite_midrange() -> None:
    score = composite_score(0.05, 0.5, 500000.0, 1000000.0)
    assert 0.0 < score < 1.0


def test_bootstrap_single_value() -> None:
    band = bootstrap_uncertainty([42.0], "test")
    assert band.point_estimate == 42.0
    assert band.lower_95 == 42.0


def test_bootstrap_interval() -> None:
    values = [10.0, 12.0, 14.0, 16.0, 18.0]
    band = bootstrap_uncertainty(values, "diesel")
    assert band.lower_95 <= band.point_estimate <= band.upper_95
    assert band.n_samples == 5
