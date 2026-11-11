from pathlib import Path

import pytest

from estimate_kit.brief import BriefTask, parse_brief
from estimate_kit.rules import estimate_brief, estimate_task, load_rules


def test_default_rules_load() -> None:
    rules = load_rules()
    assert len(rules.categories) > 5
    assert "out of scope" in rules.skip_sections
    assert rules.default.name == "general"


def test_category_match_uses_hours_from_file() -> None:
    result = estimate_task(BriefTask("Owner login with password reset", "Owner"), load_rules())
    assert result.category == "auth"
    h = result.hours
    assert (h.best, h.likely, h.worst) == (6, 10, 20)
    assert h.expected == pytest.approx(11.0)  # (6 + 40 + 20) / 6
    assert result.modifiers == ()


def test_first_category_in_file_order_wins() -> None:
    # "email" (notifications) and "login" (auth) both match; auth is listed first.
    result = estimate_task(BriefTask("Login by email link", "A"), load_rules())
    assert result.category == "auth"


def test_unmatched_task_uses_default() -> None:
    result = estimate_task(BriefTask("Frobnicate the widgets", "A"), load_rules())
    assert result.category == "general"
    assert (result.hours.best, result.hours.likely, result.hours.worst) == (2, 5, 12)
    assert any("generic range" in a for a in result.assumptions)


def test_modifier_scales_and_rounds() -> None:
    result = estimate_task(BriefTask("Live chat for guests", "A"), load_rules())
    assert result.category == "general"
    assert result.modifiers == ("realtime",)
    h = result.hours
    assert (h.best, h.likely, h.worst) == (3, 7.5, 18)  # 2, 5, 12 times 1.5
    assert h.expected == pytest.approx(8.5)  # (3 + 30 + 18) / 6
    assert any("Real-time" in r for r in result.risks)


def test_modifier_found_in_details_and_factors_multiply() -> None:
    task = BriefTask("Gallery", "A", ("upload images", "in Arabic"))
    result = estimate_task(task, load_rules())
    assert result.category == "ui"  # 3 / 7 / 16
    assert set(result.modifiers) == {"uploads", "multilingual"}
    # 1.2 * 1.3 = 1.56 -> 4.68, 10.92, 24.96 -> rounded to 0.5
    h = result.hours
    assert (h.best, h.likely, h.worst) == (4.5, 11.0, 25.0)


def test_keyword_matches_word_start_only() -> None:
    result = estimate_task(BriefTask("Capital letters in names", "A"), load_rules())
    assert result.category == "general"  # "api" must not match inside "capital"


def test_estimate_brief_totals_and_deduped_risks() -> None:
    brief = parse_brief("## A\n- Login\n- Sign up page\n- Frobnicate\n")
    estimate = estimate_brief(brief, load_rules())
    assert [t.category for t in estimate.tasks] == ["auth", "auth", "general"]
    # 11.0 + 11.0 + (2 + 20 + 12) / 6
    assert estimate.total.expected == pytest.approx(22.0 + 34 / 6)
    auth_risks = [r for r in estimate.risks if r.startswith("Password reset")]
    assert len(auth_risks) == 1
    assert auth_risks[0].endswith("(Login, Sign up page)")
    assert estimate.assumptions[0].startswith("Estimates cover")


def test_custom_rules_file(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_text(
        '[default]\nname = "x"\nbest = 1\nlikely = 2\nworst = 3\n'
        '[[category]]\nname = "c"\nkeywords = ["foo"]\nbest = 4\nlikely = 5\nworst = 6\n',
        encoding="utf-8",
    )
    rules = load_rules(path)
    assert estimate_task(BriefTask("a foo", "s"), rules).hours.likely == 5
    assert rules.modifiers == ()
