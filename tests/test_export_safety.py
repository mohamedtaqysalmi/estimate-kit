import csv
import io

import pytest

from estimate_kit.brief import BriefTask
from estimate_kit.export import to_csv, to_markdown
from estimate_kit.ranges import ThreePoint, combine
from estimate_kit.rules import Estimate, EstimatedTask


def _estimate(title: str, section: str = "S", category: str = "c") -> Estimate:
    item = EstimatedTask(
        BriefTask(title, section), category, ThreePoint(1, 2, 3), (), ("risk\nover two lines",), ()
    )
    return Estimate("T", (item,), combine([item.hours]), item.risks, (), ())


@pytest.mark.parametrize("start", ["=", "+", "-", "@"])
def test_csv_neutralises_formula_starts(start: str) -> None:
    text = f'{start}HYPERLINK("http://example.test","x")'
    rows = list(csv.reader(io.StringIO(to_csv(_estimate(text, section=text, category=text)))))
    assert rows[1][:3] == ["'" + text] * 3


def test_csv_neutralises_a_formula_hidden_behind_spaces() -> None:
    rows = list(csv.reader(io.StringIO(to_csv(_estimate("  =1+1")))))
    assert rows[1][1] == "'  =1+1"


def test_csv_leaves_ordinary_text_alone() -> None:
    rows = list(csv.reader(io.StringIO(to_csv(_estimate("Pay 50% up front, then 50%")))))
    assert rows[1][1] == "Pay 50% up front, then 50%"


def test_csv_keeps_newlines_and_quotes_in_one_cell() -> None:
    rows = list(csv.reader(io.StringIO(to_csv(_estimate('line one\nline "two"')))))
    assert rows[1][1] == 'line one\nline "two"'
    assert len(rows) == 2


def test_markdown_escapes_pipes_in_category_and_flattens_list_items() -> None:
    text = to_markdown(_estimate("Task", category="a|b"))
    assert "| a\\|b |" in text
    assert "- risk over two lines\n" in text
