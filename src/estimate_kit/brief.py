"""Turn a Markdown brief into candidate tasks.

Rules:

- The first level-1 heading is the project title.
- Every other heading starts a section.
- Each top-level bullet (`-`, `*`, `+` or `1.` / `1)`) in a section is one task.
  A leading `[ ]` or `[x]` is dropped.
- Bullets indented by two or more spaces (or a tab) belong to the bullet above
  them. They are kept as details and used for keyword matching, not as tasks.
- Bullets under a heading that contains one of `skip_sections` (for example
  "Out of scope") are ignored, and so is everything nested below that heading.
- `**` and backticks are removed from task text. Nothing else is interpreted.

Not understood: tables, prose paragraphs, front matter, HTML, links to other
documents, and bullets that pack several features into one line ("login and
billing" is one task). Requirements written as plain sentences are skipped
without a warning, so check the task list against your brief.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_BULLET = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?(\S.*?)\s*$")
_FENCE = re.compile(r"^\s*(```|~~~)")

UNTITLED = "Untitled project"
NO_SECTION = "(no heading)"


@dataclass(frozen=True)
class BriefTask:
    title: str
    section: str
    details: tuple[str, ...] = ()


@dataclass(frozen=True)
class Brief:
    title: str
    tasks: tuple[BriefTask, ...]
    skipped_sections: tuple[str, ...] = field(default=())


def _clean(text: str) -> str:
    return text.replace("**", "").replace("`", "").strip()


def parse_brief(text: str, skip_sections: tuple[str, ...] = ()) -> Brief:
    title: str | None = None
    section = NO_SECTION
    skipping_level: int | None = None
    skipped: list[str] = []
    in_fence = False
    # Each entry is [title, section, details]; frozen at the end.
    open_tasks: list[tuple[str, str, list[str]]] = []

    for raw in text.splitlines():
        line = raw.expandtabs(4)
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading = _HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            name = _clean(heading.group(2))
            if skipping_level is not None and level <= skipping_level:
                skipping_level = None
            if title is None and level == 1:
                title = name
            if skipping_level is None and any(s in name.lower() for s in skip_sections):
                skipping_level = level
                skipped.append(name)
            section = name
            continue

        if skipping_level is not None:
            continue

        bullet = _BULLET.match(line)
        if not bullet:
            continue
        text_ = _clean(bullet.group(2))
        nested = len(bullet.group(1)) >= 2
        if nested and open_tasks and open_tasks[-1][1] == section:
            open_tasks[-1][2].append(text_)
        else:
            open_tasks.append((text_, section, []))

    tasks = tuple(BriefTask(t, s, tuple(d)) for t, s, d in open_tasks)
    return Brief(title or UNTITLED, tasks, tuple(skipped))
