"""Interactive human review of a draft estimate.

Every task is shown with its proposed range. The reviewer must accept, edit or
drop each one before the estimate can be marked reviewed. Export code treats
``reviewed=False`` as a draft that has not been checked by a person.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from estimate_kit.ranges import ThreePoint, combine
from estimate_kit.rules import Estimate, EstimatedTask, _gather

PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]


def _prompt_hours(item: EstimatedTask, input_fn: InputFn, print_fn: PrintFn) -> ThreePoint | None:
    print_fn(
        f"  Current: best={item.hours.best:.1f}  likely={item.hours.likely:.1f}  "
        f"worst={item.hours.worst:.1f}  (expected {item.hours.expected:.1f})"
    )
    print_fn("  Enter best, likely, worst as three numbers (or blank to cancel):")
    raw = input_fn("  > ").strip()
    if not raw:
        return None
    parts = raw.replace(",", " ").split()
    if len(parts) != 3:
        print_fn("  Need exactly three numbers.")
        return None
    try:
        best, likely, worst = (float(p) for p in parts)
        return ThreePoint(best, likely, worst).rounded()
    except ValueError as exc:
        print_fn(f"  Invalid hours: {exc}")
        return None


def review_estimate(
    estimate: Estimate,
    *,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> Estimate:
    """Walk each task and require accept / edit / drop before returning."""
    kept: list[EstimatedTask] = []
    total = len(estimate.tasks)
    print_fn(f"Review {total} task(s) for: {estimate.title}")
    print_fn("For each task: [a]ccept  [e]dit hours  [d]rop  (required before export)")
    print_fn("")

    for index, item in enumerate(estimate.tasks, start=1):
        while True:
            h = item.hours
            print_fn(f"[{index}/{total}] {item.task.section} — {item.task.title}")
            print_fn(f"  category={item.category}  modifiers={', '.join(item.modifiers) or 'none'}")
            print_fn(
                f"  best={h.best:.1f}  likely={h.likely:.1f}  worst={h.worst:.1f}  "
                f"expected={h.expected:.1f}"
            )
            choice = input_fn("  [a/e/d] > ").strip().lower()
            if choice in {"a", "accept"}:
                kept.append(item)
                break
            if choice == "":
                print_fn("  Choose a, e or d.")
                continue
            if choice in {"d", "drop"}:
                print_fn("  Dropped.")
                break
            if choice in {"e", "edit"}:
                edited = _prompt_hours(item, input_fn, print_fn)
                if edited is None:
                    continue
                item = replace(item, hours=edited)
                kept.append(item)
                print_fn(
                    f"  Saved: best={edited.best:.1f}  likely={edited.likely:.1f}  "
                    f"worst={edited.worst:.1f}"
                )
                break
            print_fn("  Choose a, e or d.")
        print_fn("")

    if not kept:
        raise ValueError("No tasks left after review. Nothing to export.")

    risks = _gather([(r, t.task.title) for t in kept for r in t.risks])
    task_assumptions = _gather([(a, t.task.title) for t in kept for a in t.assumptions])
    # Keep project-level assumptions (those without a task title suffix) from the draft.
    project_assumptions = tuple(a for a in estimate.assumptions if " (" not in a)
    return Estimate(
        title=estimate.title,
        tasks=tuple(kept),
        total=combine(t.hours for t in kept),
        risks=risks,
        assumptions=(*project_assumptions, *task_assumptions),
        skipped_sections=estimate.skipped_sections,
        reviewed=True,
        engine=estimate.engine,
    )
