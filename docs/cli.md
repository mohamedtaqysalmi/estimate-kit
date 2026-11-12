# CLI reference

Entry point: `estimate-kit` (module `estimate_kit.cli:app`).

## Global

| Flag | Effect |
| --- | --- |
| `--version` | Print `estimate-kit <version>` and exit. |
| `--help` | Show help (also available on the `estimate` command). |

## `estimate BRIEF`

Read a Markdown brief and print a draft estimate.

| Option | Default | Effect |
| --- | --- | --- |
| `--format` / `-f` | `markdown` | `markdown` or `csv`. |
| `--output` / `-o` | stdout | Write UTF-8 file instead of stdout. |
| `--rules PATH` | packaged `rules.toml` | Alternate rules file. |
| `--skip-review` | off | Skip interactive review; output stays unreviewed. |

Exit codes: `0` success, `1` no tasks found or every task dropped in review, `2` usage error or review required without a TTY. Quitting the review with Ctrl-C or end of input aborts without writing any output.

The brief file may start with a UTF-8 byte order mark.

Environment for the optional LLM path: see the configuration table in the README.
