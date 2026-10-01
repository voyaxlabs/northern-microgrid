"""Compare all scientific JSON values; exclude timing and environment/revision receipts."""

import json
import math
import sys
from pathlib import Path


def compare(expected, actual, location="root"):
    if isinstance(expected, dict):
        ignored = {"timing"} if location == "root" else set()
        if location == "root.run_metadata":
            ignored = {"source_revision", "source_revision_scope", "dependencies", "python"}
        keys = set(expected) - ignored
        assert keys == set(actual) - ignored, f"{location}: keys differ"
        for key in sorted(keys):
            compare(expected[key], actual[key], f"{location}.{key}")
    elif isinstance(expected, list):
        assert len(expected) == len(actual), f"{location}: length differs"
        for i, (left, right) in enumerate(zip(expected, actual, strict=True)):
            compare(left, right, f"{location}[{i}]")
    elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
        assert math.isclose(expected, actual, rel_tol=1e-9, abs_tol=1e-6), location
    else:
        assert expected == actual, location


if __name__ == "__main__":
    compare(json.loads(Path(sys.argv[1]).read_text()), json.loads(Path(sys.argv[2]).read_text()))
    print(
        "PASS: scientific values and input/code/config hashes match "
        "(rtol=1e-9, atol=1e-6); timing/revision/environment receipts excluded"
    )
