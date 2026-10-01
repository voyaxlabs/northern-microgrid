"""Tests for CLI."""

from pathlib import Path

from click.testing import CliRunner

from northern_microgrid.cli import main


def test_list_sites() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["list-sites"])
    assert result.exit_code == 0
    assert "iqaluit" in result.output


def test_validate_scorers() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["validate-scorers"])
    assert result.exit_code == 0


def test_hash_file(tmp_path: Path) -> None:
    f = tmp_path / "test.txt"
    f.write_text("hello", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(main, ["hash-file", str(f)])
    assert result.exit_code == 0
    assert len(result.output.strip()) == 64
