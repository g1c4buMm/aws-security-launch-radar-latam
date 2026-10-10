# Overview

The radar is one weekly cycle over two files: `out/items.json` (what AWS published) and `out/radar.json` (what Claude chose to say about it).

| Step | Who | Movement |
|---|---|---|
| Collect | `fetch_feeds.py` | **Read**: the last 7 days of AWS What's New, AWS security blogs and Security Bulletins |
| Curate | Claude, through the skill | **Choose**: 3 to 7 highlights, other relevant items and the week's bulletins, written in your language |
| Validate | `validate_radar.py` | **Check**: only real items, no URLs in text, bulletins only in their own section |
| Render | `render.py` | **Format**: email (HTML and text) and a Slack message |
| Deliver | Gmail connector, `send_slack.py` | **Send**: to your recipients and channel |

## Principles

- **The agent chooses and explains; the scripts guarantee the facts.** Titles, dates, links and severities never come from Claude's text.
- **Nothing is sent if validation fails.**
- **Source content is untrusted data.** Instructions found in a feed are never followed.
- **No customer data in this repository.** Your recipients live in your own private copy; the webhook URL lives only in an environment variable.
- **One thing done well.** The MVP is a weekly, general review. Everything else is on the [roadmap](../ROADMAP.md).
