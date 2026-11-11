# Prompt pack v1

Used when `ESTIMATE_KIT_LLM=1`. The CLI loads `system.md` and `user.md` from this directory.

- `{{brief}}` in `user.md` is replaced with the parsed brief rendered as Markdown.
- Bump the folder name (`v2`, …) when the contract changes; keep old packs so past runs stay reproducible.
