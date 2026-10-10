# Roadmap

The MVP (v0.1) ships one thing well: a **weekly review of AWS security news**, in English, Portuguese or Spanish, delivered by email and Slack. Everything below was prototyped before the MVP was cut, so most items are about hardening, testing and review rather than building from zero.

Dates are targets for a single maintainer working part time. Items that depend on an external review (open source, legal) say so, because those reviews set the pace, not the code.

## v0.1 · MVP: weekly security review

| Date | Milestone |
|---|---|
| Oct 7 to Oct 16, 2026 | Hardening: unit tests for the four scripts, sample outputs in `docs/`, setup tested in the three languages |
| Oct 12 to Nov 9, 2026 | Private pilot: five Monday editions (Oct 12, 19, 26, Nov 2, Nov 9) sent to a small group, at least one reader per language |
| Nov 10, 2026 | Feedback from the pilot applied; submit for open source review |
| Week of Dec 7, 2026 | Target publication. **Depends on the open source review**; estimated at four weeks |

Exit criteria: five pilot editions sent with no validation failures reaching readers, and no broken links.

## v0.1.1 · Bulletin archive (Nov 16, 2026)

AWS only publishes the last ~30 days of Security Bulletins. Each weekly run will store the bulletins it saw in a local archive. **Starting this early matters**: a complete 2027 year-to-date view (v0.2) is only possible if the archive starts in 2026.

## v0.2 · Periods and trends (Jan 29, 2027)

- Monthly, quarterly, year to date, previous month or quarter, and custom dates.
- "Period in numbers" section: counts by source, service type and month.
- Up to four trends per report; the validator blocks any number that is not in the computed stats.
- Partial coverage warning when a source does not reach the start of the period.

## v0.2.1 · Kiro support (Feb 26, 2027)

- Run the same radar from Kiro, in addition to Claude Code.
- Move the scripts and agent instructions into an agent-neutral core, with a thin adapter per tool. The scripts are already plain Python, so most of the work is packaging.
- **Depends on confirming** how Kiro packages agent instructions and how it would schedule a weekly run.

## v0.3 · Personalization (Mar 12, 2027)

- Reader personas: CISO, security engineer, DPO, cloud architect, founder, each with its own focus, tone and number of highlights.
- Company profile: AWS services in use, used to rank items.
- Filters by service (39 in the catalog), by security domain (identity, detection, vulnerabilities, data protection, network, governance, AI security) and by official AWS category.
- "Affects you" flag in the CVE section when the bulletin touches a service in the profile.
- Shortlist script that ranks candidates, so long periods do not overload the agent.

## v0.4 · Brazil regulatory mapping (May 14, 2027)

- Each highlight mapped to controls from LGPD, CMN Resolution 4,893 / BCB Resolution 85 and PCI DSS v4.0, chosen only from a closed catalog.
- **LATAM Spotlight** section: the item with the highest regional regulatory impact.
- **Depends on legal and compliance review of the catalog.** Review starts Feb 1, 2027; estimated at six to eight weeks.

## v0.5 · Spanish-speaking LATAM and auto-discovery (Jul 30, 2027)

- Regulatory catalogs for Mexico, Colombia and Chile. Scope to be confirmed with local legal reviewers.
- Opt-in, read-only discovery of the AWS services an account actually uses (AWS Config or Resource Explorer), replacing the manual list.
- Slack delivery through a connector as an alternative to webhooks.

## Not planned

- Sending anything outside the customer's own email and Slack.
- Storing customer data outside the customer's repository and account.
