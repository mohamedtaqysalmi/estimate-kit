# CLI reference

Entry point: `estimate-kit` (module `estimate_kit.cli:app`).

## Global

| Flag | Effect |
| --- | --- |
| `--version` | Print `estimate-kit <version>` and exit. |
| `-h` / `--help` | Show help. |

## `estimate BRIEF`

Read a Markdown brief and print a draft estimate.

| Option | Default | Effect |
| --- | --- | --- |
| `--format` / `-f` | `markdown` | `markdown` or `csv`. |
| `--output` / `-o` | stdout | Write UTF-8 file instead of stdout. |
| `--rules PATH` | packaged `rules.toml` | Alternate rules file. |
| `--skip-review` | off | Skip interactive review; output stays unreviewed. |

Exit codes: `0` success, `1` no tasks / review emptied the list, `2` usage error or review required without a TTY.

Environment for the optional LLM path: see the configuration table in the README.
