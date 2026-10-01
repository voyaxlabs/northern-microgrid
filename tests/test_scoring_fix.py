"""Tests for composite scoring cost monotonicity (finding 12)."""

from northern_microgrid.evaluation import composite_score


def test_expensive_design_scores_lower() -> None:
    reference = 1_000_000.0
    cheap = composite_score(0.0, 0.5, 800_000.0, reference)
    expensive = composite_score(0.0, 0.5, 2_000_000.0, reference)
    assert expensive < cheap


def test_diesel_heavy_counterexample_not_perfect() -> None:
    reference = 1_000_000.0
    score = composite_score(0.0, 0.3, 1_900_000.0, reference)
    assert score < 1.0
