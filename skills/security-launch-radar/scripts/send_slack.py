#!/usr/bin/env python3
"""Post out/slack.json to a Slack Incoming Webhook.

The webhook URL comes from the environment variable named in the config
(default SLACK_WEBHOOK_URL) and is never written to a file.

Usage: python3 send_slack.py --payload out/slack.json --config radar.config.json [--dry-run]
"""
import argparse
import json
import os
import sys
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload", default="out/slack.json")
    ap.add_argument("--config", default="radar.config.json")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        env_name = json.load(f)["delivery"]["slack"].get("webhook_env", "SLACK_WEBHOOK_URL")
    with open(args.payload, "rb") as f:
        payload = f.read()

    url = os.environ.get(env_name, "")
    if args.dry_run:
        print("dry-run: %d bytes ready; %s %s" % (len(payload), env_name, "is set" if url else "is NOT set"))
        return
    if not url.startswith("https://hooks.slack.com/"):
        sys.exit("%s is missing or is not a Slack webhook" % env_name)

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
    if body.strip() != "ok":
        sys.exit("Slack replied: %s" % body)
    print("posted to Slack")


if __name__ == "__main__":
    main()
