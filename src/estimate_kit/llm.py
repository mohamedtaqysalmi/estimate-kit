"""Optional LLM estimate path, off unless ESTIMATE_KIT_LLM=1.

When enabled, the brief is sent to an OpenAI-compatible chat API using the
versioned prompt files under ``prompts/``. Any failure (missing key, HTTP error,
bad JSON) falls back to the rule-based estimator so the CLI still works offline.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from estimate_kit.brief import Brief, BriefTask
from estimate_kit.ranges import ThreePoint, combine
from estimate_kit.rules import Estimate, EstimatedTask, RuleSet

ENV_ENABLED = "ESTIMATE_KIT_LLM"
ENV_API_KEY = "ESTIMATE_KIT_LLM_API_KEY"
ENV_BASE_URL = "ESTIMATE_KIT_LLM_BASE_URL"
ENV_MODEL = "ESTIMATE_KIT_LLM_MODEL"
ENV_OPENAI_KEY = "OPENAI_API_KEY"

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
PROMPT_VERSION = "v1"


@dataclass(frozen=True)
class LlmConfig:
    api_key: str
    base_url: str
    model: str
    prompts_dir: Path


def llm_enabled() -> bool:
    return os.environ.get(ENV_ENABLED, "").strip().lower() in {"1", "true", "yes", "on"}


def _repo_prompts_dir() -> Path:
    # Prefer the repo-root prompts/ when developing from a checkout; fall back to
    # the packaged copy shipped inside the wheel.
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "prompts" / PROMPT_VERSION,
        here.parent / "prompts" / PROMPT_VERSION,
    ]
    for path in candidates:
        if (path / "system.md").is_file() and (path / "user.md").is_file():
            return path
    raise FileNotFoundError(
        f"Prompt files for {PROMPT_VERSION} not found. Expected system.md and user.md "
        f"under prompts/{PROMPT_VERSION}/."
    )


def load_config(prompts_dir: Path | None = None) -> LlmConfig:
    key = os.environ.get(ENV_API_KEY) or os.environ.get(ENV_OPENAI_KEY) or ""
    if not key.strip():
        raise ValueError(
            f"{ENV_ENABLED} is set but no API key was found. Set {ENV_API_KEY} or {ENV_OPENAI_KEY}."
        )
    return LlmConfig(
        api_key=key.strip(),
        base_url=os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL).rstrip("/"),
        model=os.environ.get(ENV_MODEL, DEFAULT_MODEL),
        prompts_dir=prompts_dir or _repo_prompts_dir(),
    )


def load_prompt(prompts_dir: Path, name: str) -> str:
    path = prompts_dir / name
    return path.read_text(encoding="utf-8")


def _brief_for_prompt(brief: Brief) -> str:
    lines = [f"# {brief.title}", ""]
    current = None
    for task in brief.tasks:
        if task.section != current:
            current = task.section
            lines += [f"## {current}", ""]
        lines.append(f"- {task.title}")
        for detail in task.details:
            lines.append(f"  - {detail}")
    return "\n".join(lines).strip() + "\n"


def render_user_prompt(template: str, brief: Brief) -> str:
    return template.replace("{{brief}}", _brief_for_prompt(brief))


def _post_chat(config: LlmConfig, system: str, user: str) -> str:
    payload = {
        "model": config.model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    request = urllib.request.Request(
        f"{config.base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "estimate-kit",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM HTTP {exc.code}: {detail[:400]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc.reason}") from exc
    try:
        return str(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("LLM response missing choices[0].message.content") from exc


def _parse_tasks(raw: str, brief: Brief) -> list[EstimatedTask]:
    data: dict[str, Any] = json.loads(raw)
    items = data.get("tasks")
    if not isinstance(items, list) or not items:
        raise ValueError("LLM JSON must contain a non-empty 'tasks' array")

    by_title = {t.title.lower(): t for t in brief.tasks}
    estimated: list[EstimatedTask] = []
    for entry in items:
        if not isinstance(entry, dict):
            raise ValueError("Each task must be an object")
        title = str(entry.get("title", "")).strip()
        if not title:
            raise ValueError("Task missing title")
        source = by_title.get(title.lower())
        section = str(entry.get("section") or (source.section if source else "(no heading)"))
        category = str(entry.get("category") or "general")
        hours = ThreePoint(
            float(entry["best"]),
            float(entry["likely"]),
            float(entry["worst"]),
        ).rounded()
        risks = tuple(str(r) for r in entry.get("risks", ()) if str(r).strip())
        assumptions = tuple(str(a) for a in entry.get("assumptions", ()) if str(a).strip())
        task = source or BriefTask(title, section)
        estimated.append(
            EstimatedTask(
                task=task,
                category=category,
                hours=hours,
                modifiers=(),
                risks=risks,
                assumptions=assumptions,
            )
        )
    return estimated


def estimate_with_llm(
    brief: Brief,
    rules: RuleSet,
    *,
    config: LlmConfig | None = None,
    post_chat: Any = None,
) -> Estimate:
    cfg = config or load_config()
    system = load_prompt(cfg.prompts_dir, "system.md")
    user = render_user_prompt(load_prompt(cfg.prompts_dir, "user.md"), brief)
    poster = post_chat or _post_chat
    content = poster(cfg, system, user)
    tasks = tuple(_parse_tasks(content, brief))
    risks = tuple(f"{r} ({t.task.title})" for t in tasks for r in t.risks)
    # De-dupe while preserving order
    seen: set[str] = set()
    unique_risks: list[str] = []
    for r in risks:
        if r not in seen:
            seen.add(r)
            unique_risks.append(r)
    task_assumptions = tuple(f"{a} ({t.task.title})" for t in tasks for a in t.assumptions)
    return Estimate(
        title=brief.title,
        tasks=tasks,
        total=combine(t.hours for t in tasks),
        risks=tuple(unique_risks),
        assumptions=(*rules.project_assumptions, *task_assumptions),
        skipped_sections=brief.skipped_sections,
        reviewed=False,
        engine="llm",
    )
