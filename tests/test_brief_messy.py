from pathlib import Path

from typer.testing import CliRunner

from estimate_kit.brief import parse_brief
from estimate_kit.cli import app
from estimate_kit.rules import load_rules

SKIP = load_rules().skip_sections


def _titles(text: str, skip: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    return [(t.section, t.title) for t in parse_brief(text, skip).tasks]


def test_byte_order_mark_does_not_hide_the_title() -> None:
    assert parse_brief("﻿# Shop\n## A\n- x\n").title == "Shop"


def test_cli_reads_a_file_saved_with_a_bom(tmp_path: Path) -> None:
    brief = tmp_path / "brief.md"
    brief.write_bytes("﻿# Shop\n## A\n- Login page\n".encode())
    result = CliRunner().invoke(app, ["estimate", str(brief), "--skip-review"])
    assert result.exit_code == 0
    assert result.stdout.startswith("# Estimate: Shop")


def test_horizontal_rules_are_not_tasks() -> None:
    text = "## A\n- a\n\n* * *\n\n- b\n- - -\n___\n"
    assert _titles(text) == [("A", "a"), ("A", "b")]


def test_front_matter_bullets_are_not_tasks() -> None:
    text = "---\ntitle: x\ntags:\n- one\n- two\n---\n# T\n- real\n"
    brief = parse_brief(text)
    assert brief.title == "T"
    assert [t.title for t in brief.tasks] == ["real"]


def test_unclosed_front_matter_is_left_alone() -> None:
    assert _titles("---\n## A\n- a\n") == [("A", "a")]


def test_underlined_headings() -> None:
    text = "Shop\n====\n\nCatalog\n-------\n- Product list\n\n---\n- After a rule\n"
    brief = parse_brief(text)
    assert brief.title == "Shop"
    assert [(t.section, t.title) for t in brief.tasks] == [
        ("Catalog", "Product list"),
        ("Catalog", "After a rule"),
    ]


def test_bullet_followed_by_dashes_is_not_a_heading() -> None:
    assert _titles("## A\n- item\n---\n") == [("A", "item")]


def test_empty_checkbox_is_not_a_task() -> None:
    assert _titles("## A\n- [ ]\n- [x] done\n") == [("A", "done")]


def test_html_comments_are_ignored() -> None:
    assert _titles("<!--\n- hidden\n-->\n## A\n- a <!-- inline -->\n") == [("A", "a")]


def test_skip_matches_whole_headings_only() -> None:
    text = (
        "## Background jobs\n- Nightly cleanup\n"
        "## Timeline view\n- Gantt chart\n"
        "## Background\n- skip 1\n"
        "## Out of scope (v1)\n- skip 2\n"
        "## Non-goals:\n- skip 3\n"
        "## Open Questions\n- skip 4\n"
    )
    brief = parse_brief(text, SKIP)
    assert [t.title for t in brief.tasks] == ["Nightly cleanup", "Gantt chart"]
    assert brief.skipped_sections == (
        "Background",
        "Out of scope (v1)",
        "Non-goals:",
        "Open Questions",
    )


def test_crlf_line_endings() -> None:
    brief = parse_brief("# T\r\n## A\r\n- a\r\n  - detail\r\n")
    assert brief.tasks[0].details == ("detail",)
