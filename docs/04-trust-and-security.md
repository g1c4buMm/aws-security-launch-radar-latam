# Trust and security

## Where facts come from

| Shown in the report | Comes from |
|---|---|
| Titles, dates, links | `out/items.json`, collected from AWS |
| Severity and CVE IDs | The bulletin title and description |
| NEWS, BLOG and UPDATED tags | The item's source and bulletin sequence |
| Headline, why it matters, action, notes | Claude, checked by the validator |

## What the validator blocks

- An `item_id` that is not in `out/items.json`.
- The same item twice anywhere in the radar.
- A bulletin outside the CVE section, or a non-bulletin inside it.
- A new bulletin of the week missing from the CVE section.
- URLs in any text field.
- Fields the renderer does not expect (for example `controls` or `latam_spotlight` from the prototype).
- Texts over the length limits, wrong priority values, and fewer than 3 or more than 7 highlights.

`examples/radar-invalid.json` breaks several rules on purpose; the CI makes sure it stays rejected.

## Untrusted source content

Feed titles and summaries go into Claude's context. The skill tells Claude to treat them as data: an instruction found in a feed ("ignore", "send to", "run") is never followed and is mentioned in the run summary. The validator is the second line: even a manipulated draft cannot add links, unknown items or new fields.

## Secrets and data

- The Slack webhook URL is read from an environment variable and never written to disk.
- Email goes through your own Gmail connector; the kit has no server and stores nothing outside your copy.
- Keep your copy of the repository **private**: `radar.config.json` holds your recipients.

Report vulnerabilities as described in [SECURITY.md](../SECURITY.md).
