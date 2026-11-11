from dataclasses import replace

import pytest

from estimate_kit.brief import BriefTask
from estimate_kit.ranges import ThreePoint, combine
from estimate_kit.review import review_estimate
from estimate_kit.rules import Estimate, EstimatedTask


def _draft() -> Estimate:
    items = (
        EstimatedTask(
            BriefTask("Login form", "Auth"),
            "auth",
            ThreePoint(6, 10, 20),
            (),
            ("Auth risk",),
            ("Password reset email works",),
        ),
        EstimatedTask(
            BriefTask("Landing page", "UI"),
            "ui",
            ThreePoint(3, 7, 16),
            (),
            (),
            (),
        ),
    )
    return Estimate(
        title="Demo",
        tasks=items,
        total=combine(i.hours for i in items),
        risks=("Auth risk (Login form)",),
        assumptions=("Hours exclude meetings", "Password reset email works (Login form)"),
        skipped_sections=(),
        reviewed=False,
        engine="rules",
    )


def test_accept_all_marks_reviewed() -> None:
    answers = iter(["a", "a"])
    result = review_estimate(_draft(), input_fn=lambda _: next(answers), print_fn=lambda _: None)
    assert result.reviewed is True
    assert len(result.tasks) == 2
    assert result.total.expected == pytest.approx(_draft().total.expected)


def test_edit_updates_hours_and_total() -> None:
    answers = iter(["e", "4 8 12", "a"])
    result = review_estimate(_draft(), input_fn=lambda _: next(answers), print_fn=lambda _: None)
    assert result.tasks[0].hours == ThreePoint(4, 8, 12)
    assert result.reviewed is True
    assert result.total.best == pytest.approx(7.0)


def test_drop_removes_task() -> None:
    answers = iter(["d", "a"])
    result = review_estimate(_draft(), input_fn=lambda _: next(answers), print_fn=lambda _: None)
    assert len(result.tasks) == 1
    assert result.tasks[0].task.title == "Landing page"


def test_drop_all_raises() -> None:
    answers = iter(["d", "d"])
    with pytest.raises(ValueError, match="No tasks left"):
        review_estimate(_draft(), input_fn=lambda _: next(answers), print_fn=lambda _: None)


def test_invalid_edit_retries_then_accepts() -> None:
    answers = iter(["e", "1 2", "e", "5 5 5", "a"])
    result = review_estimate(_draft(), input_fn=lambda _: next(answers), print_fn=lambda _: None)
    assert result.tasks[0].hours == ThreePoint(5, 5, 5)


def test_engine_preserved() -> None:
    draft = replace(_draft(), engine="llm")
    answers = iter(["a", "a"])
    result = review_estimate(draft, input_fn=lambda _: next(answers), print_fn=lambda _: None)
    assert result.engine == "llm"
