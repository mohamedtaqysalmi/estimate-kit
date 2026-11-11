from estimate_kit.brief import NO_SECTION, UNTITLED, parse_brief

SKIP = ("out of scope", "background")


def test_title_sections_and_tasks() -> None:
    text = "# Shop\n\n## Catalog\n\n- Product list\n* Product page\n1. Search box\n2) Filters\n"
    brief = parse_brief(text)
    assert brief.title == "Shop"
    assert [t.title for t in brief.tasks] == [
        "Product list",
        "Product page",
        "Search box",
        "Filters",
    ]
    assert {t.section for t in brief.tasks} == {"Catalog"}


def test_nested_bullets_become_details_not_tasks() -> None:
    brief = parse_brief("## A\n- Checkout\n  - with Stripe\n    - and refunds\n- Emails\n")
    assert [t.title for t in brief.tasks] == ["Checkout", "Emails"]
    assert brief.tasks[0].details == ("with Stripe", "and refunds")


def test_tab_indent_counts_as_nested() -> None:
    brief = parse_brief("## A\n- One\n\t- detail\n")
    assert len(brief.tasks) == 1
    assert brief.tasks[0].details == ("detail",)


def test_checkboxes_and_emphasis_are_stripped() -> None:
    brief = parse_brief("## A\n- [ ] **Login** page\n- [x] `Search` box\n")
    assert [t.title for t in brief.tasks] == ["Login page", "Search box"]


def test_skipped_sections_and_their_subsections() -> None:
    text = (
        "# P\n## Features\n- Keep\n## Out of scope\n- Drop\n### Later\n- Drop too\n"
        "## More\n- Keep as well\n## Background\n- Drop 3\n"
    )
    brief = parse_brief(text, SKIP)
    assert [t.title for t in brief.tasks] == ["Keep", "Keep as well"]
    assert brief.skipped_sections == ("Out of scope", "Background")


def test_prose_tables_and_code_fences_are_ignored() -> None:
    text = "## A\nSome prose sentence.\n| a | b |\n|---|---|\n```\n- not a task\n```\n- Real task\n"
    brief = parse_brief(text)
    assert [t.title for t in brief.tasks] == ["Real task"]


def test_no_title_and_bullets_before_any_heading() -> None:
    brief = parse_brief("- Orphan\n")
    assert brief.title == UNTITLED
    assert brief.tasks[0].section == NO_SECTION


def test_indented_bullet_without_parent_is_a_task() -> None:
    brief = parse_brief("## A\n  - starts indented\n")
    assert [t.title for t in brief.tasks] == ["starts indented"]


def test_empty_brief() -> None:
    assert parse_brief("").tasks == ()
