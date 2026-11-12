import email.message
import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from estimate_kit.brief import Brief, BriefTask
from estimate_kit.cli import app
from estimate_kit.llm import (
    ENV_API_KEY,
    ENV_BASE_URL,
    ENV_ENABLED,
    LlmConfig,
    _post_chat,
    _repo_prompts_dir,
    estimate_with_llm,
    load_config,
    load_prompt,
)
from estimate_kit.rules import load_rules

PROMPTS = Path(__file__).parent.parent / "prompts" / "v1"
SECRET = "sk-test-secret-value"
CONFIG = LlmConfig(SECRET, "https://example.test/v1", "m", PROMPTS)


def _brief() -> Brief:
    return Brief("Demo", (BriefTask("Login", "Auth"), BriefTask("Landing page", "UI")))


def _run(payload: Any) -> Any:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return estimate_with_llm(_brief(), load_rules(), config=CONFIG, post_chat=lambda *_args: text)


def _task(title: str = "Login", **extra: Any) -> dict[str, Any]:
    return {"title": title, "best": 1, "likely": 2, "worst": 3, **extra}


@pytest.mark.parametrize(
    "url", ["http://api.example.com/v1", "ftp://example.com", "api.example.com/v1"]
)
def test_key_is_never_sent_over_plain_http_to_a_remote_host(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setenv(ENV_API_KEY, SECRET)
    monkeypatch.setenv(ENV_BASE_URL, url)
    with pytest.raises(ValueError, match="https"):
        load_config(PROMPTS)


@pytest.mark.parametrize("url", ["http://localhost:11434/v1", "http://127.0.0.1:8080/v1"])
def test_plain_http_is_allowed_for_localhost(monkeypatch: pytest.MonkeyPatch, url: str) -> None:
    monkeypatch.setenv(ENV_API_KEY, SECRET)
    monkeypatch.setenv(ENV_BASE_URL, url)
    assert load_config(PROMPTS).base_url == url


def test_openai_key_fallback_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    monkeypatch.delenv(ENV_BASE_URL, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "  fallback-key ")
    config = load_config()
    assert config.api_key == "fallback-key"
    assert config.base_url == "https://api.openai.com/v1"
    assert (config.prompts_dir / "system.md").is_file()


def test_prompts_are_found_and_versioned() -> None:
    assert _repo_prompts_dir().name == "v1"
    assert "prompt v1" in load_prompt(PROMPTS, "system.md")


@pytest.mark.parametrize(
    "bad",
    [
        "not json",
        "[]",
        '"text"',
        {"tasks": "Login"},
        {"tasks": [42]},
        {"tasks": [{"best": 1, "likely": 2, "worst": 3}]},
        {"tasks": [{"title": "Login", "best": 1, "likely": 2}]},
        {"tasks": [_task(best="lots")]},
        {"tasks": [_task(best=5, likely=2, worst=9)]},
        {"tasks": [_task(best=None)]},
        {"tasks": [_task(risks="a string, not a list")]},
        {"tasks": [_task(assumptions=5)]},
    ],
)
def test_malformed_model_output_is_rejected_with_a_value_error(bad: Any) -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        _run(bad)


def test_non_finite_numbers_from_the_model_are_rejected() -> None:
    raw = '{"tasks": [{"title": "Login", "best": 1, "likely": 2, "worst": Infinity}]}'
    with pytest.raises(ValueError, match="finite"):
        _run(raw)


def test_null_risks_are_treated_as_none() -> None:
    result = _run({"tasks": [_task(risks=None, assumptions=None), _task("Landing page")]})
    assert result.risks == ()


def test_titles_are_matched_ignoring_case_and_spacing() -> None:
    result = _run({"tasks": [_task("  login  "), _task("LANDING   page")]})
    assert [t.task.section for t in result.tasks] == ["Auth", "UI"]


def test_invented_and_missing_tasks_are_flagged() -> None:
    result = _run({"tasks": [_task("Login"), _task("Crypto wallet")]})
    assert any("Crypto wallet" in r and "added by the model" in r for r in result.risks)
    assert any("no estimate for: Landing page" in r for r in result.risks)
    assert result.reviewed is False


def test_duplicate_risks_are_merged_and_project_assumptions_kept() -> None:
    same = {"risks": ["Slow API"], "assumptions": ["Sandbox exists"]}
    result = _run({"tasks": [_task("Login", **same), _task("Landing page", **same)]})
    assert result.risks == ("Slow API (Login, Landing page)",)
    assert result.project_assumptions == load_rules().project_assumptions
    assert result.assumptions.count("Sandbox exists (Login, Landing page)") == 1


class _Response(io.BytesIO):
    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _patch_urlopen(monkeypatch: pytest.MonkeyPatch, result: Any) -> list[urllib.request.Request]:
    seen: list[urllib.request.Request] = []

    def fake(request: urllib.request.Request, timeout: float) -> _Response:
        seen.append(request)
        if isinstance(result, Exception):
            raise result
        return _Response(json.dumps(result).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return seen


def test_post_chat_sends_the_request_and_returns_the_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = _patch_urlopen(monkeypatch, {"choices": [{"message": {"content": "{}"}}]})
    assert _post_chat(CONFIG, "sys", "usr") == "{}"
    request = seen[0]
    assert request.full_url == "https://example.test/v1/chat/completions"
    assert request.get_header("Authorization") == f"Bearer {SECRET}"
    body = json.loads(request.data)  # type: ignore[arg-type]
    assert body["messages"][0] == {"role": "system", "content": "sys"}
    assert body["temperature"] == 0


def test_post_chat_errors_do_not_leak_the_key(monkeypatch: pytest.MonkeyPatch) -> None:
    http_error = urllib.error.HTTPError(
        CONFIG.base_url,
        401,
        "Unauthorized",
        email.message.Message(),
        io.BytesIO(b'{"error": "bad key"}'),
    )
    cases = [
        (http_error, "HTTP 401"),
        (urllib.error.URLError("no route"), "no route"),
        ({"choices": []}, "missing choices"),
        ({"unexpected": 1}, "missing choices"),
    ]
    for result, expected in cases:
        _patch_urlopen(monkeypatch, result)
        with pytest.raises(RuntimeError, match=expected) as info:
            _post_chat(CONFIG, "sys", "usr")
        assert SECRET not in str(info.value)


def test_cli_falls_back_to_rules_and_never_prints_the_key(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_API_KEY, SECRET)
    _patch_urlopen(monkeypatch, urllib.error.URLError("offline"))
    brief = tmp_path / "b.md"
    brief.write_text("# T\n## A\n- Login page\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["estimate", str(brief), "--skip-review"])
    assert result.exit_code == 0
    assert "falling back to keyword rules" in result.output
    assert "produced by keyword rules" in result.stdout
    assert SECRET not in result.output


def test_cli_falls_back_when_the_key_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    brief = tmp_path / "b.md"
    brief.write_text("# T\n## A\n- Login page\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["estimate", str(brief), "--skip-review"])
    assert result.exit_code == 0
    assert "no API key" in result.output


def test_cli_uses_the_llm_when_it_answers(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ENV_ENABLED, "1")
    monkeypatch.setenv(ENV_API_KEY, SECRET)
    reply = {"tasks": [{"title": "Login page", "best": 1, "likely": 2, "worst": 3}]}
    content = json.dumps(reply)
    _patch_urlopen(monkeypatch, {"choices": [{"message": {"content": content}}]})
    brief = tmp_path / "b.md"
    brief.write_text("# T\n## A\n- Login page\n", encoding="utf-8")
    result = CliRunner().invoke(app, ["estimate", str(brief), "--skip-review"])
    assert result.exit_code == 0
    assert "Draft produced by the LLM path. It has not been reviewed" in result.stdout
