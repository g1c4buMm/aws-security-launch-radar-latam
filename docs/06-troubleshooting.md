# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| The skill does not load | Claude Code was started outside the repository folder | `cd` into the repository and start `claude` again |
| `fetch_feeds.py` exits with code 2 | No security items, or every source failed | Read the `ERROR` lines; check proxy and firewall |
| `INVALID RADAR` three times | Claude's draft broke a rule repeatedly | Read the listed errors; nothing was sent. Run again |
| "No connector" for email | Gmail is not connected to this Claude account | Connect it at claude.ai/customize/connectors |
| `SLACK_WEBHOOK_URL is missing` | The variable is not set where Claude Code runs | Export it in your shell, or set it in the routine's environment |
| Old bulletins appear as new | The feed resurfaced them with a new date | They should show as **UPDATED**; if not, open an issue with the bulletin ID |
| The routine did not send | Missing config, connector or variable in the cloud environment | Read the run summary at claude.ai/code/routines |
| CI fails with "out of date" | A source changed without a rebuild | Run `python3 scripts/build.py` and commit |
