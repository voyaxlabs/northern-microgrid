"""Command-line interface for northern-microgrid."""

from __future__ import annotations

import hashlib
from pathlib import Path

import click

from northern_microgrid.pipeline import run_pipeline
from northern_microgrid.sites import CANADIAN_SITES


@click.group()
@click.version_option()
def main() -> None:
    """Size off-grid PV, wind, battery and diesel systems for Canadian northern sites."""


@main.command()
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("."),
    help="Project root directory",
)
@click.option(
    "--site",
    multiple=True,
    help="Site ID (default: all four case-study sites)",
)
@click.option(
    "--archetype",
    type=click.Choice(["remote_residential", "remote_camp", "research_station"]),
    default="remote_camp",
)
@click.option("--no-fetch", is_flag=True, help="Skip weather fetch (use cached data)")
def run(
    root: Path,
    site: tuple[str, ...],
    archetype: str,
    no_fetch: bool,
) -> None:
    """Run the full evaluation pipeline."""
    site_ids = list(site) if site else None
    results = run_pipeline(
        root.resolve(),
        site_ids=site_ids,
        archetype=archetype,  # type: ignore[arg-type]
        fetch_weather=not no_fetch,
    )
    from northern_microgrid.results_doc import write_results_markdown

    results_md = write_results_markdown(root.resolve())
    click.echo(f"Pipeline complete. Results: {root / 'results' / 'evaluation_results.json'}")
    click.echo(f"Results summary: {results_md}")
    click.echo(f"Sites evaluated: {', '.join(results['sites'].keys())}")


@main.command("list-sites")
def list_sites() -> None:
    """List available case-study sites."""
    for sid, loc in CANADIAN_SITES.items():
        click.echo(
            f"  {sid}: {loc.name}, {loc.province_territory} "
            f"({loc.latitude}, {loc.longitude})"
        )


@main.command()
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def hash_file(file: Path) -> None:
    """Compute SHA-256 hash of a file (for preregistration)."""
    digest = hashlib.sha256(file.read_bytes()).hexdigest()
    click.echo(digest)


@main.command("generate-results-md")
@click.option(
    "--root",
    type=click.Path(path_type=Path),
    default=Path("."),
    help="Project root directory",
)
def generate_results_md(root: Path) -> None:
    """Regenerate RESULTS.md from evaluation_results.json."""
    from northern_microgrid.results_doc import write_results_markdown

    out = write_results_markdown(root.resolve())
    click.echo(f"Wrote {out}")


@main.command("validate-scorers")
def validate_scorers() -> None:
    """Verify scorer sanity checks (perfect=1.0, empty=0.0)."""
    from northern_microgrid.evaluation import score_empty_system, score_perfect_system

    perfect = score_perfect_system()
    empty = score_empty_system()
    if perfect != 1.0:
        raise click.ClickException(f"Perfect scorer returned {perfect}, expected 1.0")
    if empty != 0.0:
        raise click.ClickException(f"Empty scorer returned {empty}, expected 0.0")
    click.echo("Scorer validation passed: perfect=1.0, empty=0.0")


if __name__ == "__main__":
    main()
