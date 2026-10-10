#!/usr/bin/env python3
"""Collect the last 7 days of AWS security news and write items.json.

Sources:
  whats-new           AWS What's New API (falls back to RSS)
  security-blog       AWS blogs API, Security, Identity & Compliance category (falls back to RSS)
  security-bulletins  AWS Security Bulletins RSS

Standard library only. Source text is untrusted data: this script only
normalizes, truncates and classifies it by rule; nothing is interpreted.

Usage: python3 fetch_feeds.py --out out/items.json
"""
import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SERVICES_FILE = os.path.join(HERE, "..", "catalog", "services.json")

API = "https://aws.amazon.com/api/dirs/items/search"
WHATS_NEW_RSS = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
BLOG_RSS = "https://aws.amazon.com/blogs/security/feed/"
BULLETINS_RSS = "https://aws.amazon.com/security/security-bulletins/rss/feed/"
SECURITY_CATEGORY = "security-identity-and-compliance"
WINDOW_DAYS = 7
PAGE_SIZE = 200
MAX_PAGES = 5
MAX_SUMMARY = 600

# Wide net for security launches that come without the security category tag.
SECURITY_TERMS = re.compile(
    r"\b(security|secure|iam|identity|access control|encrypt\w*|kms|secrets?|certificate|"
    r"firewall|waf|ddos|guardduty|inspector|macie|detective|compliance|audit|cloudtrail|"
    r"vulnerab\w*|cve|patch|threat|malware|ransomware|zero trust|permission\w*|"
    r"guardrails?|least privilege|sso|mfa|passkey|tls|privatelink|sovereign\w*|"
    r"authori[sz]\w*|authenticat\w*|polic(?:y|ies)|consent|vpc endpoints?)\b",
    re.IGNORECASE,
)


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "aws-security-launch-radar-latam/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def parse_iso(value):
    return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


# ---------------- sources ----------------

def api_pages(params, date_field, start):
    """Page through the API newest first until we pass the start of the window."""
    for page in range(MAX_PAGES):
        q = dict(params, size=PAGE_SIZE, page=page, sort_order="desc")
        batch = json.loads(get(API + "?" + urllib.parse.urlencode(q))).get("items", [])
        for x in batch:
            yield x
        if len(batch) < PAGE_SIZE:
            return
        last = batch[-1]["item"]["additionalFields"].get(date_field)
        if last and parse_iso(last) < start:
            return


def fetch_whats_new(start, end):
    out = []
    params = {"item.directoryId": "whats-new-v2", "item.locale": "en_US",
              "sort_by": "item.additionalFields.postDateTime"}
    for x in api_pages(params, "postDateTime", start):
        f = x["item"]["additionalFields"]
        if not f.get("postDateTime") or not f.get("headlineUrl"):
            continue
        date = parse_iso(f["postDateTime"])
        if not start <= date < end:
            continue
        tags = {}
        for t in x.get("tags", []):
            tags.setdefault(t.get("tagNamespaceId", "").split("#", 1)[-1], []).append(t.get("name", ""))
        out.append(dict(source="whats-new", title=clean(f.get("headline")), date=date,
                        link=urllib.parse.urljoin("https://aws.amazon.com", f["headlineUrl"]),
                        summary=clean(f.get("postBody")), product_tags=tags.get("general-products", []),
                        aws_categories=tags.get("marketing-marchitecture", [])))
    return out


def fetch_blog(start, end):
    out = []
    params = {"item.directoryId": "blog-posts", "item.locale": "en_US",
              "sort_by": "item.additionalFields.createdDate",
              "tags.id": "blog-posts#category#security-identity-compliance"}
    for x in api_pages(params, "createdDate", start):
        f = x["item"]["additionalFields"]
        if not f.get("createdDate") or not f.get("link"):
            continue
        date = parse_iso(f["createdDate"])
        if not start <= date < end:
            continue
        cats = [t.get("name", "") for t in x.get("tags", []) if t.get("tagNamespaceId") == "blog-posts#category"]
        out.append(dict(source="security-blog", title=clean(f.get("title")), link=f["link"], date=date,
                        summary=clean(f.get("postExcerpt")), product_tags=cats, aws_categories=[SECURITY_CATEGORY]))
    return out


def fetch_rss(source, url, start, end, keep_before=False):
    out = []
    for node in ET.fromstring(get(url)).iter("item"):
        try:
            date = parsedate_to_datetime(node.findtext("pubDate")).astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
        link = (node.findtext("link") or "").strip()
        if not link.startswith("https://aws.amazon.com/") or date >= end or (date < start and not keep_before):
            continue
        cats = []
        for c in node.findall("category"):
            cats.extend(p.strip() for p in (c.text or "").split(",") if p.strip())
        out.append(dict(source=source, title=clean(node.findtext("title")), link=link, date=date,
                        summary=clean(node.findtext("description")), product_tags=cats,
                        aws_categories=[SECURITY_CATEGORY] if source != "whats-new" else []))
    return out


BULLETIN_SEQ = re.compile(r"/(\d{4})-(\d{3})-aws/?$", re.IGNORECASE)


def fetch_bulletins(start, end):
    """Bulletins in the window, each flagged new or updated.

    The RSS date is the last update, so AWS can resurface old bulletins with a new
    date. Bulletin IDs are sequential: a bulletin is new only if its number is
    higher than every bulletin dated before the window.
    """
    items = fetch_rss("security-bulletins", BULLETINS_RSS, start, end, keep_before=True)

    def seq(it):
        m = BULLETIN_SEQ.search(it["link"])
        return (int(m.group(1)), int(m.group(2))) if m else None

    before = [seq(i) for i in items if i["date"] < start and seq(i)]
    threshold = max(before) if before else None
    out = []
    for it in items:
        if it["date"] < start:
            continue
        n = seq(it)
        it["updated"] = bool(threshold and n and n <= threshold)
        out.append(it)
    return out


# ---------------- classification ----------------

def load_services():
    with open(SERVICES_FILE, encoding="utf-8") as f:
        services = json.load(f)["services"]
    for s in services.values():
        s["_re"] = re.compile(s["keywords"], re.IGNORECASE)
    return services


def classify(it, services):
    """Mark security items. Mixed services (core=false) only count if the title talks security."""
    text = it["title"] + " " + it["summary"]
    tags = set(it["product_tags"])
    matched = [k for k, s in services.items() if tags.intersection(s["tags"]) or s["_re"].search(text)]
    core = [k for k in matched if services[k].get("core", True)]
    it["services"] = matched
    it["cve_ids"] = list(dict.fromkeys(re.findall(r"CVE-\d{4}-\d+", it["title"])))
    sev = re.search(r"Content Type:\s*([A-Za-z]+)", it["summary"]) if it["source"] == "security-bulletins" else None
    it["severity"] = sev.group(1) if sev else ""
    it["is_security"] = (it["source"] != "whats-new" or bool(core)
                         or SECURITY_CATEGORY in it["aws_categories"]
                         or bool(SECURITY_TERMS.search(it["title"])))


def collect(name, primary, fallback, errors):
    try:
        return primary()
    except Exception as exc:
        errors.append({"source": name, "error": "API: %s" % exc})
    try:
        return fallback()
    except Exception as exc:
        errors.append({"source": name, "error": "RSS: %s" % exc})
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="out/items.json")
    args = ap.parse_args()

    services = load_services()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=WINDOW_DAYS)
    errors = []
    raw = collect("whats-new", lambda: fetch_whats_new(start, end),
                  lambda: fetch_rss("whats-new", WHATS_NEW_RSS, start, end), errors)
    raw += collect("security-blog", lambda: fetch_blog(start, end),
                   lambda: fetch_rss("security-blog", BLOG_RSS, start, end), errors)
    try:
        raw += fetch_bulletins(start, end)
    except Exception as exc:
        errors.append({"source": "security-bulletins", "error": str(exc)})

    seen, items = set(), []
    for it in sorted(raw, key=lambda i: i["date"], reverse=True):
        it["id"] = hashlib.sha1(it["link"].encode()).hexdigest()[:8]
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        it["date"] = it["date"].strftime("%Y-%m-%d")
        it["summary"] = it["summary"][:MAX_SUMMARY]
        it["updated"] = it.get("updated", False)
        classify(it, services)
        if it["is_security"]:
            items.append(it)

    out = {
        "generated_at": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {"from": start.strftime("%Y-%m-%d"), "to": end.strftime("%Y-%m-%d")},
        "errors": errors,
        "stats": {"total": len(items), "by_source": dict(Counter(i["source"] for i in items)),
                  "cves": sum(1 for i in items if i["source"] == "security-bulletins"),
                  "bulletins_new": sum(1 for i in items if i["source"] == "security-bulletins" and not i["updated"]),
                  "bulletins_updated": sum(1 for i in items if i["updated"])},
        "items": [{k: it[k] for k in ("id", "source", "date", "title", "link", "services",
                                      "cve_ids", "severity", "updated", "summary")} for it in items],
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    st = out["stats"]
    print("week %s to %s | items: %d | by source: %s | bulletins: %d new, %d updated"
          % (out["window"]["from"], out["window"]["to"], len(items), st["by_source"], st["bulletins_new"], st["bulletins_updated"]))
    for e in errors:
        print("ERROR %s: %s" % (e["source"], e["error"]), file=sys.stderr)
    if not items:
        sys.exit(2)


if __name__ == "__main__":
    main()
