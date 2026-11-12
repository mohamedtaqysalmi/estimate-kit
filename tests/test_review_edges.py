from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from estimate_kit.brief import BriefTask
from estimate_kit.cli import app
from estimate_kit.ranges import ThreePoint, combine
from estimate_kit.review import review_estimate
from estimate_kit.rules import Estimate, EstimatedTask


def _draft() -> Estimate:
    items = (
        EstimatedTask(
            BriefTask("Login", "Auth"), "auth", ThreePoint(6, 10, 20), (), ("R",), ("A",)
        ),
        EstimatedTask(BriefTask("Landing", "UI"), "ui", ThreePoint(3, 7, 16), (), (), ()),
    )
    return Estimate(
        title="Demo",
        tasks=items,
        total=combine(i.hours for i in items),
        risks=("R (Login)",),
        assumptions=("Project rule (one developer)", "A (Login)"),
        skipped_sections=(),
        project_assumptions=("Project rule (one developer)",),
    )


def _answers(*values: str) -> Callable[[str], str]:
    it = iter(values)
    return lambda _prompt: next(it)


def _review(*values: str) -> tuple[Estimate, list[str]]:
    printed: list[str] = []
    result = review_estimate(_draft(), input_fn=_answers(*values), print_fn=printed.append)
    return result, printed


def test_project_assumptions_survive_even_with_parentheses() -> None:
    result, _ = _review("a", "a")
    assert result.assumptions[0] == "Project rule (one developer)"
    assert "A (Login)" in result.assumptions


def test_dropping_a_task_removes_its_risks_and_assumptions() -> None:
    result, _ = _review("d", "a")
    assert result.risks == ()
    assert result.assumptions == ("Project rule (one developer)",)


def test_blank_and_unknown_choices_ask_again() -> None:
    result, printed = _review("", "x", "accept", "drop")
    assert [t.task.title for t in result.tasks] == ["Login"]
    assert printed.count("  Choose a, e or d.") == 2


def test_long_command_names_work() -> None:
    result, _ = _review("edit", "1 2 3", "drop")
    assert result.tasks[0].hours == ThreePoint(1, 2, 3)


def test_cancelling_an_edit_returns_to_the_task() -> None:
    result, _ = _review("e", "", "a", "a")
    assert result.tasks[0].hours == ThreePoint(6, 10, 20)


@pytest.mark.parametrize("bad", ["1 2", "3 2 1", "a b c", "inf inf inf", "nan nan nan", "-1 2 3"])
def test_bad_hours_are_refused_and_the_old_range_kept(bad: str) -> None:
    result, printed = _review("e", bad, "a", "a")
    assert result.tasks[0].hours == ThreePoint(6, 10, 20)
    assert any("Need exactly three" in p or "Invalid hours" in p for p in printed)


def test_edited_hours_accept_commas_and_are_rounded() -> None:
    result, _ = _review("e", "1.2, 2.6, 3.9", "a")
    assert result.tasks[0].hours == ThreePoint(1.0, 2.5, 4.0)


def test_quitting_midway_exports_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("estimate_kit.cli._stdin_is_tty", lambda: True)
    brief = tmp_path / "brief.md"
    brief.write_text("# T\n## A\n- Login\n- Landing page\n", encoding="utf-8")
    out = tmp_path / "out.md"
    result = CliRunner().invoke(app, ["estimate", str(brief), "-o", str(out)], input="a\n")
    assert result.exit_code != 0
    assert not out.exists()
    assert "# Estimate" not in result.stdout


def test_reviewer_sees_the_risks_and_assumptions_they_are_accepting() -> None:
    _, printed = _review("a", "a")
    assert "  risk: R" in printed
    assert "  assumes: A" in printed
