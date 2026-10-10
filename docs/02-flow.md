# The weekly flow

Start Claude Code in the repository folder and ask:

```
claude
> run the security radar
```

| # | Step | What happens | File |
|---|---|---|---|
| 1 | Config | Claude reads the language and delivery settings | `radar.config.json` |
| 2 | Collect | `fetch_feeds.py` reads the last 7 days | `out/items.json` |
| 3 | Curate | Claude writes the radar in your language, citing items only by ID | `out/radar.json` |
| 4 | Validate | `validate_radar.py` checks the radar; on failure Claude fixes it, up to 3 attempts | |
| 5 | Render | `render.py` formats the email, the Slack message and a LinkedIn post | `out/email.html`, `out/email.txt`, `out/slack.json`, `out/linkedin.txt`, `out/linkedin.html` |
| 6 | Preview | Claude shows the result and **asks before sending** | |
| 7 | Deliver | Gmail connector sends the email; `send_slack.py` posts to Slack | |
| 8 | Summary | Week covered, items read, what was sent and any failure | |

Open `out/email.html` in a browser to see the email exactly as it will arrive.

## What goes where in the report

| Section | Source | Rule |
|---|---|---|
| Highlights | What's New (**NEWS**) and security blogs (**BLOG**) | 3 to 7, each with priority, why it matters and an action |
| Also released | Same sources, split into News and Blog posts | Up to 10 |
| Good to know: CVEs and security bulletins | Security Bulletins only | Every **new** bulletin; updates to older bulletins only when relevant, tagged **UPDATED** |

## The LinkedIn post

Every run also writes a post to copy and paste, with or without connectors:

- `out/linkedin.html`: preview with a character counter, a **Copy post** button and a **Copy links for the first comment** button.
- `out/linkedin.txt`: the same post as plain text.

Structure: title and week, headline, highlights (bold title and why it matters), new CVEs, a count of what else was released, the closing question and hashtags. Headings use Unicode bold, because LinkedIn has no markdown. Accented letters stay regular, since Unicode bold has no accented forms. Links go in the first comment, not in the body. If the post does not fit in 2,900 characters, `render.py` shortens it in this order: why it matters to its first sentence, at most three CVEs, no action lines, at most four highlights.

## New versus updated bulletins

The bulletins feed dates each item by its last update, so AWS can resurface old bulletins with a new date. Bulletin IDs are sequential: `fetch_feeds.py` marks a bulletin as new only if its number is higher than every bulletin dated before the week. The others are marked `"updated": true`.

## Scheduled mode

A routine runs the same steps with the prompt `Use the security-launch-radar skill in scheduled mode.` It never asks questions: if something is missing, it generates the files, does not send, and explains why in the run summary.
