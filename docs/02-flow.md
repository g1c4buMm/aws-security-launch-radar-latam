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
| 3 | Curate | Three `radar-curator` subagents, in parallel: threats, identity, data-network | `out/drafts/*.json` |
| 4 | Merge | Claude joins the drafts into the radar in your language, citing items only by ID | `out/radar.json` |
| 5 | Review | The `radar-reviewer` subagent checks the radar against the items; Claude applies its fixes | `out/review.json` |
| 6 | Validate | `validate_radar.py` checks the radar; on failure Claude fixes it, up to 3 attempts | |
| 7 | Render | `render.py` formats the email, the Slack message and a LinkedIn post | `out/email.html`, `out/email.txt`, `out/slack.json`, `out/linkedin.txt`, `out/linkedin.html` |
| 8 | Preview | Claude shows the result and **asks before sending** | |
| 9 | Deliver | Gmail connector sends the email; `send_slack.py` posts to Slack | |
| 10 | Publish | `export_tracker.py` writes the week in the tracker format; `deploy.sh` merges, commits and pushes it to your tracker site (only with `tracker.enabled`, asks before pushing) | `out/tracker-week.json`, `data/weeks/wNN.json` |
| 11 | Summary | Week covered, items read, what was sent, launches added to the site and any failure | |

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

## The tracker site

If you also keep an [AWS Security Launch Tracker](https://github.com/g1c4buMm/aws-security-tracker) site, the radar can feed it every week. `export_tracker.py` takes only What's New launches from `out/items.json` and writes one line per launch: date, official title, official link, pillar (`threat`, `identity`, `posture`, `network`, `data`, `ai`, from the catalog domain), service and the first sentence of the official summary. Nothing in it is written by the model. The tracker's own `add_week.py` skips launches that are already on the site, so running the radar twice in a week is safe.

The push uses your own git credentials. In a routine, add the tracker repository to the routine's repositories and set `tracker.repo_path` to where it is cloned.

## Scheduled mode

A routine runs the same steps with the prompt `Use the security-launch-radar skill in scheduled mode.` It never asks questions: if something is missing, it generates the files, does not send, and explains why in the run summary.
