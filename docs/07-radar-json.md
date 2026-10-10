# radar.json and items.json

## out/items.json (written by `fetch_feeds.py`)

```json
{
 "generated_at": "2026-10-07T19:25:44Z",
 "window": {"from": "2026-09-30", "to": "2026-10-07"},
 "errors": [],
 "stats": {"total": 51, "by_source": {...}, "cves": 26, "bulletins_new": 7, "bulletins_updated": 19},
 "items": [
  {"id": "95de98e6", "source": "whats-new", "date": "2026-10-01", "title": "...", "link": "https://aws.amazon.com/...",
   "services": ["security-hub"], "cve_ids": [], "severity": "", "updated": false, "summary": "..."}
 ]
}
```

| Field | Meaning |
|---|---|
| `id` | First 8 characters of the SHA-1 of the link. Stable across runs |
| `source` | `whats-new`, `security-blog` or `security-bulletins` |
| `services` | Matches from `catalog/services.json` |
| `severity` | From the bulletin description; empty when AWS publishes none |
| `updated` | Bulletins only: `true` when an older bulletin was resurfaced this week |

## out/radar.json (written by Claude)

```json
{
 "headline": "One sentence with the main message of the week",
 "highlights": [
  {"item_id": "95de98e6", "priority": "medium", "why_it_matters": "...", "action": "..."}
 ],
 "also_noted": ["8aa5a39c"],
 "cves": [{"item_id": "4a93b9f8", "note": "Optional, up to 200 characters."}]
}
```

| Field | Rule |
|---|---|
| `headline` | Up to 200 characters |
| `highlights` | 3 to 7; `whats-new` or `security-blog` items; `priority` is `high`, `medium` or `low` |
| `why_it_matters` / `action` | Up to 450 and 280 characters |
| `also_noted` | Up to 10 IDs; no bulletins |
| `cves` | Up to 15; bulletins only; every new bulletin must be listed |
| `question` | Optional, up to 200 characters; the closing question of the LinkedIn post |

No other fields are accepted. No text field may contain a URL or an em dash. A blank skeleton is in `templates/radar.json`; full examples are `examples/radar-en.json`, `examples/radar-pt-BR.json` and `examples/radar-es.json`.
