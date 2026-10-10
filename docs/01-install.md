# Install

About 15 minutes, once. The [README](../README.md#getting-started) has the same steps with screenshots.

## Requirements

| Requirement | Why | Check |
|---|---|---|
| Claude Code, signed in with your Claude account | Runs the skill | `claude --version` |
| Python 3.9 or later, standard library only | Runs the scripts | `python3 --version` |
| Gmail connected to your Claude account | Sends the email from your Gmail address | step 3 |
| A Slack workspace where you can add apps (optional) | Posts to a channel | step 4 |
| Outbound HTTPS to `aws.amazon.com` and `hooks.slack.com` | Reads the sources, posts to Slack | step 2 |

## 1. Get the code

On GitHub, choose **Use this template › Create a new repository** and set it to **Private** (a fork of a public repository is always public). Then clone it. The weekly routine clones this copy, so your settings must live there.

```
git clone https://github.com/<your-user>/aws-security-launch-radar-latam.git
cd aws-security-launch-radar-latam
```

Claude Code discovers the skill in `.claude/skills/security-launch-radar/` when you start it from this folder.

## 2. Check that the sources are reachable

```
python3 .claude/skills/security-launch-radar/scripts/fetch_feeds.py
```

You should see one line like the one in `examples/fetch-output.txt`. An `ERROR` line means a source could not be reached: check your proxy or firewall.

## 3. Connect Gmail

Open [claude.ai/customize/connectors](https://claude.ai/customize/connectors), connect **Gmail** and approve the permissions with the account that should send the radar. Claude Code and the scheduled routine use the same connector.

## 4. Create a Slack webhook (optional)

1. At [api.slack.com/apps](https://api.slack.com/apps), choose **Create New App**, then **From scratch**, and pick your workspace.
2. Open **Incoming Webhooks**, turn it on, choose **Add New Webhook to Workspace** and pick the channel.
3. Export the URL in your shell. Never put it in a file:

```
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## 5. Choose the language and recipients

```
python3 setup.py
```

Details in [05-configuration.md](05-configuration.md). Commit `radar.config.json` to your private copy.

## 6. First run and schedule

See [02-flow.md](02-flow.md) for the first run and [03-claude-code-features.md](03-claude-code-features.md) for the weekly routine.
