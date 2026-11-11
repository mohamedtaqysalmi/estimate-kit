from pathlib import Path

from typer.testing import CliRunner

from estimate_kit import __version__
from estimate_kit.cli import app

runner = CliRunner()
EXAMPLE = Path(__file__).parent.parent / "examples" / "riad-booking.md"


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"estimate-kit {__version__}"


def test_markdown_to_stdout() -> None:
    result = runner.invoke(app, ["estimate", str(EXAMPLE)])
    assert result.exit_code == 0
    assert result.stdout.startswith("# Estimate: Riad Lotus booking site")
    assert "Mobile app" not in result.stdout  # out-of-scope bullet skipped
    assert "## Ignored sections" in result.stdout
    assert "expected ± 2 spread" in result.stdout


def test_csv_to_file(tmp_path: Path) -> None:
    out = tmp_path / "out.csv"
    result = runner.invoke(app, ["estimate", str(EXAMPLE), "-f", "csv", "-o", str(out)])
    assert result.exit_code == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("section,task,category")
    assert len(lines) > 10


def test_brief_without_tasks_fails(tmp_path: Path) -> None:
    brief = tmp_path / "empty.md"
    brief.write_text("# Nothing here\n\nJust prose.\n", encoding="utf-8")
    result = runner.invoke(app, ["estimate", str(brief)])
    assert result.exit_code == 1
    assert "No tasks found" in result.output


def test_missing_file_is_a_usage_error(tmp_path: Path) -> None:
    result = runner.invoke(app, ["estimate", str(tmp_path / "nope.md")])
    assert result.exit_code == 2


def test_bad_format_is_a_usage_error() -> None:
    result = runner.invoke(app, ["estimate", str(EXAMPLE), "-f", "markdwn"])
    assert result.exit_code == 2
