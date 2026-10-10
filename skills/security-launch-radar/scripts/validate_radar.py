#!/usr/bin/env python3
"""Validate the radar.json written by the agent before anything is sent.

Guarantees the agent only cites items that came from the sources, keeps
security bulletins in their own section, and writes no URLs or unknown
fields. Exits with code 1 on any error.

Usage: python3 validate_radar.py --radar out/radar.json --items out/items.json
"""
import argparse
import json
import re
import sys

PRIORITIES = {"high", "medium", "low"}
URL = re.compile(r"https?://|www\.", re.IGNORECASE)
LIMITS = {"headline": 200, "why_it_matters": 450, "action": 280, "note": 200, "question": 200}
BULLETINS = "security-bulletins"
MIN_HIGHLIGHTS, MAX_HIGHLIGHTS, MAX_ALSO, MAX_CVES = 3, 7, 10, 15
TOP_KEYS = {"headline", "highlights", "also_noted", "cves", "question"}
HIGHLIGHT_KEYS = {"item_id", "priority", "why_it_matters", "action"}
CVE_KEYS = {"item_id", "note"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_text(errors, where, field, value):
    if not isinstance(value, str) or not value.strip():
        errors.append("%s: '%s' is empty" % (where, field))
        return
    if len(value) > LIMITS[field]:
        errors.append("%s: '%s' has %d characters (max %d)" % (where, field, len(value), LIMITS[field]))
    if URL.search(value):
        errors.append("%s: '%s' contains a URL; links come only from items.json" % (where, field))
    if "\u2014" in value:
        errors.append("%s: '%s' contains an em dash" % (where, field))


def check_keys(errors, where, obj, allowed):
    extra = set(obj) - allowed
    if extra:
        errors.append("%s: unknown fields %s" % (where, sorted(extra)))


def validate(radar, items):
    errors = []
    source = {i["id"]: i["source"] for i in items["items"]}
    used = set()

    def check_ref(where, item_id, bulletin):
        """bulletin=True accepts only security bulletins; False rejects them. Nothing appears twice."""
        if item_id not in source:
            errors.append("%s: item_id '%s' not in items.json" % (where, item_id))
        elif bulletin and source[item_id] != BULLETINS:
            errors.append("%s: '%s' is not a security bulletin" % (where, item_id))
        elif not bulletin and source[item_id] == BULLETINS:
            errors.append("%s: '%s' is a bulletin; bulletins go only in 'cves'" % (where, item_id))
        if item_id in used:
            errors.append("%s: item_id '%s' repeated" % (where, item_id))
        used.add(item_id)

    check_keys(errors, "radar", radar, TOP_KEYS)
    check_text(errors, "radar", "headline", radar.get("headline"))
    if radar.get("question") is not None:
        check_text(errors, "radar", "question", radar["question"])

    hl = radar.get("highlights") or []
    if not MIN_HIGHLIGHTS <= len(hl) <= MAX_HIGHLIGHTS:
        errors.append("highlights: %d items (expected %d to %d)" % (len(hl), MIN_HIGHLIGHTS, MAX_HIGHLIGHTS))
    for n, h in enumerate(hl, 1):
        where = "highlights[%d]" % n
        check_keys(errors, where, h, HIGHLIGHT_KEYS)
        check_ref(where, h.get("item_id"), bulletin=False)
        check_text(errors, where, "why_it_matters", h.get("why_it_matters"))
        check_text(errors, where, "action", h.get("action"))
        if h.get("priority") not in PRIORITIES:
            errors.append("%s: priority must be one of %s" % (where, sorted(PRIORITIES)))

    also = radar.get("also_noted") or []
    if len(also) > MAX_ALSO:
        errors.append("also_noted: max %d items" % MAX_ALSO)
    for item_id in also:
        check_ref("also_noted", item_id, bulletin=False)

    cves = radar.get("cves") or []
    if len(cves) > MAX_CVES:
        errors.append("cves: max %d items" % MAX_CVES)
    for n, c in enumerate(cves, 1):
        where = "cves[%d]" % n
        if not isinstance(c, dict):
            errors.append('%s: use {"item_id": ..., "note": ...}' % where)
            continue
        check_keys(errors, where, c, CVE_KEYS)
        check_ref(where, c.get("item_id"), bulletin=True)
        if c.get("note") is not None:
            check_text(errors, where, "note", c["note"])
    listed = {c.get("item_id") for c in cves if isinstance(c, dict)}
    new = [i["id"] for i in items["items"] if i["source"] == BULLETINS and not i.get("updated")]
    missing = [i for i in new if i not in listed]
    if missing and len(cves) < MAX_CVES:
        errors.append("cves: new bulletins missing: %s (every new bulletin must be listed)" % ", ".join(missing))
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radar", default="out/radar.json")
    ap.add_argument("--items", default="out/items.json")
    args = ap.parse_args()

    errors = validate(load(args.radar), load(args.items))
    if errors:
        print("INVALID RADAR (%d errors):" % len(errors))
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("radar valid")


if __name__ == "__main__":
    main()
