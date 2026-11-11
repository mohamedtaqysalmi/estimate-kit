# estimate-kit

A CLI that turns a Markdown project brief into a task breakdown with best, likely and worst estimates, plus risks and assumptions. A human has to review the result before anything is exported.

Status: early scaffold, nothing usable yet.

## Development setup

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## Running the checks

```bash
ruff check .
ruff format --check .
mypy
pytest
```

`pytest` also reports coverage and fails below 85%.

## License

MIT, see [LICENSE](LICENSE).
