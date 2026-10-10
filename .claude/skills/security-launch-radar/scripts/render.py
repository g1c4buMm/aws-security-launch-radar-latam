#!/usr/bin/env python3
"""Render the validated radar as email (HTML and text), a Slack message (Block Kit) and a LinkedIn post.

Titles, dates, links and severities come from items.json, never from the agent's text.
Order: header · highlights · also released · good to know (CVEs and bulletins) · footer.
The LinkedIn post (linkedin.txt, plus linkedin.html with copy buttons) uses Unicode bold for
headings, keeps links out of the body (they go in the first comment) and fits LinkedIn's limit.

Usage: python3 render.py --radar out/radar.json --items out/items.json --config radar.config.json --out out
"""
import argparse
import html
import json
import os

LANGUAGES = ("en", "pt-BR", "es")
LABELS = {
    "en": {
        "title": "AWS Security Weekly Radar", "week": "Week of", "to": "to",
        "news": "This week's highlights", "why": "Why it matters", "action": "Suggested action",
        "also": "Also released", "cves_title": "Good to know: CVEs and security bulletins",
        "cve": "CVE", "affected": "Service or package", "severity": "Severity", "date": "Date",
        "na": "n/a", "no_id": "no CVE", "updated": "Updated",
        "priority": {"high": "High", "medium": "Medium", "low": "Low"},
        "sources": {"whats-new": "What's New", "security-blog": "Security blog", "security-bulletins": "Security Bulletin"},
        "kind": {"whats-new": "News", "security-blog": "Blog"},
        "groups": {"whats-new": "News · AWS What's New", "security-blog": "Blog posts · AWS security blogs"},
        "disclaimer": "AI-assisted summary of public AWS sources. Always confirm details in the linked source.",
        "footer": "Sources: AWS What's New, AWS security blogs and AWS Security Bulletins.",
    },
    "pt-BR": {
        "title": "Radar Semanal de Segurança AWS", "week": "Semana de", "to": "a",
        "news": "Destaques da semana", "why": "Por que importa", "action": "Ação sugerida",
        "also": "Também saiu", "cves_title": "Também é bom saber: CVEs e boletins de segurança",
        "cve": "CVE", "affected": "Serviço ou pacote", "severity": "Severidade", "date": "Data",
        "na": "n/d", "no_id": "sem CVE", "updated": "Atualizado",
        "priority": {"high": "Alta", "medium": "Média", "low": "Baixa"},
        "sources": {"whats-new": "What's New", "security-blog": "Blog de segurança", "security-bulletins": "Security Bulletin"},
        "kind": {"whats-new": "Novidade", "security-blog": "Blog"},
        "groups": {"whats-new": "Novidades · AWS What's New", "security-blog": "Posts de blog · blogs de segurança da AWS"},
        "disclaimer": "Resumo gerado com apoio de IA a partir de fontes públicas da AWS. Confirme os detalhes na fonte indicada.",
        "footer": "Fontes: AWS What's New, blogs de segurança da AWS e AWS Security Bulletins.",
    },
    "es": {
        "title": "Radar Semanal de Seguridad AWS", "week": "Semana del", "to": "al",
        "news": "Destacados de la semana", "why": "Por qué importa", "action": "Acción sugerida",
        "also": "También salió", "cves_title": "También es bueno saber: CVEs y boletines de seguridad",
        "cve": "CVE", "affected": "Servicio o paquete", "severity": "Severidad", "date": "Fecha",
        "na": "n/d", "no_id": "sin CVE", "updated": "Actualizado",
        "priority": {"high": "Alta", "medium": "Media", "low": "Baja"},
        "sources": {"whats-new": "What's New", "security-blog": "Blog de seguridad", "security-bulletins": "Security Bulletin"},
        "kind": {"whats-new": "Novedad", "security-blog": "Blog"},
        "groups": {"whats-new": "Novedades · AWS What's New", "security-blog": "Publicaciones de blog · blogs de seguridad de AWS"},
        "disclaimer": "Resumen generado con apoyo de IA a partir de fuentes públicas de AWS. Confirma los detalles en la fuente indicada.",
        "footer": "Fuentes: AWS What's New, blogs de seguridad de AWS y AWS Security Bulletins.",
    },
}

# Sober palette: AWS navy, orange only on section titles.
NAVY, ORANGE, INK, MUTED, LINE, SOFT, LINK = "#232f3e", "#ff9900", "#1d2939", "#667085", "#e4e7ec", "#f5f6f8", "#0b5cad"
BADGE = {"high": ("#fef3f2", "#b42318"), "medium": ("#fffaeb", "#b54708"), "low": ("#f2f4f7", "#475467")}
PRIORITY_EMOJI = {"high": "🔴", "medium": "🟠", "low": "⚪"}
KIND_BADGE = {"whats-new": ("#eaf2ff", "#0b5cad"), "security-blog": ("#f4efff", "#6941c6")}
GROUP_ORDER = ("whats-new", "security-blog")
FONT = "font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def e(text):
    return html.escape(text or "", quote=True)


def mrk(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kind_badge(source, L):
    bg, fg = KIND_BADGE[source]
    return ('<span style="background:%s;color:%s;font-weight:700;font-size:10px;letter-spacing:.5px;padding:2px 7px;border-radius:4px;">%s</span>'
            % (bg, fg, e(L["kind"][source].upper())))


def grouped(ids, by_id):
    """'Also released' split into news and blog posts, keeping the agent's order inside each group."""
    return [(src, [i for i in ids if by_id[i]["source"] == src]) for src in GROUP_ORDER
            if any(by_id[i]["source"] == src for i in ids)]


def cve_rows(radar, by_id, L):
    rows = []
    for c in radar.get("cves") or []:
        it = by_id[c["item_id"]]
        affected = it["title"]
        for cid in it.get("cve_ids", []):
            affected = affected.replace(cid, "")
        affected = affected.strip(" -:,–")
        if affected.lower().startswith("and "):
            affected = affected[4:].strip(" -:,–")
        rows.append({"ids": ", ".join(it.get("cve_ids") or []) or L["no_id"], "affected": affected or it["title"],
                     "severity": it.get("severity") or L["na"], "date": it["date"], "link": it["link"],
                     "note": c.get("note") or "", "updated": bool(it.get("updated"))})
    rows.sort(key=lambda r: (not r["updated"], r["date"]), reverse=True)  # new bulletins first, then updates
    return rows


def context(radar, items, config):
    lang = config.get("language", "en")
    if lang not in LABELS:
        raise SystemExit("unsupported language '%s' (use %s)" % (lang, ", ".join(LANGUAGES)))
    L = LABELS[lang]
    dates = "%s %s %s %s" % (L["week"], items["window"]["from"], L["to"], items["window"]["to"])
    return {"L": L, "lang": lang, "by_id": {i["id"]: i for i in items["items"]}, "dates": dates,
            "cves": cve_rows(radar, {i["id"]: i for i in items["items"]}, L),
            "subject": "%s | %s" % (L["title"], radar["headline"])}


# ---------------- HTML (tables: works in Outlook and Gmail) ----------------

def section_title(text):
    return ('<tr><td style="padding:28px 32px 8px 32px;"><table role="presentation" width="100%%" cellpadding="0" cellspacing="0"><tr>'
            '<td style="%sfont-size:13px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:%s;'
            'border-bottom:2px solid %s;padding-bottom:6px;">%s</td></tr></table></td></tr>' % (FONT, NAVY, ORANGE, e(text)))


def render_html(radar, c):
    L, by_id = c["L"], c["by_id"]
    r = ['<tr><td style="background:%s;padding:28px 32px;">'
         '<div style="%sfont-size:11px;font-weight:700;letter-spacing:1.2px;color:%s;">%s</div>'
         '<div style="%sfont-size:21px;line-height:28px;font-weight:700;color:#ffffff;margin-top:8px;">%s</div>'
         '<div style="%sfont-size:12px;line-height:18px;color:#c4cad3;margin-top:10px;">%s</div></td></tr>'
         % (NAVY, FONT, ORANGE, e(L["title"].upper()), FONT, e(radar["headline"]), FONT, e(c["dates"]))]
    r.append(section_title(L["news"]))
    for hl in radar["highlights"]:
        it = by_id[hl["item_id"]]
        bg, fg = BADGE[hl["priority"]]
        r.append('<tr><td style="padding:14px 32px 2px 32px;">'
                 '<div style="%sfont-size:11px;color:%s;"><span style="background:%s;color:%s;font-weight:700;padding:2px 8px;border-radius:10px;">%s</span>'
                 '&nbsp; %s &nbsp;%s · %s</div>'
                 '<div style="margin-top:6px;"><a href="%s" style="%sfont-size:15px;line-height:21px;font-weight:700;color:%s;text-decoration:none;">%s</a></div>'
                 '<div style="%sfont-size:14px;line-height:21px;color:%s;margin-top:6px;"><b>%s:</b> %s</div>'
                 '<div style="%sfont-size:14px;line-height:21px;color:%s;margin-top:4px;"><b>%s:</b> %s</div>'
                 '<div style="border-bottom:1px solid %s;margin-top:14px;"></div></td></tr>'
                 % (FONT, MUTED, bg, fg, e(L["priority"][hl["priority"]]), kind_badge(it["source"], L), e(it["date"]), e(L["sources"].get(it["source"], it["source"])),
                    e(it["link"]), FONT, LINK, e(it["title"]), FONT, INK, e(L["why"]), e(hl["why_it_matters"]),
                    FONT, INK, e(L["action"]), e(hl["action"]), LINE))
    also = radar.get("also_noted") or []
    if also:
        r.append(section_title(L["also"]))
        rows = ""
        for src, ids in grouped(also, by_id):
            rows += '<div style="margin:10px 0 6px 0;">%s <span style="color:%s;font-size:12px;font-weight:600;">&nbsp;%s</span></div>' % (
                kind_badge(src, L), MUTED, e(L["groups"][src]))
            rows += "".join('<div style="margin:0 0 7px 0;"><a href="%s" style="color:%s;text-decoration:none;">%s</a> <span style="color:%s;">· %s</span></div>'
                            % (e(by_id[i]["link"]), LINK, e(by_id[i]["title"]), MUTED, e(by_id[i]["date"])) for i in ids)
        r.append('<tr><td style="padding:4px 32px 0 32px;%sfont-size:13px;line-height:19px;">%s</td></tr>' % (FONT, rows))
    if c["cves"]:
        r.append(section_title(L["cves_title"]))
        head = '<tr>' + "".join('<td style="%sfont-size:10px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:%s;'
                                'padding:8px 10px;border-bottom:1px solid %s;">%s</td>' % (FONT, MUTED, LINE, e(h))
                                for h in (L["cve"], L["affected"], L["severity"], L["date"])) + '</tr>'
        cell = '%sfont-size:12px;line-height:17px;color:%s;padding:8px 10px;border-bottom:1px solid %s;vertical-align:top;' % (FONT, INK, LINE)
        body = []
        for row in c["cves"]:
            note = '<div style="color:%s;margin-top:3px;">%s</div>' % (MUTED, e(row["note"])) if row["note"] else ""
            if row["updated"]:
                note = ('<div style="margin-top:3px;"><span style="background:#f2f4f7;color:#475467;font-weight:700;font-size:10px;'
                        'padding:1px 6px;border-radius:4px;">%s</span></div>' % e(L["updated"].upper())) + note
            body.append('<tr><td style="%swhite-space:nowrap;"><a href="%s" style="color:%s;text-decoration:none;font-weight:700;">%s</a></td>'
                        '<td style="%s">%s%s</td><td style="%s">%s</td><td style="%swhite-space:nowrap;">%s</td></tr>'
                        % (cell, e(row["link"]), LINK, e(row["ids"]).replace(", ", "<br>"), cell, e(row["affected"]), note,
                           cell, e(row["severity"]), cell, e(row["date"])))
        r.append('<tr><td style="padding:8px 32px 0 32px;"><table role="presentation" width="100%%" cellpadding="0" cellspacing="0" '
                 'style="background:%s;border:1px solid %s;">%s%s</table></td></tr>' % (SOFT, LINE, head, "".join(body)))
    r.append('<tr><td style="padding:28px 32px;"><div style="border-top:1px solid %s;padding-top:14px;%sfont-size:11px;line-height:17px;color:%s;">%s<br>%s</div></td></tr>'
             % (LINE, FONT, MUTED, e(L["disclaimer"]), e(L["footer"])))

    # Preheader: the line the inbox shows next to the subject.
    preheader = ('<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">%s%s</div>'
                 % (e(radar["headline"]), "&#847;&zwnj;&nbsp;" * 40))
    # Full document with charset, otherwise some clients read UTF-8 as Latin-1.
    return ('<!DOCTYPE html>\n<html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="light"><title>%s</title></head><body style="margin:0;padding:0;background:%s;">%s\n'
            '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" style="background:%s;"><tr><td align="center" style="padding:24px 12px;">'
            '<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:100%%;max-width:640px;background:#ffffff;border:1px solid %s;">'
            '%s</table></td></tr></table>\n</body></html>'
            % (e(c["lang"]), e(c["subject"]), SOFT, preheader, SOFT, LINE, "\n".join(r)))


def render_text(radar, c):
    L, by_id = c["L"], c["by_id"]
    t = [L["title"], c["dates"], radar["headline"], "", L["news"].upper()]
    for n, hl in enumerate(radar["highlights"], 1):
        it = by_id[hl["item_id"]]
        t += ["", "%d. [%s] [%s] %s (%s)" % (n, L["priority"][hl["priority"]], L["kind"][it["source"]].upper(), it["title"], it["date"]), it["link"],
              "%s: %s" % (L["why"], hl["why_it_matters"]), "%s: %s" % (L["action"], hl["action"])]
    also = radar.get("also_noted") or []
    if also:
        t += ["", L["also"].upper()]
        for src, ids in grouped(also, by_id):
            t += ["", L["groups"][src] + ":"] + ["- %s (%s) %s" % (by_id[i]["title"], by_id[i]["date"], by_id[i]["link"]) for i in ids]
    if c["cves"]:
        t += ["", L["cves_title"].upper()]
        for row in c["cves"]:
            t.append("- %s%s | %s | %s | %s | %s" % (row["ids"], " [%s]" % L["updated"].upper() if row["updated"] else "",
                                                   row["affected"], row["severity"], row["date"], row["link"]))
            if row["note"]:
                t.append("  %s" % row["note"])
    t += ["", L["disclaimer"], L["footer"]]
    return "\n".join(t)


def render_slack(radar, c):
    L, by_id = c["L"], c["by_id"]
    blocks = [{"type": "header", "text": {"type": "plain_text", "text": "🛡️ " + L["title"]}},
              {"type": "context", "elements": [{"type": "mrkdwn", "text": c["dates"]}]},
              {"type": "section", "text": {"type": "mrkdwn", "text": "*%s*" % mrk(radar["headline"])}},
              {"type": "divider"}, {"type": "section", "text": {"type": "mrkdwn", "text": "*%s*" % L["news"]}}]
    for hl in radar["highlights"]:
        it = by_id[hl["item_id"]]
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": (
            "%s `%s` *<%s|%s>* _(%s)_\n*%s:* %s\n*%s:* %s" % (PRIORITY_EMOJI[hl["priority"]], L["kind"][it["source"]].upper(), it["link"], mrk(it["title"]), it["date"],
                                                      L["why"], mrk(hl["why_it_matters"]), L["action"], mrk(hl["action"])))[:2990]}})
    also = radar.get("also_noted") or []
    if also:
        parts = []
        for src, ids in grouped(also, by_id):
            parts.append("`%s` _%s_\n%s" % (L["kind"][src].upper(), mrk(L["groups"][src]),
                                             "\n".join("• <%s|%s>" % (by_id[i]["link"], mrk(by_id[i]["title"])) for i in ids)))
        blocks += [{"type": "divider"}, {"type": "section", "text": {"type": "mrkdwn", "text": ("*%s*\n%s" % (L["also"], "\n\n".join(parts)))[:2990]}}]
    if c["cves"]:
        chunks, chunk = [], ""
        for row in c["cves"]:
            line = "• <%s|%s> %s%s · _%s · %s_" % (row["link"], mrk(row["ids"]), "`%s` " % L["updated"].upper() if row["updated"] else "",
                                                   mrk(row["affected"]), mrk(row["severity"]), row["date"])
            if row["note"]:
                line += "\n   " + mrk(row["note"])
            if len(chunk) + len(line) > 2900:  # Slack caps a block at 3000 characters
                chunks.append(chunk)
                chunk = ""
            chunk += line + "\n"
        chunks.append(chunk)
        blocks += [{"type": "divider"}, {"type": "section", "text": {"type": "mrkdwn", "text": "🧩 *%s*" % L["cves_title"]}}]
        blocks += [{"type": "section", "text": {"type": "mrkdwn", "text": ch}} for ch in chunks if ch]
    blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": mrk(L["disclaimer"])}]})
    return {"text": c["subject"], "blocks": blocks[:50]}


# ---------------- LinkedIn ----------------

LINKEDIN = {
    "en": {"highlights": "Highlights", "cves": "New CVEs to check", "also": "Also released",
           "news": ("{n} more news item", "{n} more news items"), "blog": ("{n} blog post", "{n} blog posts"),
           "and": " and ", "also_end": " in the full report.", "more": "…and {k} more in the full report.",
           "question": "Which of these goes on your backlog first?",
           "hashtags": "#AWS #CloudSecurity #AWSSecurity #CVE #SecurityEngineering",
           "ui": {"copy": "Copy post", "links": "Copy links for the first comment", "copied": "Copied", "chars": "characters",
                  "hint": "Paste the post, then paste the links as the first comment.", "comment": "First comment"}},
    "pt-BR": {"highlights": "Destaques", "cves": "CVEs novas para checar", "also": "Também saiu",
              "news": ("Mais {n} novidade", "Mais {n} novidades"), "blog": ("{n} post de blog", "{n} posts de blog"),
              "and": " e ", "also_end": " no relatório completo.", "more": "…e mais {k} no relatório completo.",
              "question": "Qual desses entra primeiro no seu backlog?",
              "hashtags": "#AWS #SegurançaEmNuvem #AWSSecurity #CVE #CiberSegurança",
              "ui": {"copy": "Copiar post", "links": "Copiar links para o primeiro comentário", "copied": "Copiado", "chars": "caracteres",
                     "hint": "Cole o post e depois cole os links como primeiro comentário.", "comment": "Primeiro comentário"}},
    "es": {"highlights": "Destacados", "cves": "CVEs nuevas para revisar", "also": "También salió",
           "news": ("{n} novedad más", "{n} novedades más"), "blog": ("{n} publicación de blog", "{n} publicaciones de blog"),
           "and": " y ", "also_end": " en el informe completo.", "more": "…y {k} más en el informe completo.",
           "question": "¿Cuál de estos entra primero en tu backlog?",
           "hashtags": "#AWS #SeguridadEnLaNube #AWSSecurity #CVE #Ciberseguridad",
           "ui": {"copy": "Copiar publicación", "links": "Copiar enlaces para el primer comentario", "copied": "Copiado", "chars": "caracteres",
                  "hint": "Pega la publicación y luego pega los enlaces como primer comentario.", "comment": "Primer comentario"}},
}
LINKEDIN_LIMIT = 2900  # LinkedIn allows 3000 UTF-16 units; keep a margin


def bold(text):
    """Unicode sans-serif bold for A-Z, a-z and 0-9; other characters stay as they are."""
    out = []
    for ch in text:
        o = ord(ch)
        if 65 <= o <= 90:
            out.append(chr(0x1D5D4 + o - 65))
        elif 97 <= o <= 122:
            out.append(chr(0x1D5EE + o - 97))
        elif 48 <= o <= 57:
            out.append(chr(0x1D7EC + o - 48))
        else:
            out.append(ch)
    return "".join(out)


def li_len(text):
    return len(text.encode("utf-16-le")) // 2  # how LinkedIn counts


def plain(text):
    """No em or en dashes in the post."""
    return (text or "").replace(" — ", ": ").replace(" – ", ": ").replace("—", "-").replace("–", "-")


def first_sentence(text):
    for sep in (". ", "! ", "? "):
        if sep in text:
            return text.split(sep)[0] + sep.strip()
    return text


def render_linkedin(radar, c):
    """Returns (post, links). Shortens step by step until the post fits."""
    L, K, by_id = c["L"], LINKEDIN[c["lang"]], c["by_id"]
    new_cves = [r for r in c["cves"] if not r["updated"]]
    news = sum(1 for i in radar.get("also_noted") or [] if by_id[i]["source"] == "whats-new")
    blogs = len(radar.get("also_noted") or []) - news
    links = [(by_id[h["item_id"]]["title"], by_id[h["item_id"]]["link"]) for h in radar["highlights"]]
    links += [(r["ids"], r["link"]) for r in new_cves]

    def also_line():
        parts = [K[key][0 if n == 1 else 1].format(n=n) for key, n in (("news", news), ("blog", blogs)) if n]
        line = K["and"].join(parts) + K["also_end"]
        return line[0].upper() + line[1:]

    # Shortening order: full text, first sentence of why, fewer CVEs, no action lines, fewer highlights.
    def build(level):
        hls = radar["highlights"] if level < 4 else radar["highlights"][:4]
        cve_max = 5 if level < 2 else 3
        t = ["🛡️ " + bold(plain(L["title"])), "📅 " + c["dates"], "", plain(radar["headline"]), "",
             "🚀 " + bold(K["highlights"]) + ":"]
        for h in hls:
            it = by_id[h["item_id"]]
            why = h["why_it_matters"] if level == 0 else first_sentence(h["why_it_matters"])
            t += ["", "%s %s" % (PRIORITY_EMOJI[h["priority"]], bold(plain(it["title"]))), plain(why)]
            if level < 3:
                t.append("➡️ " + plain(h["action"]))
        if new_cves:
            t += ["", "🧩 " + bold(K["cves"]) + ":"]
            for r in new_cves[:cve_max]:
                t.append("• %s: %s" % (r["ids"], plain(r["affected"])))
            if len(new_cves) > cve_max:
                t.append(K["more"].format(k=len(new_cves) - cve_max))
        if news or blogs:
            t += ["", "📌 " + bold(K["also"]) + ":", also_line()]
        t += ["", "💬 " + plain(radar.get("question") or K["question"]), "", K["hashtags"]]
        return "\n".join(t)

    for level in range(5):
        post = build(level)
        if li_len(post) <= LINKEDIN_LIMIT:
            return post, links
    return post, links


def render_linkedin_html(post, links, c):
    ui = LINKEDIN[c["lang"]]["ui"]
    links_text = "\n".join("%s: %s" % (plain(t), u) for t, u in links)
    return """<!DOCTYPE html>
<html lang="%(lang)s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LinkedIn Post Preview</title>
<style>
:root{--bg:#f4f2ee;--card:#fff;--ink:#1c1916;--muted:#6b635b;--line:#e2ddd7;--accent:#b9561c}
@media (prefers-color-scheme:dark){:root{--bg:#13110f;--card:#1d1a17;--ink:#ede7e0;--muted:#a59c92;--line:#332e29;--accent:#ef7d3c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.wrap{max-width:640px;margin:0 auto;padding:24px 16px 48px;display:grid;gap:16px}
h1{font-size:18px;margin:0}.sub{color:var(--muted);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.post{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;font:inherit}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
button{font:600 14px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;border-radius:999px;padding:9px 16px;cursor:pointer;border:1px solid var(--accent);background:var(--accent);color:#fff}
button.alt{background:transparent;color:var(--accent)}
.count{font:13px ui-monospace,Menlo,monospace;color:var(--muted)}.ok{color:#2f7d55}.bad{color:#b42318}
.links{white-space:pre-wrap;overflow-wrap:anywhere;font:13px ui-monospace,Menlo,monospace;color:var(--muted);margin:0}
</style></head><body><div class="wrap">
<div><h1>LinkedIn · %(title)s</h1><p class="sub">%(dates)s. %(hint)s</p></div>
<div class="row"><button type="button" data-copy="post">%(copy)s</button><button type="button" class="alt" data-copy="links">%(links_btn)s</button>
<span class="count" id="count"></span></div>
<div class="card"><pre class="post" id="post">%(post)s</pre></div>
<div class="card"><p class="sub" style="margin:0 0 8px">%(comment)s</p><pre class="links" id="links">%(links)s</pre></div>
</div>
<script>
(function(){
  var post=document.getElementById('post').textContent, n=post.length, el=document.getElementById('count');
  el.textContent=n+' / 3000 %(chars)s'; el.className='count '+(n<=3000?'ok':'bad');
  document.querySelectorAll('button[data-copy]').forEach(function(b){
    b.addEventListener('click',function(){
      var text=document.getElementById(b.getAttribute('data-copy')).textContent, label=b.textContent;
      function done(){b.textContent='%(copied)s';setTimeout(function(){b.textContent=label},1500)}
      if(navigator.clipboard){navigator.clipboard.writeText(text).then(done,fallback)}else{fallback()}
      function fallback(){var t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();
        try{document.execCommand('copy');done()}catch(e){}document.body.removeChild(t)}
    });
  });
})();
</script></body></html>""" % {"lang": e(c["lang"]), "title": e(c["L"]["title"]), "dates": e(c["dates"]),
                               "post": e(post), "links": e(links_text), "hint": e(ui["hint"]), "copy": e(ui["copy"]),
                               "links_btn": e(ui["links"]), "comment": e(ui["comment"]), "chars": e(ui["chars"]), "copied": e(ui["copied"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radar", default="out/radar.json")
    ap.add_argument("--items", default="out/items.json")
    ap.add_argument("--config", default="radar.config.json")
    ap.add_argument("--out", default="out")
    args = ap.parse_args()

    radar = load(args.radar)
    c = context(radar, load(args.items), load(args.config))
    os.makedirs(args.out, exist_ok=True)
    post, links = render_linkedin(radar, c)
    files = {"email_subject.txt": c["subject"], "email.html": render_html(radar, c), "email.txt": render_text(radar, c),
             "slack.json": json.dumps(render_slack(radar, c), ensure_ascii=False, indent=1),
             "linkedin.txt": post + "\n", "linkedin.html": render_linkedin_html(post, links, c)}
    for name, content in files.items():
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            f.write(content)
    print("written to %s: %s" % (args.out, ", ".join(files)))


if __name__ == "__main__":
    main()
