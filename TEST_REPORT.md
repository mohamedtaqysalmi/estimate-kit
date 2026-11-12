# Test report

Run on 2026-11-12 against the `fix/review-findings` branch, on top of v0.1.0. Re-run it before tagging a release; the numbers below are a snapshot, not something CI keeps current.

## Commands

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

## Results

| Check | Result |
| --- | --- |
| ruff check | clean |
| ruff format --check | clean |
| mypy (strict) | no issues in 20 files |
| pytest | 121 passed |
| Coverage | 98%, gate is 85% |
| python -m build | sdist and wheel build; the wheel contains `rules.toml` and `prompts/v1/` |
| Wheel installed in a clean venv | `estimate-kit --version` runs and the prompt files are found |

Local run: Windows 11, Python 3.12.10, ruff 0.17.4, mypy 2.4.1, pytest 9.2.0, pytest-cov 7.1.0, typer 0.29.1. Python 3.15 could not install the dev extras (PyYAML has no wheel for it), so the local suite was not run there. CI runs Python 3.11 and 3.14.

## What the tests cover

- Brief parsing: headings (both styles), bullets, nested details, skipped sections, code fences, byte order mark, front matter, HTML comments, horizontal rules, empty checkboxes.
- Range math: validation, non-finite values, rounding, hand-computed totals, clamping.
- Rule matching and modifiers.
- Markdown and CSV export: escaping, non-ASCII text, spreadsheet formula prefixes.
- Review: accept, edit, drop, invalid input, cancelling, quitting midway (nothing is exported).
- LLM path with HTTP mocked: configuration, https requirement, malformed output, fallback to rules, the API key staying out of error output.
- CLI: `--skip-review`, non-TTY guard, version flag, files with a byte order mark.

## What is not covered

- Live calls to a real LLM provider.
- An interactive terminal session outside Typer's `CliRunner`.
- Calibration of the hour figures against delivered projects.
- Browser automation for the Pages site.
