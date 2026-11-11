# QA

Last prepared: 2026-11-11 · Environment target: Windows 10 / Python 3.11+ · Reviewer: maintainer (manual run pending).

## Test strategy

| Layer | What | Why |
| --- | --- | --- |
| Unit | `ranges.py`, `brief.py`, `rules.py`, `review.py`, `llm.py` (mocked HTTP) | Core math and parsing must be deterministic with no network. |
| CLI integration | `tests/test_cli.py` via Typer `CliRunner` | Covers estimate → export, `--skip-review`, non-TTY guard, accept-all review. |
| Static site smoke | Open `site/index.html` locally; exercise calculator | Pages has no build step; manual / browser check is enough for v0.1.0. |
| Coverage gate | pytest-cov, fail under 85% | Stated in `pyproject.toml` and CI. |

Not covered yet: live calls to a real LLM API, Playwright against GitHub Pages, calibration of `rules.toml` against real projects.

## How to run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy
pytest
```

## Manual checklist

| Step | Expected | Pass / Fail |
| --- | --- | --- |
| `estimate-kit estimate examples/riad-booking.md` in a real terminal | Prompts `[a/e/d]` per task; after accepts, Markdown says reviewed | |
| Same with `--skip-review` | Exits 0; output says not reviewed | |
| `ESTIMATE_KIT_LLM=1` without API key | Falls back to rules with a stderr message | |
| Edit one task during review to `4 8 12` | Exported row shows those hours; summary changes | |
| Drop every task | Exit 1, "No tasks left after review" | |
| Open `site/index.html` at 360px width | Hero brand readable; calculator usable; no horizontal overflow | |
| Change a calculator worst below likely | That row ignored until valid; totals still compute for valid rows | |
| README "How not to trust this tool" | Present and linked from the Pages caution line | |

## Known bugs / limits

- Keyword categories miss multilingual work (called out in README).
- Plausible range assumes independent tasks.
- LLM path is untested against a live provider in CI.
- No lockfile yet (pip + Dependabot only).

## Last manual run

| Field | Value |
| --- | --- |
| Date | 2026-11-11 (agent prep; maintainer still runs interactive TTY + Pages) |
| OS / Python | Windows 10 / Python 3.12.10 |
| pytest summary | 54 passed |
| Coverage % | 89% |
| Pages check | _pending — enable Pages + open live URL_ |
