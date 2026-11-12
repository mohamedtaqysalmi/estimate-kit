# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Briefs saved with a UTF-8 byte order mark lost their title and first section.
- Horizontal rules (`* * *`, `- - -`), YAML front matter bullets, bullets in HTML comments and empty `[ ]` checkboxes were turned into tasks. Underlined (`====`) headings were not recognised.
- Sections were skipped when their heading merely contained a skip word, so "Background jobs" and "Timeline view" disappeared. Only whole headings match now.
- CSV cells starting with `=`, `+`, `-` or `@` are prefixed with a quote so spreadsheets do not run them as formulas.
- Typing `inf` or a huge number when editing hours crashed the review with a traceback. Non-finite hours are rejected.
- The LLM path accepted a plain `http://` base URL for a remote host and would have sent the API key in clear text. It now needs https (http only for localhost).
- LLM output where `risks` was a string, `best` was missing, or the model skipped or invented tasks produced garbage or confusing errors. Bad output now falls back to rules with a clear message, and invented or missing tasks are flagged in the risks.
- The review showed only hours, so a reviewer accepted risks and assumptions they never saw. Each task now lists them before the prompt.
- Review rebuilt project-level assumptions by looking for " (" in the text, which dropped any assumption containing a bracket.
- Markdown export did not escape `|` in categories or flatten line breaks in risks and assumptions.
- Docs: `QA.md` and `TEST_REPORT.md` moved to the repo root and now hold real results instead of pending placeholders; the CLI reference no longer claims a `-h` flag.

### Added

- Mandatory interactive review (`accept` / `edit` / `drop` per task) before export; `--skip-review` keeps the draft marked unreviewed.
- Optional LLM path behind `ESTIMATE_KIT_LLM=1` with versioned prompts in `prompts/v1/` and rule-based fallback.
- GitHub Pages site with brief→output example and in-browser PERT range calculator (`site/`).
- `QA.md` and `TEST_REPORT.md` at the repo root, `docs/architecture.md` and `docs/cli.md`.

## [0.1.0] — 2026-11-11

### Added

- Project scaffold: package layout, tooling configuration and a version test.
- Markdown brief parser: headings become sections, bullets become tasks, skippable sections.
- Rule-based estimator with all hours, keywords, risks and assumptions in `rules.toml`.
- Three-point (PERT) range math with validation and combined totals.
- Markdown and CSV export.
- `estimate-kit estimate` command and an example brief in `examples/`.
- README sections on ranges and "How not to trust this tool".
