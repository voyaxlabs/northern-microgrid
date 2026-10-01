"""Portable, content-bound input and run metadata."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

from northern_microgrid.sizing import SizingConstraints


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_data_manifest(root: Path, *, allow_missing: set[Path] | None = None) -> None:
    """Check shipped bytes/rows, optionally deferring explicitly requested absent files."""
    manifest_path = root / "data/weather/manifest.json"
    if not manifest_path.exists():
        return  # Library callers may supply their own, calendar-validated weather.
    import pandas as pd

    for record in json.loads(manifest_path.read_text())["files"]:
        path = root / record["path"]
        if not path.exists() and allow_missing is not None and path in allow_missing:
            continue
        if sha256(path) != record["sha256"] or len(pd.read_parquet(path)) != record["rows"]:
            raise ValueError(f"Data manifest mismatch: {record['path']}")


def run_metadata(
    root: Path, weather_paths: list[Path], constraints: SizingConstraints
) -> dict[str, Any]:
    """Bind actual content; a protocol hash does not prove pre-result timing."""
    protocol = root / "docs/PREREGISTRATION.md"
    protocol_hash = sha256(protocol) if protocol.exists() else None
    digest = root / "docs/PREREGISTRATION.sha256"
    if digest.exists() and digest.read_text().strip() != protocol_hash:
        raise ValueError("Protocol SHA-256 mismatch")
    code_files = sorted((root / "src").rglob("*.py"))
    code_hash = hashlib.sha256()
    for path in code_files:
        code_hash.update(str(path.relative_to(root)).encode())
        code_hash.update(path.read_bytes())
    revision = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    )
    deps = [
        "numpy",
        "pandas",
        "pyarrow",
        "requests",
        "scipy",
        "matplotlib",
        "jinja2",
        "pyyaml",
        "click",
    ]
    return {
        "source_revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "source_revision_scope": "checkout HEAD; code_sha256 binds executed source content",
        "code_sha256": code_hash.hexdigest(),
        "protocol_sha256": protocol_hash,
        "constraints_sha256": sha256(root / "constraints.txt")
        if (root / "constraints.txt").exists()
        else None,
        "cache_sha256": {str(p.relative_to(root)): sha256(p) for p in weather_paths},
        "dependencies": {name: importlib.metadata.version(name) for name in deps},
        "python": platform.python_version(),
        "search_constraints": asdict(constraints),
        "bootstrap": {"resamples": 1000, "seed": 42, "estimand": "weather-year mean"},
        "boundary_policy": "midpoint unknown-source initial SOC; unconstrained terminal SOC",
        "protocol_chronology": "unverified",
        "memory_abort_rule": "not enforced",
    }
