# TEST_REPORT — v0.1.0

Date: 2026-11-11 (generated for release cut; re-run before tagging if commits landed after this file).

## Command

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
```

## Results (fill from local / CI run at tag time)

| Check | Result |
| --- | --- |
| ruff check | clean after autofix (local 2026-11-11) |
| ruff format | clean (local 2026-11-11) |
| mypy --strict | pending confirmation in this cut |
| pytest | 54 passed (local, Python 3.12) |
| Coverage | **89%** (gate ≥ 85%) |
| Python matrix in CI | 3.11, 3.14 |

## What is covered

- Brief parsing: headings, bullets, nested details, skip sections, fences.
- Range math: validation, scale/round, combine, clamp.
- Rules matching and modifiers.
- Markdown/CSV export including Unicode and escaping.
- Review accept / edit / drop / empty-draft failure.
- LLM config, prompt injection, JSON parse, empty-tasks rejection (mocked HTTP).
- CLI `--skip-review`, non-TTY guard, version flag.

## What is not covered

- Live LLM HTTP against a real provider.
- Playwright / Lighthouse automation for Pages.
- Calibration of hour figures against delivered projects.
- End-to-end interactive TTY session outside `CliRunner`.
