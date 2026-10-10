# Claude Code features used

| Feature | Used for | Where |
|---|---|---|
| **Project skills** | Claude Code loads the radar instructions when you ask for the radar | `.claude/skills/security-launch-radar/SKILL.md` |
| **Bash tool** | Running the four scripts | `skills/security-launch-radar/scripts/` |
| **Gmail connector** | Sending the email from your Gmail address | [claude.ai/customize/connectors](https://claude.ai/customize/connectors) |
| **Routines** | Running the radar every Monday in the cloud | `/schedule` or [claude.ai/code/routines](https://claude.ai/code/routines) |

## Skill source and generated copy

The source of the skill is `skills/security-launch-radar/`. `python3 scripts/build.py` copies it to `.claude/skills/`, where Claude Code finds it. Edit the source, never the copy; the CI fails if they differ.

## Creating the weekly routine

1. Push your private copy, with `radar.config.json`, to GitHub.
2. In Claude Code, run `/schedule` and ask for a weekly routine on that repository with this prompt:

```
Use the security-launch-radar skill in scheduled mode.
```

3. Use a Monday cron in UTC, for example `0 11 * * 1` for 08:00 in São Paulo, and attach the Gmail connector.
4. For Slack, add `SLACK_WEBHOOK_URL` as an environment variable of the cloud environment the routine uses.

Review, pause or run it now at [claude.ai/code/routines](https://claude.ai/code/routines).
