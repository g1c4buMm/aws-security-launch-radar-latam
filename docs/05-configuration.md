# Configuration

Everything you choose at setup lives in `radar.config.json`.

```
python3 setup.py
```

The setup asks three questions: report language, email recipients and whether to post to Slack. Or pass everything at once:

```
python3 setup.py --language es --email security@example.com,ciso@example.com --slack
```

| Language | `--language` | Report title |
|---|---|---|
| English | `en` | AWS Security Weekly Radar |
| Português (Brasil) | `pt-BR` | Radar Semanal de Segurança AWS |
| Español | `es` | Radar Semanal de Seguridad AWS |

The whole report arrives in the chosen language: section titles, priorities, tags and Claude's texts. AWS service names and CVE IDs stay in English.

## The file

```json
{
 "language": "pt-BR",
 "delivery": {
  "email": {"enabled": true, "to": ["security@example.com"]},
  "slack": {"enabled": true, "webhook_env": "SLACK_WEBHOOK_URL"}
 }
}
```

| Field | Meaning |
|---|---|
| `language` | `en`, `pt-BR` or `es` |
| `delivery.email.enabled` / `to` | Send by email, and to whom |
| `delivery.slack.enabled` | Post to Slack |
| `delivery.slack.webhook_env` | Name of the environment variable that holds the webhook URL |

A blank copy is in `templates/radar.config.json`. Rendered examples in each language are in `examples/`.
