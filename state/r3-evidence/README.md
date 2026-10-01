# Round-three verification receipts

Dated 2026-10-01. Final receipts use `*-final.txt`, `before-verified.txt`, `regeneration.json`, `regeneration-final.txt`, `release-final.txt` and `prior-art.json`. Other files inherited from the interrupted round-three work are intermediate/superseded and are not the final validation evidence.

Local installation/test paths are redacted. Original raw logs and local independent reviews stay outside the publication payload. The baseline red tests ran on an isolated archive of commit 27ba7c7; the generated source was verified in a separate clean Git checkout. The original repository history was preserved.

Dependency installation used a locally reconstructed wheelhouse from already installed distributions because upstream package downloads were unavailable. This checks portable constrained resolution and isolated installation, not upstream wheel authenticity. The reconstructed Ruff wheel lacked its native binary; final Ruff checks use the installed 0.16.9 executable, with caches disabled. Numerical/runtime tests use both fresh environments.

The release scan is a bounded pattern scan over tracked/history/archive bytes plus decoded PNG/Parquet metadata and string columns; it is not a fresh dedicated Gitleaks run or a proof of absence.
