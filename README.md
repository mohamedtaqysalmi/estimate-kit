# estimate-kit

A CLI that turns a Markdown project brief into a task breakdown with best, likely and worst estimates, plus risks and assumptions. The output is a draft for a person to correct.

## Status

Usable offline for drafts. Parse a brief, estimate from keyword rules, **review every task**, export Markdown or CSV. An optional LLM path sits behind `ESTIMATE_KIT_LLM=1` and falls back to rules on any failure. Hour figures are still uncalibrated against real delivery data.

Live demo: [Pages range calculator](https://mohamedtaqysalmi.github.io/estimate-kit/).

## Try it

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"

estimate-kit estimate examples/riad-booking.md
estimate-kit estimate examples/riad-booking.md --format csv --output estimate.csv
estimate-kit estimate examples/riad-booking.md --skip-review   # draft stays marked unreviewed
```

`--rules path/to/rules.toml` uses your own numbers instead of the built-in ones.

### Review

By default the CLI asks `[a]ccept` / `[e]dit` / `[d]rop` for each task. Export is marked reviewed only after that walk. Non-interactive runs need `--skip-review`.

## Example

[`examples/riad-booking.md`](examples/riad-booking.md) is an invented brief for a small guesthouse. This is the start of the real output of the command above (the full output also lists risks and assumptions per task, and ignored sections):

```markdown
# Estimate: Riad Lotus booking site

Draft produced by keyword rules. It has not been reviewed by a person.

## Summary

| Measure | Hours |
| --- | ---: |
| Sum of best cases | 55.5 |
| Sum of likely cases | 111.5 |
| Expected (PERT) | 125.5 |
| Plausible range (expected ± 2 spread) | 105.6 to 145.4 |
| Sum of worst cases | 251.5 |

## Tasks

| Section | Task | Category | Best | Likely | Worst | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Public site | Landing page with photo gallery and a short story about the riad | ui | 3.0 | 7.0 | 16.0 | 7.8 |
| Public site | Room pages with prices per night and a calendar showing availability | ui | 3.0 | 7.0 | 16.0 | 7.8 |
| Public site | Contact form that emails the owner | notifications | 3.0 | 7.0 | 16.0 | 7.8 |
| Public site | Site available in English, French and Arabic | general | 2.5 | 6.5 | 15.5 | 7.3 |
| Booking | Guests pick dates and a room, then pay a 30% deposit online with Stripe | payments | 10.0 | 18.0 | 40.0 | 20.3 |
| Booking | Confirmation email with the booking details | notifications | 3.0 | 7.0 | 16.0 | 7.8 |
| Booking | Reminder email three days before arrival | notifications | 3.0 | 7.0 | 16.0 | 7.8 |
| Owner area | Owner login with password reset | auth | 6.0 | 10.0 | 20.0 | 11.0 |
| Owner area | Admin screens to manage rooms, prices and blocked dates | admin | 8.0 | 14.0 | 30.0 | 15.7 |
| Owner area | Monthly report of bookings and income, exportable as a spreadsheet | reporting | 5.0 | 10.0 | 22.0 | 11.2 |
| Owner area | Import existing bookings from the owner's Excel sheet | integration | 6.0 | 12.0 | 30.0 | 14.0 |
| Launch | Deploy to a standard host with a custom domain and daily backups | devops | 3.0 | 6.0 | 14.0 | 6.8 |
```

The "Site available in English, French and Arabic" row shows a weak spot: no category keyword matched, so it got the generic range with a language multiplier. A person would size multilingual work differently.

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `ESTIMATE_KIT_LLM` | unset / off | Set to `1` / `true` / `on` to try the LLM path first. |
| `ESTIMATE_KIT_LLM_API_KEY` | — | API key (falls back to `OPENAI_API_KEY`). Required when LLM is on. |
| `ESTIMATE_KIT_LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible base URL. |
| `ESTIMATE_KIT_LLM_MODEL` | `gpt-4o-mini` | Chat model id. |

Prompts live in [`prompts/v1/`](prompts/v1/) and are versioned with the pack folder name. The base URL must be https (plain http is accepted only for localhost) because the API key is sent in a header. Malformed model output, a missing key or a network error prints a message on stderr and falls back to the keyword rules.

## How it works

```mermaid
flowchart LR
  brief[Markdown brief] --> parse[Parse]
  parse --> est[Rules or LLM]
  est --> review[Human review]
  review --> out[Markdown / CSV]
```

1. **Parsing.** Headings become sections and top-level bullets become tasks. Indented bullets are details of the bullet above. A section whose whole heading is "Out of scope", "Background", "Assumptions" and a few similar names (see `skip_sections` in `rules.toml`) is skipped and listed at the end of the output; "Background jobs" is not skipped. The exact rules are in the docstring of [`brief.py`](src/estimate_kit/brief.py).
2. **Rules (default).** Each task is matched against the categories in [`rules.toml`](src/estimate_kit/rules.toml) by keyword. Every hour figure, keyword, risk and assumption is in that one file. Modifiers (real-time, mobile, multilingual, migration, uploads) multiply the range.
3. **LLM (optional).** When `ESTIMATE_KIT_LLM=1`, the brief is sent with the v1 prompt pack. Any error falls back to rules.
4. **Review.** Accept, edit or drop each task. Required unless `--skip-review`. Quitting midway exports nothing.
5. **Range math.** See [`ranges.py`](src/estimate_kit/ranges.py). Per task: expected = (best + 4 x likely + worst) / 6, spread = (worst - best) / 6. For the total, expected values add and spreads combine as the square root of the sum of squares. Best, likely and worst are validated so that best <= likely <= worst.
6. **Export.** Markdown and CSV, UTF-8. Status line states whether a person reviewed the draft.

### Brief shapes it does not understand

- Tables, prose paragraphs and requirements written as plain sentences. They are skipped without a warning.
- HTML other than comments, and links to other documents. (A byte order mark, YAML front matter, HTML comments, code fences and horizontal rules are ignored.)
- One bullet that contains several features ("login and billing" becomes one task).
- Nested bullets are never separate tasks, even when they should be.
- Only English keywords are matched.

If the task list in the output does not match your brief, the brief shape is the problem. Reshape it as headings with one bullet per deliverable.

## Why ranges

A single number hides the thing a client most needs to know, which is how wrong it might be. A task that is 3 hours when everything goes right and 16 when one assumption fails is a different risk from one that is always 7. The tool keeps all three numbers per task and shows the spread in the total.

Adding worst cases naively overstates the risk (every task going badly at once) and adding best cases understates it. The summary shows both sums next to the PERT total so you can see the gap.

## How not to trust this tool

- The hour figures in `rules.toml` are my rough starting points. They are not measured from past projects and nothing here has been calibrated against actual delivery times.
- CSV export prefixes cells that start with `=`, `+`, `-` or `@` with a single quote, so a spreadsheet does not run them as formulas. The quote is part of the cell text.
- Keyword matching is crude. A task is categorised by words, not by understanding it. Check the Category column.
- The plausible range treats tasks as independent. In real projects they are not: one wrong assumption about a client's data or approvals can slow many tasks together. The true uncertainty is wider than the "plausible range" line says.
- Anything the brief does not mention is not estimated. Testing by others, meetings, revisions, content and project management are excluded (see the assumptions in the output).
- The output is a draft. Read every row, change what you disagree with, and do not send it to a client unchecked.

## Testing

See [QA.md](QA.md) for strategy and the manual checklist, and [TEST_REPORT.md](TEST_REPORT.md) for the last run. Architecture notes: [docs/architecture.md](docs/architecture.md). CLI options: [docs/cli.md](docs/cli.md).

```bash
pre-commit install
ruff check .
ruff format --check .
mypy
pytest
```

`pytest` also reports coverage and fails below 85%. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Limitations and roadmap

- Hour figures in `rules.toml` are starting points, not calibrated.
- No live LLM test in CI; only mocked parsing.
- Pages site teaches the math; it does not run the Python parser.
- Next: calibration notes from real projects, richer review UX, prompt pack v2 if the JSON contract changes.

## Security notes

Report vulnerabilities privately via [SECURITY.md](SECURITY.md). Do not put client briefs or API keys in the repo. The LLM path sends the brief text to the configured provider when enabled.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT, see [LICENSE](LICENSE).
