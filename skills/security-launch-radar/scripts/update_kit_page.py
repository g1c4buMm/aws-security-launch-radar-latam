#!/usr/bin/env python3
"""Refresh the "This week on the radar" block of the kit page (index.html).

    python3 SKILL_DIR/scripts/update_kit_page.py --radar out/radar.json --items out/items.json \
        --config radar.config.json --page index.html

Replaces everything between <!-- radar:latest:start --> and <!-- radar:latest:end -->
with the week's headline and highlights. Titles, dates and links come from items.json;
the headline and "why it matters" come from the validated radar. Standard library only.
"""
import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path

START, END = "<!-- radar:latest:start -->", "<!-- radar:latest:end -->"
PRIORITY = {"high": "Act this week", "medium": "Plan this quarter", "low": "Good to track"}
LANG = {"en": "en", "pt-BR": "pt-BR", "es": "es"}
DASHES = re.compile(r"\s*[–—]\s*")


def esc(s):
    return html.escape(DASHES.sub(", ", str(s or "")), quote=True)


def block(radar, items, language, tracker_url):
    by_id = {it["id"]: it for it in items}
    rows = [(h, by_id[h["item_id"]]) for h in radar.get("highlights", []) if h.get("item_id") in by_id]
    dates = sorted(it["date"] for it in items if it.get("date"))
    end = dt.date.fromisoformat(dates[-1]) if dates else dt.date.today()
    week = end.isocalendar()[1]
    span = "%s to %s" % (dates[0], dates[-1]) if dates else ""
    lis = "\n".join(
        ' <li><span class="prio p-%s">%s</span> <a href="%s">%s</a><p lang="%s">%s</p></li>'
        % (esc(h.get("priority", "medium")), esc(PRIORITY.get(h.get("priority"), "Plan this quarter")),
           esc(it["link"]), esc(it["title"]), LANG.get(language, "en"), esc(h.get("why_it_matters", "")))
        for h, it in rows)
    more = ' <a class="btn" href="%s">All launches on the tracker</a>' % esc(tracker_url) if tracker_url else ""
    return """%s
<section id="latest" aria-labelledby="latest-t"><div class="wrap">
<p class="eyebrow">This week on the radar · W%d · %s</p>
<h2 id="latest-t" lang="%s">%s</h2>
<ol class="latest">
%s
</ol>
<div class="ctas"><a class="btn primary" href="examples/email-en.html">See a full email</a>%s</div>
</div></section>
%s""" % (START, week, esc(span), LANG.get(language, "en"), esc(radar.get("headline", "")), lis, more, END)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--radar", default="out/radar.json")
    ap.add_argument("--items", default="out/items.json")
    ap.add_argument("--config", default="radar.config.json")
    ap.add_argument("--page", default="index.html")
    args = ap.parse_args()
    radar = json.loads(Path(args.radar).read_text(encoding="utf-8"))
    data = json.loads(Path(args.items).read_text(encoding="utf-8"))
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8")) if Path(args.config).exists() else {}
    page = Path(args.page)
    text = page.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("%s has no %s ... %s markers" % (args.page, START, END))
    new = block(radar, data.get("items", data), cfg.get("language", "en"), cfg.get("tracker", {}).get("site_url", ""))
    text = text[:text.index(START)] + new + text[text.index(END) + len(END):]
    page.write_text(text, encoding="utf-8")
    print("kit page: %d highlights written to %s" % (len(radar.get("highlights", [])), args.page))


if __name__ == "__main__":
    main()
