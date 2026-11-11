from estimate_kit.brief import BriefTask
from estimate_kit.export import to_csv, to_markdown
from estimate_kit.ranges import ThreePoint, combine
from estimate_kit.rules import Estimate, EstimatedTask


def _estimate(title: str = "Café site", sections: tuple[str, ...] = ()) -> Estimate:
    items = (
        EstimatedTask(
            task=BriefTask('Pay, then "confirm" | email', "Réservation"),
            category="payments",
            hours=ThreePoint(10, 18, 40),
            modifiers=(),
            risks=(),
            assumptions=(),
        ),
        EstimatedTask(
            task=BriefTask("Page d'accueil été مرحبا", "Public"),
            category="ui",
            hours=ThreePoint(3, 7, 16),
            modifiers=(),
            risks=(),
            assumptions=(),
        ),
    )
    return Estimate(
        title=title,
        tasks=items,
        total=combine(i.hours for i in items),
        risks=("Risk one (Pay)",),
        assumptions=("Assume A",),
        skipped_sections=sections,
    )


def test_csv_exact_output_with_escaping_and_unicode() -> None:
    expected = (
        "section,task,category,best_h,likely_h,worst_h,expected_h,spread_h\n"
        'Réservation,"Pay, then ""confirm"" | email",payments,10.0,18.0,40.0,20.3,5.0\n'
        "Public,Page d'accueil été مرحبا,ui,3.0,7.0,16.0,7.8,2.2\n"
    )
    assert to_csv(_estimate()) == expected


def test_markdown_exact_output() -> None:
    expected = """\
# Estimate: Café site

Draft produced by keyword rules. It has not been reviewed by a person.

## Summary

| Measure | Hours |
| --- | ---: |
| Sum of best cases | 13.0 |
| Sum of likely cases | 25.0 |
| Expected (PERT) | 28.2 |
| Plausible range (expected ± 2 spread) | 17.3 to 39.1 |
| Sum of worst cases | 56.0 |

## Tasks

| Section | Task | Category | Best | Likely | Worst | Expected |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Réservation | Pay, then "confirm" \\| email | payments | 10.0 | 18.0 | 40.0 | 20.3 |
| Public | Page d'accueil été مرحبا | ui | 3.0 | 7.0 | 16.0 | 7.8 |

## Risks

- Risk one (Pay)

## Assumptions

- Assume A
"""
    assert to_markdown(_estimate()) == expected


def test_markdown_lists_ignored_sections_and_handles_no_risks() -> None:
    est = _estimate(sections=("Out of scope",))
    text = to_markdown(
        Estimate(est.title, est.tasks, est.total, (), est.assumptions, est.skipped_sections)
    )
    assert "- None recorded." in text
    assert text.endswith("## Ignored sections\n\n- Out of scope\n")


def test_markdown_cell_collapses_newlines() -> None:
    text = to_markdown(_estimate(title="Two\nlines"))
    assert text.startswith("# Estimate: Two lines\n")
