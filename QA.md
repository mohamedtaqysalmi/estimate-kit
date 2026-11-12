# QA

Last updated: 2026-11-12. Numbers from the last run are in [TEST_REPORT.md](TEST_REPORT.md).

## Test strategy

| Layer | What | Why |
| --- | --- | --- |
| Unit | `ranges.py`, `brief.py`, `rules.py`, `export.py`, `review.py`, `llm.py` (HTTP mocked) | Core math and parsing must be deterministic with no network. |
| CLI integration | `tests/test_cli.py` and the edge-case files, via Typer's `CliRunner` | Covers estimate to export, `--skip-review`, the non-TTY guard, accept-all review and quitting midway. |
| Static site | Open `site/index.html` through a local web server and use the calculator | Pages has no build step, so this is a manual browser check. |
| Coverage gate | pytest-cov, fail under 85% | Set in `pyproject.toml`, enforced by CI. |

Not covered: calls to a real LLM provider, browser automation against the live Pages site, and calibration of `rules.toml` against real projects.

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

"Scripted" means I ran the step with piped input rather than typing it into a terminal.

| Step | Expected | Result on 2026-11-12 |
| --- | --- | --- |
| `estimate-kit estimate examples/riad-booking.md` in a real terminal | Prompts `[a/e/d]` per task; after accepting all, Markdown says reviewed | Scripted only; not run by hand |
| Same with `--skip-review` | Exits 0; output says not reviewed | Pass |
| Same with piped stdin and no `--skip-review` | Refuses with exit code 2 | Pass (also covered by a test) |
| `ESTIMATE_KIT_LLM=1` without an API key | Falls back to rules with a message on stderr | Pass |
| Edit one task during review to `4 8 12` | Exported row shows those hours and the summary changes | Pass (test) |
| Drop every task | Exit 1, "No tasks left after review" | Pass (test) |
| Open the Pages site at 360px width | Readable, calculator usable, no horizontal page scroll | Not re-checked in this review |
| Enter best above likely in the calculator | Message names the row; the row is left out of the totals | Not re-checked in this review |
| README "How not to trust this tool" | Present | Pass |

## Known limits

- Keyword categories miss multilingual work (called out in the README).
- The plausible range assumes independent tasks.
- The LLM path has only been tested against mocked responses.
- No lockfile (pip plus Dependabot only).
- Briefs are read as English Markdown: bullets under headings. Tables and prose requirements are skipped.
