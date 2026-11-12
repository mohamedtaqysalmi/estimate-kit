from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from estimate_kit import __version__
from estimate_kit.brief import parse_brief
from estimate_kit.export import to_csv, to_markdown
from estimate_kit.llm import estimate_with_llm, llm_enabled
from estimate_kit.review import review_estimate
from estimate_kit.rules import estimate_brief, load_rules

app = typer.Typer(help="Turn a Markdown project brief into a draft estimate.", no_args_is_help=True)


class OutputFormat(StrEnum):
    markdown = "markdown"
    csv = "csv"


def _write_stdout(text: str) -> None:
    # Windows consoles often default to a legacy code page; write UTF-8 bytes so
    # task names and the plus-minus sign survive.
    try:
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.flush()
    except AttributeError:
        typer.echo(text, nl=False)


def _stdin_is_tty() -> bool:
    return sys.stdin.isatty()


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"estimate-kit {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_show_version, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    pass


@app.command()
def estimate(
    brief: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    fmt: Annotated[OutputFormat, typer.Option("--format", "-f")] = OutputFormat.markdown,
    output: Annotated[Path | None, typer.Option("--output", "-o", help="Write to a file.")] = None,
    rules: Annotated[
        Path | None, typer.Option(help="Use a different rules file.", exists=True, dir_okay=False)
    ] = None,
    skip_review: Annotated[
        bool,
        typer.Option(
            "--skip-review",
            help="Skip the interactive review. Output stays marked as unreviewed.",
        ),
    ] = False,
) -> None:
    """Read BRIEF, estimate, force a human review, then print Markdown or CSV."""
    rule_set = load_rules(rules)
    parsed = parse_brief(brief.read_text(encoding="utf-8-sig"), rule_set.skip_sections)
    if not parsed.tasks:
        typer.echo(
            "No tasks found. The brief needs bullet lists under headings; see the README.",
            err=True,
        )
        raise typer.Exit(code=1)

    if llm_enabled():
        try:
            result = estimate_with_llm(parsed, rule_set)
            typer.echo("Used LLM path (ESTIMATE_KIT_LLM=1).", err=True)
        except Exception as exc:
            typer.echo(f"LLM path failed ({exc}); falling back to keyword rules.", err=True)
            result = estimate_brief(parsed, rule_set)
    else:
        result = estimate_brief(parsed, rule_set)

    if not skip_review:
        if not _stdin_is_tty():
            typer.echo(
                "Review is required but stdin is not a TTY. "
                "Re-run interactively, or pass --skip-review for an unreviewed draft.",
                err=True,
            )
            raise typer.Exit(code=2)
        try:
            result = review_estimate(result)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc

    text = to_csv(result) if fmt is OutputFormat.csv else to_markdown(result)
    if output is None:
        _write_stdout(text)
    else:
        output.write_text(text, encoding="utf-8", newline="\n")
        typer.echo(f"Wrote {output}", err=True)
