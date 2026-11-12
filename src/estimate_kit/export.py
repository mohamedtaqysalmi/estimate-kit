from __future__ import annotations

import csv
import io

from estimate_kit.rules import Estimate

CSV_COLUMNS = (
    "section",
    "task",
    "category",
    "best_h",
    "likely_h",
    "worst_h",
    "expected_h",
    "spread_h",
    "reviewed",
    "engine",
)


def _h(value: float) -> str:
    return f"{value:.1f}"


def _line(text: str) -> str:
    return " ".join(text.split())


def _cell(text: str) -> str:
    return _line(text).replace("|", "\\|")


# Spreadsheet programs run cells that start with these characters as formulas.
_FORMULA_STARTS = ("=", "+", "-", "@")


def _csv_text(text: str) -> str:
    if text.lstrip().startswith(_FORMULA_STARTS):
        return "'" + text
    return text


def _status_line(estimate: Estimate) -> str:
    engine = "keyword rules" if estimate.engine == "rules" else "the LLM path"
    if estimate.reviewed:
        return f"Draft produced by {engine}. Reviewed by a person before export."
    return f"Draft produced by {engine}. It has not been reviewed by a person."


def to_csv(estimate: Estimate) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    reviewed = "yes" if estimate.reviewed else "no"
    for item in estimate.tasks:
        h = item.hours
        writer.writerow(
            [
                _csv_text(item.task.section),
                _csv_text(item.task.title),
                _csv_text(item.category),
                _h(h.best),
                _h(h.likely),
                _h(h.worst),
                _h(h.expected),
                _h(h.spread),
                reviewed,
                estimate.engine,
            ]
        )
    return buffer.getvalue()


def to_markdown(estimate: Estimate) -> str:
    t = estimate.total
    lines = [
        f"# Estimate: {_cell(estimate.title)}",
        "",
        _status_line(estimate),
        "",
        "## Summary",
        "",
        "| Measure | Hours |",
        "| --- | ---: |",
        f"| Sum of best cases | {_h(t.best)} |",
        f"| Sum of likely cases | {_h(t.likely)} |",
        f"| Expected (PERT) | {_h(t.expected)} |",
        f"| Plausible range (expected ± 2 spread) | {_h(t.low)} to {_h(t.high)} |",
        f"| Sum of worst cases | {_h(t.worst)} |",
        "",
        "## Tasks",
        "",
        "| Section | Task | Category | Best | Likely | Worst | Expected |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for item in estimate.tasks:
        h = item.hours
        lines.append(
            f"| {_cell(item.task.section)} | {_cell(item.task.title)} | {_cell(item.category)} "
            f"| {_h(h.best)} | {_h(h.likely)} | {_h(h.worst)} | {_h(h.expected)} |"
        )
    lines += ["", "## Risks", ""]
    lines += [f"- {_line(r)}" for r in estimate.risks] or ["- None recorded."]
    lines += ["", "## Assumptions", ""]
    lines += [f"- {_line(a)}" for a in estimate.assumptions]
    if estimate.skipped_sections:
        lines += ["", "## Ignored sections", ""]
        lines += [f"- {_cell(s)}" for s in estimate.skipped_sections]
    return "\n".join(lines) + "\n"
