"""Load rules.toml and apply it to parsed tasks."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from estimate_kit.brief import Brief, BriefTask
from estimate_kit.ranges import ThreePoint, Total, combine


@dataclass(frozen=True)
class CategoryRule:
    name: str
    keywords: tuple[str, ...]
    hours: ThreePoint
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class ModifierRule:
    name: str
    keywords: tuple[str, ...]
    factor: float
    risk: str


@dataclass(frozen=True)
class RuleSet:
    default: CategoryRule
    categories: tuple[CategoryRule, ...]
    modifiers: tuple[ModifierRule, ...]
    project_assumptions: tuple[str, ...]
    skip_sections: tuple[str, ...]


@dataclass(frozen=True)
class EstimatedTask:
    task: BriefTask
    category: str
    hours: ThreePoint
    modifiers: tuple[str, ...]
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]


@dataclass(frozen=True)
class Estimate:
    title: str
    tasks: tuple[EstimatedTask, ...]
    total: Total
    risks: tuple[str, ...]
    assumptions: tuple[str, ...]
    skipped_sections: tuple[str, ...]


def _category(data: dict[str, Any], name: str | None = None) -> CategoryRule:
    return CategoryRule(
        name=name or data["name"],
        keywords=tuple(data.get("keywords", ())),
        hours=ThreePoint(data["best"], data["likely"], data["worst"]),
        risks=tuple(data.get("risks", ())),
        assumptions=tuple(data.get("assumptions", ())),
    )


def load_rules(path: Path | None = None) -> RuleSet:
    if path is None:
        raw = resources.files("estimate_kit").joinpath("rules.toml").read_text("utf-8")
    else:
        raw = path.read_text("utf-8")
    data = tomllib.loads(raw)
    return RuleSet(
        default=_category(data["default"]),
        categories=tuple(_category(c) for c in data.get("category", ())),
        modifiers=tuple(
            ModifierRule(m["name"], tuple(m["keywords"]), float(m["factor"]), m["risk"])
            for m in data.get("modifier", ())
        ),
        project_assumptions=tuple(data.get("project", {}).get("assumptions", ())),
        skip_sections=tuple(s.lower() for s in data.get("parsing", {}).get("skip_sections", ())),
    )


def _matches(keywords: tuple[str, ...], text: str) -> bool:
    # A keyword matches at the start of a word, so "login" also finds "logins"
    # but "api" does not match inside "capital".
    return any(re.search(rf"(?<![a-z0-9]){re.escape(k)}", text) for k in keywords)


def estimate_task(task: BriefTask, rules: RuleSet) -> EstimatedTask:
    text = " ".join((task.title, *task.details)).lower()
    category = next((c for c in rules.categories if _matches(c.keywords, text)), rules.default)
    hours = category.hours
    risks = list(category.risks)
    applied: list[str] = []
    for mod in rules.modifiers:
        if _matches(mod.keywords, text):
            hours = hours.scaled(mod.factor)
            risks.append(mod.risk)
            applied.append(mod.name)
    return EstimatedTask(
        task=task,
        category=category.name,
        hours=hours.rounded(),
        modifiers=tuple(applied),
        risks=tuple(risks),
        assumptions=category.assumptions,
    )


def _gather(items: list[tuple[str, str]]) -> tuple[str, ...]:
    """Merge (text, task title) pairs so each text appears once with its tasks."""
    by_text: dict[str, list[str]] = {}
    for text, title in items:
        by_text.setdefault(text, [])
        if title not in by_text[text]:
            by_text[text].append(title)
    return tuple(f"{text} ({', '.join(titles)})" for text, titles in by_text.items())


def estimate_brief(brief: Brief, rules: RuleSet) -> Estimate:
    tasks = tuple(estimate_task(t, rules) for t in brief.tasks)
    risks = _gather([(r, t.task.title) for t in tasks for r in t.risks])
    task_assumptions = _gather([(a, t.task.title) for t in tasks for a in t.assumptions])
    return Estimate(
        title=brief.title,
        tasks=tasks,
        total=combine(t.hours for t in tasks),
        risks=risks,
        assumptions=(*rules.project_assumptions, *task_assumptions),
        skipped_sections=brief.skipped_sections,
    )
