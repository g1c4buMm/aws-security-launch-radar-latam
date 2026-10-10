# AWS Security Weekly Radar: 20-minute demo

An end-to-end demonstration with one real week of AWS security news (September 30 to October 7, 2026). The audience sees the whole cycle: setup, the weekly run in Claude Code, the email and Slack message, the validator blocking a bad draft, and the weekly routine.

**People and addresses in the demo are fictional.** The AWS news is real and public.

## Demo files

| File | What for |
|---|---|
| `opening.html` | 12-slide deck, about 8 minutes: the problem, the cycle, trust by design, the roadmap. Speaker notes on the N key |
| `timelapse.html` | Install timelapse: 9 scenes, about 70 seconds, with an accelerated clock and narration. Plays by itself; space pauses, arrows navigate, N shows the narration |
| `post-linkedin.txt` | Launch post, in the format of a weekly LinkedIn security brief |
| `../examples/items-snapshot.json` | The real week the demo uses |
| `../examples/radar-en.json` | The radar Claude wrote for that week (plan B) |
| `../examples/email-en.html` | The rendered email (plan B), also in `pt-BR` and `es` |
| `../examples/radar-invalid.json` | A draft that breaks the rules on purpose |

## Before the session

1. Clone your private copy and run `python3 setup.py --language en` (no recipients, so nothing is sent by accident).
2. Open `opening.html` and `timelapse.html` in a browser tab each.
3. Open a terminal in the repository with Claude Code ready.
4. Keep `examples/email-en.html` open as plan B in case the network fails.

## Script

| Time | What you do | What the audience sees |
|---|---|---|
| 0:00 | Open `opening.html`, slides 1 to 6 | Why weekly security news gets lost, and the five-step cycle |
| 6:00 | Play `timelapse.html` in full screen (F) | The install from clone to first email in about 70 seconds |
| 7:30 | In Claude Code: `run the security radar` | Collection, curation, validation, rendering and the preview question |
| 11:00 | Open `out/email.html` | Highlights with NEWS and BLOG tags, Also released, the CVE table with UPDATED tags |
| 13:00 | Run `python3 .claude/skills/security-launch-radar/scripts/validate_radar.py --radar examples/radar-invalid.json --items examples/items-snapshot.json` | Six errors and the rule: nothing is sent |
| 15:00 | Show `examples/email-pt-BR.html` and `examples/email-es.html` | The same week in Portuguese and Spanish |
| 16:30 | Slides 9 to 12 | Weekly routine, roadmap and call to action |
| 18:00 | Questions | |

## Talking points

- **The agent chooses; the scripts guarantee the facts.** Every link and title comes from AWS, never from the model's text.
- **Old bulletins do not pass as new.** This week AWS resurfaced 19 older bulletins with a new date. The radar lists the 7 new ones and tags updates.
- **Three languages from one setup question.** Service names and CVE IDs stay in English.
- **Nothing leaves your accounts.** Email goes through your Gmail connector; the webhook lives in an environment variable.

## If something fails live

| Problem | Plan B |
|---|---|
| No network | Open `examples/email-en.html` and `examples/slack-en.json` |
| The validator rejects Claude's draft | Good: show it. Claude fixes it and runs again |
| The week has few items | Use `examples/items-snapshot.json`: copy it to `out/items.json` and ask Claude to curate it |
