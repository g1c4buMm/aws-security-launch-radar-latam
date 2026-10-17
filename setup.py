#!/usr/bin/env python3
"""Deploy-time setup: choose the report language and where to deliver it.

Writes radar.config.json. Run interactively or with flags:
  python3 setup.py
  python3 setup.py --language es --email sec@example.com,cto@example.com --slack
  python3 setup.py --language pt-BR --tracker ../aws-security-tracker
"""
import argparse
import json
import os
import re

LANGUAGES = {"1": "en", "2": "pt-BR", "3": "es"}
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONFIG = "radar.config.json"


def ask(prompt, default=""):
    value = input("%s%s: " % (prompt, " [%s]" % default if default else "")).strip()
    return value or default


def parse_emails(raw):
    emails = [x.strip() for x in raw.split(",") if x.strip()]
    bad = [x for x in emails if not EMAIL.match(x)]
    if bad:
        raise SystemExit("invalid email(s): %s" % ", ".join(bad))
    return emails


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--language", choices=sorted(LANGUAGES.values()))
    ap.add_argument("--email", help="comma-separated recipients")
    ap.add_argument("--slack", action="store_true", help="also post to Slack (webhook from SLACK_WEBHOOK_URL)")
    ap.add_argument("--tracker", metavar="PATH", help="local clone of your aws-security-tracker site; each run adds the week and pushes it")
    args = ap.parse_args()

    if args.language:
        language, emails, slack = args.language, parse_emails(args.email or ""), args.slack
    else:
        print("AWS Security Weekly Radar setup\n")
        choice = ask("Report language: 1) English  2) Português (Brasil)  3) Español", "1")
        if choice not in LANGUAGES:
            raise SystemExit("choose 1, 2 or 3")
        language = LANGUAGES[choice]
        emails = parse_emails(ask("Email recipients (comma-separated, empty to skip)"))
        slack = ask("Post to Slack too? (y/n)", "n").lower().startswith("y")
        args.tracker = ask("Path to your aws-security-tracker clone (empty to skip)")

    config = {
        "language": language,
        "delivery": {
            "email": {"enabled": bool(emails), "to": emails},
            "slack": {"enabled": slack, "webhook_env": "SLACK_WEBHOOK_URL"},
        },
        "tracker": {"enabled": bool(args.tracker), "repo_path": args.tracker or "../aws-security-tracker"},
    }
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print("\nSaved %s: language=%s, email=%s, slack=%s, tracker=%s" % (CONFIG, language, ", ".join(emails) or "off", "on" if slack else "off", args.tracker or "off"))
    if args.tracker and not os.path.exists(os.path.join(args.tracker, "scripts", "deploy.sh")):
        print("Warning: %s has no scripts/deploy.sh; clone your aws-security-tracker repository there" % args.tracker)
    if slack:
        print("Set the webhook as an environment variable (never in a file): export SLACK_WEBHOOK_URL=https://hooks.slack.com/...")
    print("Run it now in Claude Code:   run the security radar")
    print("Schedule it weekly (routine prompt):   Use the security-launch-radar skill in scheduled mode.")


if __name__ == "__main__":
    main()
