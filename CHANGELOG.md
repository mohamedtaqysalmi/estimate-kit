# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Mandatory interactive review (`accept` / `edit` / `drop` per task) before export; `--skip-review` keeps the draft marked unreviewed.
- Optional LLM path behind `ESTIMATE_KIT_LLM=1` with versioned prompts in `prompts/v1/` and rule-based fallback.
- GitHub Pages site with brief→output example and in-browser PERT range calculator (`site/`).
- `docs/QA.md`, `docs/architecture.md`, `docs/TEST_REPORT.md`.

## [0.1.0] — 2026-11-11

### Added

- Project scaffold: package layout, tooling configuration and a version test.
- Markdown brief parser: headings become sections, bullets become tasks, skippable sections.
- Rule-based estimator with all hours, keywords, risks and assumptions in `rules.toml`.
- Three-point (PERT) range math with validation and combined totals.
- Markdown and CSV export.
- `estimate-kit estimate` command and an example brief in `examples/`.
- README sections on ranges and "How not to trust this tool".
