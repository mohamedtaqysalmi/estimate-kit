# Contributing

estimate-kit is maintained by one person in their spare time. Issues and pull requests are welcome,
but replies may take a few days. If you plan a large change, open an issue first so we can agree on
the direction before you spend time on it.

## Setup

You need Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pre-commit install
```

## Running the checks

CI runs the same commands on Python 3.11 and 3.14.

```bash
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

`pytest` reports coverage and fails below 85%. New behaviour needs tests.

## Branches and commits

- Branch from `main`. Name branches `type/short-description`, for example `feat/csv-export` or
  `fix/empty-brief`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`,
  `chore:`, `test:`, `refactor:`).
- `main` takes changes through pull requests only, squash-merged once CI is green.

## Pull requests

- Keep a PR to one change. Fill in the template: what, why, how you tested it.
- CI must pass. Please fix failures rather than loosening a check.
- Add a line to the Unreleased section of `CHANGELOG.md` for user-visible changes.
- Use fake data in tests and examples. Never commit real client briefs or secrets.

By contributing you agree that your work is released under the MIT license.
