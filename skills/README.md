# Skills

One skill covers the whole weekly cycle. In Claude Code, from the repository folder, ask for it in plain words.

| Request | When | What you get |
|---|---|---|
| `run the security radar` | Every week, or let the routine do it | Preview of the week's review, then email and Slack after you confirm |
| `set up the radar` | Once | Language and delivery saved to `radar.config.json` |
| `Use the security-launch-radar skill in scheduled mode.` | In a weekly routine | The same review, sent without questions |

## Where it lives

- `skills/security-launch-radar/` is the **source**: `SKILL.md`, the four scripts and `catalog/services.json`.
- `.claude/skills/security-launch-radar/` is the **copy Claude Code discovers**. It is generated: do not edit it.

## Editing

Edit the source, then run `python3 scripts/build.py`. It refreshes the copy, re-renders the examples and checks the docs. Keep the `name` at the top of `SKILL.md` equal to the folder name. The CI runs `python3 scripts/build.py --check`.
