#!/usr/bin/env python3
"""Export the week's What's New launches in the format of the AWS Security Launch Tracker site.

    python3 SKILL_DIR/scripts/export_tracker.py --items out/items.json --radar out/radar.json \
        --config radar.config.json --out out/tracker-week.json --highlights-out out/tracker-highlights.json

Writes two files for the aws-security-tracker repository and prints the ISO week number:
- tracker-week.json -> data/weeks/wNN.json: a list of {d, t, u, p, s, x} (date, official
  title, official URL, pillar, service, one line from the official text). Facts only from
  items.json: nothing here is written by the model.
- tracker-highlights.json -> data/highlights/wNN.json: the validated radar highlights
  (headline, priority, why it matters, action) with title, date and link from items.json.
Standard library only.
"""
import argparse
import datetime as dt
import json
import re
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "catalog" / "services.json"
PILLAR = {
    "deteccao-resposta": "threat",
    "vulnerabilidades": "threat",
    "identidade-acesso": "identity",
    "governanca-compliance": "posture",
    "rede-perimetro": "network",
    "protecao-dados": "data",
    "seguranca-ia": "ai",
}
DASHES = re.compile(r"\s*[–—]\s*")


def first_sentence(text, limit=200):
    text = DASHES.sub(", ", " ".join((text or "").split()))
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    line = m.group(1) if m else text
    if len(line) > limit:
        line = line[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "."
    return line


def export(items, catalog):
    rows = []
    for it in items:
        if it.get("source") != "whats-new" or not str(it.get("link", "")).startswith("https://aws.amazon.com/"):
            continue
        services = [s for s in it.get("services") or [] if s in catalog]
        svc = catalog[services[0]] if services else None
        rows.append({
            "d": it["date"],
            "t": DASHES.sub(", ", it["title"]).strip(),
            "u": it["link"],
            "p": PILLAR.get(svc.get("domain"), "posture") if svc else "posture",
            "s": svc["name"] if svc else "AWS",
            "x": first_sentence(it.get("summary") or it["title"]),
        })
    rows.sort(key=lambda r: (r["d"], r["t"]))
    return rows


LANG = {"en": "en", "pt-BR": "pt", "es": "es"}


def highlights(radar, items, catalog, language, week):
    by_id = {it["id"]: it for it in items}
    out = []
    for h in radar.get("highlights", []):
        it = by_id.get(h["item_id"])
        if not it or not str(it.get("link", "")).startswith("https://aws.amazon.com/"):
            continue
        services = [s for s in it.get("services") or [] if s in catalog]
        svc = catalog[services[0]] if services else None
        out.append({
            "d": it["date"],
            "t": DASHES.sub(", ", it["title"]).strip(),
            "u": it["link"],
            "p": PILLAR.get(svc.get("domain"), "posture") if svc else "posture",
            "s": svc["name"] if svc else "AWS",
            "priority": h.get("priority", "medium"),
            "why": DASHES.sub(", ", h.get("why_it_matters", "")),
            "action": DASHES.sub(", ", h.get("action", "")),
        })
    return {"w": week, "lang": LANG.get(language, "en"), "headline": DASHES.sub(", ", radar.get("headline", "")), "items": out}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", default="out/items.json")
    ap.add_argument("--out", default="out/tracker-week.json")
    ap.add_argument("--radar", default="out/radar.json", help="validated radar; skipped if missing")
    ap.add_argument("--config", default="radar.config.json")
    ap.add_argument("--highlights-out", default="out/tracker-highlights.json")
    args = ap.parse_args()
    data = json.loads(Path(args.items).read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["services"]
    items = data.get("items", data)
    rows = export(items, catalog)
    Path(args.out).write_text("[\n" + ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n", encoding="utf-8")
    week = dt.date.fromisoformat(max(r["d"] for r in rows)).isocalendar()[1] if rows else 0
    print("tracker: %d launches, week w%02d, written to %s" % (len(rows), week, args.out))
    if Path(args.radar).exists() and week:
        cfg = Path(args.config)
        language = json.loads(cfg.read_text(encoding="utf-8")).get("language", "en") if cfg.exists() else "en"
        hl = highlights(json.loads(Path(args.radar).read_text(encoding="utf-8")), items, catalog, language, week)
        Path(args.highlights_out).write_text(json.dumps(hl, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("tracker: %d highlights (%s), written to %s" % (len(hl["items"]), hl["lang"], args.highlights_out))


if __name__ == "__main__":
    main()
