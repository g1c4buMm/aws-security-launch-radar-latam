# Security policy

The AWS Security Weekly Radar is an independent open kit, not affiliated with or endorsed by Amazon Web Services: a Claude Code skill, four Python scripts and templates. It has no server, database or account of its own. Each team runs it from its own private copy, with its own Claude account, Gmail connector and Slack webhook. Even so, an agent that reads public feeds can be manipulated or leak data, and that is what this policy covers.

## Supported versions

| Version | Support |
|---|---|
| 0.1.x | ✅ Receives security fixes |

## Reporting a vulnerability

**Do not open a public issue.** Use GitHub's private channel:

1. Go to [Security › Advisories](https://github.com/g1c4buMm/aws-security-launch-radar-latam/security/advisories/new) and choose **Report a vulnerability**.
2. Describe the problem, the version, the script or skill step affected and the steps to reproduce.

**Use fictional data**: never send real recipients, webhook URLs or internal documents. The `examples/` folder has a ready snapshot for reproductions.

## Scope

**In scope:**

- **Prompt injection:** feed content that makes the skill follow embedded instructions, send to other recipients, skip validation or change delivery.
- **Validator bypass:** a `radar.json` that passes `validate_radar.py` but puts invented links, items or fields into the email or Slack message.
- **Rendering:** HTML or Slack markup injection from feed titles or Claude's text in `render.py`.
- **Secrets:** any path that writes the Slack webhook URL to disk, to logs or into the repository.
- **Build and CI:** code execution through `scripts/build.py` or the workflow, or personal data entering the repository.

**Out of scope:**

- The security of AWS, Claude, Claude Code, Gmail, Slack or GitHub. Report those to their owners. For AWS services, use the [AWS vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/).
- Inaccurate summaries that do not break a rule above. Always confirm details in the linked AWS source.

## Principles the kit follows

- **The agent chooses; the scripts guarantee the facts.** Links and titles never come from the agent's text.
- **Nothing is sent if validation fails.**
- **Source content is untrusted data.**
- **Secrets only in environment variables.**
- **No personal data in the repository.** The CI rejects email addresses outside the fictional domains used in the examples.

## If you use the kit

- Keep your copy of the repository **private**; `radar.config.json` holds your recipients.
- Rotate the Slack webhook if it was ever pasted into a chat, file or ticket.
- Review the first runs in interactive mode before turning on the weekly routine.
