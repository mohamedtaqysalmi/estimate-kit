import json
from pathlib import Path

import pytest

from estimate_kit.brief import Brief, BriefTask
from estimate_kit.llm import (
    ENV_API_KEY,
    ENV_ENABLED,
    LlmConfig,
    estimate_with_llm,
    llm_enabled,
    load_config,
    render_user_prompt,
)
from estimate_kit.rules import load_rules

PROMPTS = Path(__file__).parent.parent / "prompts" / "v1"


def _brief() -> Brief:
    return Brief(
        "Demo",
        (
            BriefTask("Owner login with password reset", "Owner area"),
            BriefTask("Landing page with photo gallery", "Public site"),
        ),
    )


def test_llm_enabled_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_ENABLED, raising=False)
    assert llm_enabled() is False
    monkeypatch.setenv(ENV_ENABLED, "1")
    assert llm_enabled() is True
    monkeypatch.setenv(ENV_ENABLED, "false")
    assert llm_enabled() is False


def test_load_config_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_API_KEY, raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key"):
        load_config(PROMPTS)


def test_render_user_prompt_injects_brief() -> None:
    template = "BEGIN\n{{brief}}\nEND\n"
    text = render_user_prompt(template, _brief())
    assert "Owner login with password reset" in text
    assert "{{brief}}" not in text


def test_estimate_with_llm_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "test-key")
    payload = {
        "tasks": [
            {
                "title": "Owner login with password reset",
                "section": "Owner area",
                "category": "auth",
                "best": 6,
                "likely": 10,
                "worst": 20,
                "risks": ["Password email deliverability"],
                "assumptions": [],
            },
            {
                "title": "Landing page with photo gallery",
                "section": "Public site",
                "category": "ui",
                "best": 3,
                "likely": 7,
                "worst": 16,
                "risks": [],
                "assumptions": ["Photos supplied by client"],
            },
        ]
    }

    def fake_post(config: LlmConfig, system: str, user: str) -> str:
        assert "estimate-kit prompt v1" in system
        assert "Owner login" in user
        assert config.api_key == "test-key"
        return json.dumps(payload)

    result = estimate_with_llm(
        _brief(),
        load_rules(),
        config=LlmConfig("test-key", "https://example.test/v1", "gpt-test", PROMPTS),
        post_chat=fake_post,
    )
    assert result.engine == "llm"
    assert result.reviewed is False
    assert len(result.tasks) == 2
    assert result.tasks[0].category == "auth"
    assert result.tasks[0].hours.best == 6
    assert "Password email deliverability" in result.risks[0]


def test_estimate_with_llm_rejects_empty_tasks(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_API_KEY, "test-key")

    def fake_post(config: LlmConfig, system: str, user: str) -> str:
        return json.dumps({"tasks": []})

    with pytest.raises(ValueError, match="tasks"):
        estimate_with_llm(
            _brief(),
            load_rules(),
            config=LlmConfig("test-key", "https://example.test/v1", "gpt-test", PROMPTS),
            post_chat=fake_post,
        )
