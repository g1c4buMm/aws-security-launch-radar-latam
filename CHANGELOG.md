# Changelog

## 0.2.0 (2026-10-17)

- **Multi-agent curation**: three `radar-curator` subagents (threats, identity, data-network) curate in parallel and write `out/drafts/`; Claude merges them into `out/radar.json`.
- **Independent review**: the `radar-reviewer` subagent, which did not write the radar, checks every claim against the items and writes `out/review.json` before `validate_radar.py` runs.
- **Visible progress**: the skill prints one status line per step, so a run can be followed or recorded.
- Falls back to single-agent curation when subagents are not available.

## 0.1.0 (2026-10-10)

- **Weekly security review**: the last 7 days of AWS What's New, AWS security blogs and AWS Security Bulletins, curated by Claude Code through the `security-launch-radar` skill.
- **Three report languages**: English, Português (Brasil) or Español, chosen at setup with `setup.py`.
- **Email and Slack**: Gmail connector and Slack Incoming Webhook, with a preview and confirmation before sending; scheduled mode for weekly routines.
- **Validator**: blocks unknown items, URLs in text, unknown fields, bulletins outside the CVE section and missing new bulletins. Nothing is sent if it fails.
- **LinkedIn post** on every run: `out/linkedin.txt` and `out/linkedin.html` with copy buttons, Unicode bold headings, links for the first comment and automatic shortening to fit LinkedIn's limit. Works with no connector at all.
- **NEWS and BLOG tags** in highlights and "Also released"; **UPDATED** tag for older bulletins that AWS resurfaced.
- **Kit structure**: `skills/` as the single source, `scripts/build.py` with `--check` in CI, `docs/`, `examples/`, `templates/`, `demo/`, site in `index.html`.
- Prototype features (periods, personas, filters, regulatory mapping) moved to the [roadmap](ROADMAP.md).
