"""Turn a Markdown brief into candidate tasks.

Rules:

- The first level-1 heading is the project title. `#` headings and underlined
  (`====` / `----`) headings both work.
- Every other heading starts a section.
- Each top-level bullet (`-`, `*`, `+` or `1.` / `1)`) in a section is one task.
  A leading `[ ]` or `[x]` is dropped.
- Bullets indented by two or more spaces (or a tab) belong to the bullet above
  them. They are kept as details and used for keyword matching, not as tasks.
- A section is skipped, with everything nested below it, when its whole heading
  is one of `skip_sections` (for example "Out of scope"). Case, a trailing "s"
  and a parenthetical such as "(v1)" are ignored; "Background jobs" is not
  "Background" and stays in.
- A leading UTF-8 byte order mark, YAML front matter (`---` ... `---` at the
  top), HTML comments, fenced code blocks and horizontal rules are ignored.
- `**` and backticks are removed from task text. Nothing else is interpreted.

Not understood: tables, prose paragraphs, other HTML, links to other documents,
and bullets that pack several features into one line ("login and billing" is
one task). Requirements written as plain sentences are skipped without a
warning, so check the task list against your brief.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_BULLET = re.compile(r"^(\s*)(?:[-*+]|\d+[.)])\s+(\S.*?)\s*$")
_CHECKBOX = re.compile(r"^\[[ xX]\]\s*")
_FENCE = re.compile(r"^\s*(```|~~~)")
_RULE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
_UNDERLINE = re.compile(r"^\s{0,3}(=+|-+)\s*$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_PAREN = re.compile(r"\([^)]*\)")

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


def _is_skipped(name: str, skip_sections: tuple[str, ...]) -> bool:
    normal = " ".join(_PAREN.sub("", name).lower().strip(" :.-").split())
    return any(normal in (term, f"{term}s") for term in skip_sections)


def _strip_front_matter(lines: list[str]) -> list[str]:
    if lines and lines[0].strip() == "---":
        for end in range(1, len(lines)):
            if lines[end].strip() in {"---", "..."}:
                return lines[end + 1 :]
    return lines


def parse_brief(text: str, skip_sections: tuple[str, ...] = ()) -> Brief:
    lines = _strip_front_matter(_COMMENT.sub("", text.removeprefix("\ufeff")).splitlines())
    title: str | None = None
    section = NO_SECTION
    skipping_level: int | None = None
    skipped: list[str] = []
    in_fence = False
    # Each entry is (title, section, details); frozen at the end.
    open_tasks: list[tuple[str, str, list[str]]] = []

    index = 0
    while index < len(lines):
        line = lines[index].expandtabs(4)
        index += 1
        if _FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        level = 0
        name = ""
        heading = _HEADING.match(line)
        if heading:
            level, name = len(heading.group(1)), _clean(heading.group(2))
        elif (
            line.strip()
            and len(line) - len(line.lstrip()) < 4
            and not _BULLET.match(line)
            and not _RULE.match(line)
            and index < len(lines)
            and (underline := _UNDERLINE.match(lines[index]))
        ):
            level = 1 if underline.group(1).startswith("=") else 2
            name = _clean(line)
            index += 1
        if level:
            if skipping_level is not None and level <= skipping_level:
                skipping_level = None
            if title is None and level == 1:
                title = name
            if skipping_level is None and _is_skipped(name, skip_sections):
                skipping_level = level
                skipped.append(name)
            section = name
            continue

        if skipping_level is not None or _RULE.match(line):
            continue

        bullet = _BULLET.match(line)
        if not bullet:
            continue
        item = _clean(_CHECKBOX.sub("", bullet.group(2)))
        if not item:
            continue
        nested = len(bullet.group(1)) >= 2
        if nested and open_tasks and open_tasks[-1][1] == section:
            open_tasks[-1][2].append(item)
        else:
            open_tasks.append((item, section, []))

    tasks = tuple(BriefTask(t, s, tuple(d)) for t, s, d in open_tasks)
    return Brief(title or UNTITLED, tasks, tuple(skipped))
