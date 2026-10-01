# Contributing

## Development setup

```bash
pip install -c constraints.txt hatchling editables build
pip install --no-build-isolation -c constraints.txt -e ".[dev]"
```

## Quality checks

```bash
ruff check src tests
mypy src
pyright src
pytest tests/ --cov=northern_microgrid --cov-report=term-missing
```

## Pull requests

- Keep changes focused
- Add tests for new behaviour
- Maintain 90%+ library coverage
- Use Canadian spelling in documentation

Use the shared constraints for both Python targets. Generated scientific values are compared with `python scripts/compare_results.py <expected.json> <actual.json>`.
