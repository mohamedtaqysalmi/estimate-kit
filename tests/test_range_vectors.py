import html
import json
from pathlib import Path

import pytest

from estimate_kit.ranges import ThreePoint, combine

SITE = Path(__file__).parent.parent / "site"
VECTORS = json.loads((SITE / "range-vectors.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", VECTORS["cases"], ids=lambda c: c["name"])
def test_combine_matches_shared_vectors(case: dict[str, object]) -> None:
    total = combine(ThreePoint(*t) for t in case["tasks"])  # type: ignore[attr-defined]
    for key, want in case["total"].items():  # type: ignore[attr-defined]
        assert getattr(total, key) == pytest.approx(want, abs=VECTORS["tolerance"]), key


@pytest.mark.parametrize("task", VECTORS["invalid"])
def test_invalid_vectors_are_rejected(task: list[float]) -> None:
    with pytest.raises(ValueError, match="best"):
        ThreePoint(*task)


def test_example_output_on_page_matches_cli() -> None:
    """Every task row and summary figure on the page must come from the real output."""
    from typer.testing import CliRunner

    from estimate_kit.cli import app

    example = Path(__file__).parent.parent / "examples" / "riad-booking.md"
    result = CliRunner().invoke(app, ["estimate", str(example), "--skip-review"])
    assert result.exit_code == 0
    page = html.unescape((SITE / "index.html").read_text(encoding="utf-8"))
    lines = result.stdout.splitlines()
    # Header rows sit right above a "| --- |" separator and are not copied to the page.
    rows = [
        ln
        for i, ln in enumerate(lines)
        if ln.startswith("| ") and not lines[i + 1].startswith("| ---")
    ]
    cells = [
        c.strip() for ln in rows if not ln.startswith("| ---") for c in ln.strip("|").split("|")
    ]
    assert len(cells) > 30
    for cell in cells:
        assert cell in page, cell


def test_site_has_no_leftover_decoration_files() -> None:
    names = {p.name for p in SITE.iterdir()}
    assert "styles.css" not in names
    assert {"base.css", "base.js", "page.css", "index.html", "favicon.svg", "og.svg"} <= names
